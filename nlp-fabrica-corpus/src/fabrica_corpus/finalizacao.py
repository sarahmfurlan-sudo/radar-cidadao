"""Etapa de finalização da Fábrica de Corpus.

Fluxo: geração (Qwen no Colab) -> revisão humana -> finalização.

A finalização trabalha sobre os corpus JÁ REVISADOS (por padrão, a pasta entrega-final):
não chama o modelo, não usa o cache e não cria exemplos. Ela:
 1. refaz o corpus_texto pelo pipeline normal (ingestão, limpeza, anonimização e
    segmentação dos 5 documentos de dados/entrada);
 2. lê corpus_qa.jsonl e corpus_chat.jsonl revisados e aplica as regras de formatação
    (hoje: tirar as páginas da citação da fonte, mantendo o nome do documento);
 3. valida: campos, tamanho mínimo, alternância das falas, duplicatas, quantidades
    mínimas do enunciado e recusas válidas;
 4. grava os 3 JSONL na própria pasta, atualiza as contagens do estatisticas.json
    (mantendo os campos da revisão humana) e refaz amostras_5_por_corpus.json.

As regras de validação vêm do fechar_entrega.py, que antes existia só nos notebooks.
Rodar duas vezes dá o mesmo resultado.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import statistics
import unicodedata
from pathlib import Path
from typing import Callable

from .exportacao import ENTRADA, RAIZ, gravar_jsonl, linha_texto, preparar_segmentos
from .segmentacao import contar_tokens_qwen

ENTREGA = RAIZ / "entrega-final"
MINIMOS = {"texto": 50, "qa": 100, "chat": 30}
MINIMO_RECUSAS = 10
CAMPOS = {
    "texto": ["text", "fonte", "segmento_id"],
    "qa": ["instruction", "input", "output", "fonte", "segmento_id"],
    "chat": ["messages", "fonte", "tipo", "segmento_id"],
}
# Primeira fala do usuário que é só um marcador, e não uma pergunta de verdade
MARCADORES_SEM_PERGUNTA = {"pedido inicial"}


# ------------------------------------------------------------ leitura
def ler_jsonl(caminho: str | Path) -> list[dict]:
    itens = []
    with open(caminho, encoding="utf-8") as arq:
        for n, linha in enumerate(arq, start=1):
            if linha.strip():
                try:
                    itens.append(json.loads(linha))
                except json.JSONDecodeError as erro:
                    raise ValueError(f"{caminho}: linha {n}: {erro}") from erro
    return itens


# ------------------------------------------------------------ formatação
# "Fonte: Título do documento, p. 7-9." -> "Fonte: Título do documento."
# Só o padrão que a função citacao() da geração coloca no fim da resposta.
_PAGINAS_NA_CITACAO = re.compile(r"(Fonte: [^\n]*?), p\. \d+(?:\s*-\s*\d+)?\.(\s*)$")


def tirar_paginas(texto: str) -> str:
    return _PAGINAS_NA_CITACAO.sub(r"\1.\2", texto)


def formatar_qa(e: dict) -> dict:
    return {"instruction": e["instruction"], "input": e.get("input", ""), "output": tirar_paginas(e["output"]),
            "fonte": e["fonte"], "segmento_id": e.get("segmento_id") or ""}


def formatar_chat(e: dict) -> dict:
    mensagens = [{"role": m["role"], "content": tirar_paginas(m["content"])} for m in e["messages"]]
    return {"messages": mensagens, "fonte": e["fonte"], "tipo": e.get("tipo", "chat"),
            "segmento_id": e.get("segmento_id") or ""}


# ------------------------------------------------------------ validação
def _normalizar(texto: str) -> str:
    """Sem acento, sem pontuação, sem caixa e com espaços colapsados (só para comparar)."""
    t = unicodedata.normalize("NFKD", str(texto)).casefold()
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def chave_duplicata(e: dict, tipo: str) -> str:
    if tipo == "texto":
        base = e["text"]
    elif tipo == "qa":
        base = e["instruction"]
    else:
        base = "\n".join(f"{m['role']}:{m['content']}" for m in e["messages"] if m["role"] != "system")
    return hashlib.sha256(_normalizar(base).encode()).hexdigest()


def conferir_formato(e: dict, tipo: str) -> str | None:
    """Devolve o problema encontrado, ou None se o exemplo está no formato."""
    if not isinstance(e, dict) or list(e) != CAMPOS[tipo]:
        return f"campos diferentes de {CAMPOS[tipo]}"
    if not isinstance(e.get("fonte"), str) or not e["fonte"].strip():
        return "fonte ausente"
    if tipo == "texto" and len(e["text"].strip()) < 30:
        return "texto curto"
    if tipo == "qa":
        if not all(isinstance(e[k], str) for k in ("instruction", "input", "output")):
            return "campos de pergunta e resposta ausentes"
        if len(e["instruction"].strip()) < 12 or len(e["output"].strip()) < 12:
            return "pergunta ou resposta curta"
    if tipo == "chat":
        ms = e["messages"]
        if not isinstance(ms, list) or any(not isinstance(m, dict) for m in ms):
            return "mensagens ausentes"
        if any(m.get("role") not in ("system", "user", "assistant") or not str(m.get("content", "")).strip()
               for m in ms):
            return "mensagem vazia ou papel inválido"
        papeis = [m["role"] for m in ms if m["role"] != "system"]
        if len(papeis) < 4 or papeis != ["user", "assistant"] * (len(papeis) // 2):
            return "menos de 2 trocas ou falas fora de ordem"
    return None


def recusa_valida(e: dict) -> bool:
    """Recusa conta para o mínimo só se a primeira fala do usuário for uma pergunta de verdade."""
    if e.get("tipo") != "recusa":
        return False
    primeira = next((m["content"] for m in e["messages"] if m["role"] == "user"), "")
    return _normalizar(primeira) not in MARCADORES_SEM_PERGUNTA and len(primeira.strip()) >= 12


def filtrar(itens: list[dict], tipo: str) -> tuple[list[dict], int, list[dict]]:
    """Devolve (válidos, duplicatas removidas, inválidos com linha e problema)."""
    validos, duplicatas, invalidos, vistos = [], 0, [], set()
    for n, e in enumerate(itens, start=1):
        problema = conferir_formato(e, tipo)
        if problema:
            invalidos.append({"linha": n, "problema": problema})
            continue
        chave = chave_duplicata(e, tipo)
        if chave in vistos:
            duplicatas += 1
            continue
        vistos.add(chave)
        validos.append(e)
    return validos, duplicatas, invalidos


def estimar_tokens(e: dict) -> int:
    """Estimativa simples (palavras e sinais), a mesma usada no estatisticas.json da entrega."""
    return len(re.findall(r"\w+|[^\w\s]", json.dumps(e, ensure_ascii=False)))


def tokens_do_exemplo(e: dict, tipo: str, contar: Callable[[str], int]) -> int:
    """Tokens do conteúdo de um exemplo, com o tokenizador do Qwen (o mesmo da segmentação).

    texto: o trecho; qa: instruction + input + output; chat: o conteúdo de todas as
    mensagens, incluindo a do system. Campos como fonte e segmento_id não contam."""
    if tipo == "texto":
        partes = [e["text"]]
    elif tipo == "qa":
        partes = [e["instruction"], e["input"], e["output"]]
    else:
        partes = [m["content"] for m in e["messages"]]
    return sum(contar(p) for p in partes if p)


# ------------------------------------------------------------ finalização
def finalizar(pasta: str | Path = ENTREGA, segmentos: list | None = None,
              contar: Callable[[str], int] | None = None) -> dict:
    """Finaliza os corpus revisados da pasta e grava o resultado nela mesma. Devolve as métricas.

    segmentos: os segmentos dos 5 documentos; se None, vêm do pipeline normal (dados/entrada)."""
    pasta = Path(pasta)
    if segmentos is None:
        segmentos, _ = preparar_segmentos(ENTRADA, contar)
    contar = contar or contar_tokens_qwen

    qa_lido = ler_jsonl(pasta / "corpus_qa.jsonl")
    chat_lido = ler_jsonl(pasta / "corpus_chat.jsonl")
    brutos = {
        "texto": [linha_texto(s) for s in segmentos],
        "qa": [formatar_qa(e) for e in qa_lido],
        "chat": [formatar_chat(e) for e in chat_lido],
    }
    antigo = pasta / "corpus_texto.jsonl"
    texto_antigo = {e["segmento_id"]: e["text"] for e in ler_jsonl(antigo)} if antigo.exists() else {}
    remapeados = _remapear_segmentos(brutos["qa"] + brutos["chat"], texto_antigo,
                                     {s.id: s.texto for s in segmentos})
    paginas_removidas = {
        "qa": sum(a["output"] != b["output"] for a, b in zip(qa_lido, brutos["qa"])),
        "chat": sum(a["messages"] != b["messages"] for a, b in zip(chat_lido, brutos["chat"])),
    }

    metricas, finais = {}, {}
    for tipo, itens in brutos.items():
        validos, dup, invalidos = filtrar(itens, tipo)
        finais[tipo] = validos
        metricas[tipo] = {"quantidade": len(validos), "minimo": MINIMOS[tipo],
                          "quantidade_atingida": len(validos) >= MINIMOS[tipo],
                          "media_tokens_aprox": round(statistics.mean(map(estimar_tokens, validos)), 1) if validos else 0,
                          "media_tokens_qwen": round(statistics.mean(tokens_do_exemplo(e, tipo, contar)
                                                                      for e in validos), 1) if validos else 0,
                          "duplicatas_removidas": dup, "invalidos_removidos": len(invalidos),
                          "detalhes_invalidos": invalidos[:40]}
    recusas = [e for e in finais["chat"] if e["tipo"] == "recusa"]
    metricas["recusas"] = len(recusas)
    metricas["recusas_validas"] = sum(map(recusa_valida, recusas))
    metricas["recusas_atingidas"] = metricas["recusas_validas"] >= MINIMO_RECUSAS
    metricas["paginas_removidas"] = paginas_removidas
    metricas["segmento_id_remapeados"] = remapeados
    metricas["respostas_com_paginas"] = (sum("p. " in e["output"] for e in finais["qa"])
                                         + sum(any("p. " in m["content"] for m in e["messages"])
                                               for e in finais["chat"]))

    for tipo, itens in finais.items():
        gravar_jsonl(itens, pasta / f"corpus_{tipo}.jsonl")
    _atualizar_estatisticas(pasta / "estatisticas.json", metricas)
    amostras = {tipo: random.Random(2026).sample(itens, min(5, len(itens))) for tipo, itens in finais.items()}
    (pasta / "amostras_5_por_corpus.json").write_text(json.dumps(amostras, ensure_ascii=False, indent=2) + "\n",
                                                       encoding="utf-8")
    return metricas


def _palavras(texto: str) -> set[str]:
    return set(re.findall(r"\w{4,}", texto.lower()))


def _remapear_segmentos(exemplos: list[dict], texto_antigo: dict, texto_novo: dict) -> dict:
    """Mantém a rastreabilidade quando a segmentação muda (limpeza ou anonimização novas).

    Se o texto do segmento_id de um exemplo mudou, o exemplo passa a apontar para o
    segmento novo do mesmo documento com mais palavras em comum com o texto antigo.
    Devolve {id antigo: id novo} só dos que mudaram de número."""
    trocas: dict[str, str] = {}
    for e in exemplos:
        sid = e.get("segmento_id")
        if not sid or sid not in texto_antigo or texto_novo.get(sid) == texto_antigo[sid]:
            continue
        if sid not in trocas:
            base = sid.rsplit("_", 1)[0]
            p = _palavras(texto_antigo[sid])
            candidatos = [k for k in texto_novo if k.rsplit("_", 1)[0] == base]
            trocas[sid] = max(candidatos, key=lambda k: (len(p & _palavras(texto_novo[k])), k == sid)) if candidatos else sid
        e["segmento_id"] = trocas[sid]
    return {a: b for a, b in trocas.items() if a != b}


def _atualizar_estatisticas(caminho: Path, metricas: dict) -> None:
    """Atualiza só as contagens; os campos da revisão humana e da geração ficam como estão."""
    estat = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
    # os remapeamentos de execuções anteriores continuam registrados (o histórico não se perde)
    anteriores = estat.get("finalizacao", {}).get("segmento_id_remapeados", {})
    for tipo in MINIMOS:
        bloco = estat.setdefault(tipo, {})
        for campo in ("quantidade", "minimo", "quantidade_atingida", "media_tokens_aprox", "media_tokens_qwen"):
            bloco[campo] = metricas[tipo][campo]
    estat["recusas_validas"] = metricas["recusas_validas"]
    estat["recusas_atingidas"] = metricas["recusas_atingidas"]
    estat["finalizacao"] = {
        tipo: {"duplicatas_removidas": metricas[tipo]["duplicatas_removidas"],
               "invalidos_removidos": metricas[tipo]["invalidos_removidos"]} for tipo in MINIMOS}
    estat["finalizacao"]["recusas_no_corpus"] = metricas["recusas"]
    estat["finalizacao"]["paginas_removidas"] = metricas["paginas_removidas"]
    estat["finalizacao"]["segmento_id_remapeados"] = {**anteriores, **metricas["segmento_id_remapeados"]}
    estat["finalizacao"]["respostas_com_paginas"] = metricas["respostas_com_paginas"]
    caminho.write_text(json.dumps(estat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
