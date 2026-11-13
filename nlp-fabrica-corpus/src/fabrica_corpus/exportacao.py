"""Exportação da Fábrica de Corpus: grava os corpus em JSONL.

Arquivos gerados (UTF-8, um JSON por linha, acentos sem escape):
 - dados/saida/corpus_texto.jsonl: segmentos dos 5 documentos de dados/entrada;
 - dados/saida/corpus_qa.jsonl: perguntas e respostas no formato instruction/input/output;
 - dados/saida/corpus_chat.jsonl: diálogos no formato messages (system/user/assistant);
 - dados/saida_rag/corpus_rag.jsonl: segmentos dos 9 documentos (dados/entrada +
   dados/entrada_ia_generativa), lido pelo RAG da disciplina de IA Generativa.

Duplicatas são removidas antes de gravar: texto igual depois de normalizar espaços e
caixa (nas perguntas, a pergunta igual). As contagens de removidos vão para o relatório.

As perguntas e os diálogos vêm do arquivo de resultado da geração
(dados/geracao/resultado_v8.json), gravado pelo notebook no fim da geração com os
exemplos aprovados e as estatísticas. A exportação só lê esse arquivo: não repete a
geração, não carrega modelo e não depende do cache.

Cada pasta é preparada separadamente (ingestão, limpeza, anonimização e segmentação),
então os segmentos dos 5 documentos são os mesmos no corpus_texto, na geração e no RAG.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable, Iterable

from .anonimizacao import anonimizar_corpus
from .geracao import MODELO_GERADOR, TITULOS, VERSAO_PROMPT, gerar_chat, gerar_qa, planejar_divisao
from .ingestao import ingerir_pasta
from .limpeza import limpar_corpus
from .segmentacao import segmentar

RAIZ = Path(__file__).resolve().parents[2]          # pasta nlp-fabrica-corpus
DADOS = RAIZ / "dados"
ENTRADA = DADOS / "entrada"
ENTRADA_IA = DADOS / "entrada_ia_generativa"
CACHE = DADOS / "cache_geracao"
SAIDA = DADOS / "saida"
SAIDA_RAG = DADOS / "saida_rag"
RESULTADO = DADOS / "geracao" / f"resultado_{VERSAO_PROMPT}.json"

TOTAL_QA, POR_SEGMENTO, TOTAL_CHAT, TURNOS = 100, 2, 30, 3


# ------------------------------------------------------------ preparação
def preparar_segmentos(pasta: str | Path, contar: Callable[[str], int] | None = None) -> tuple[list, dict]:
    """Ingestão, limpeza, anonimização e segmentação de uma pasta. Devolve (segmentos, estatísticas)."""
    trechos = ingerir_pasta(pasta)
    limpos, est_limpeza = limpar_corpus(trechos)
    anonimos, est_anonimizacao = anonimizar_corpus(limpos)
    segmentos, est_segmentacao = segmentar(anonimos, contar)
    return segmentos, {"limpeza": est_limpeza, "anonimizacao": est_anonimizacao,
                       "segmentacao": est_segmentacao}


# ------------------------------------------------------------ duplicatas e gravação
def normalizar(texto: str) -> str:
    """Espaços colapsados e caixa ignorada, só para comparar (o texto gravado não muda)."""
    return " ".join(str(texto).split()).casefold()


def remover_duplicatas(itens: Iterable, chave: Callable) -> tuple[list, int]:
    """Mantém a primeira ocorrência de cada chave normalizada. Devolve (únicos, removidos)."""
    vistos, unicos, removidos = set(), [], 0
    for item in itens:
        marca = normalizar(chave(item))
        if marca in vistos:
            removidos += 1
            continue
        vistos.add(marca)
        unicos.append(item)
    return unicos, removidos


def gravar_jsonl(linhas: Iterable[dict], caminho: str | Path) -> int:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(caminho, "w", encoding="utf-8", newline="\n") as arq:
        for linha in linhas:
            arq.write(json.dumps(linha, ensure_ascii=False) + "\n")
            n += 1
    return n


# ------------------------------------------------------------ formatos
def linha_texto(seg) -> dict:
    return {"id": seg.id, "texto": seg.texto, "fonte": seg.fonte, "paginas": seg.paginas, "tokens": seg.tokens}


def linha_rag(seg) -> dict:
    return {"id": seg.id, "texto": seg.texto, "fonte": seg.fonte, "titulo": TITULOS.get(seg.fonte, seg.fonte),
            "paginas": seg.paginas, "tokens": seg.tokens}


def linha_qa(exemplo: dict) -> dict:
    return {"id": exemplo["id"], "instruction": exemplo["pergunta"], "input": "", "output": exemplo["resposta"],
            "fonte": exemplo["fonte"], "paginas": exemplo["paginas"], "segmento_id": exemplo["segmento_id"]}


def linha_chat(exemplo: dict) -> dict:
    mensagens = [{"role": m["role"], "content": m["content"]} for m in exemplo["mensagens"]]
    return {"id": exemplo["id"], "messages": mensagens, "fonte": exemplo["fonte"], "paginas": exemplo["paginas"],
            "segmento_id": exemplo["segmento_id"]}


def _texto_do_dialogo(linha: dict) -> str:
    return " ".join(m["content"] for m in linha["messages"])


# ------------------------------------------------------------ perguntas e diálogos
def gerar_perguntas_e_dialogos(segmentos: list, gerar: Callable[[list], str], pasta_cache: str | Path | None = CACHE,
                               total_qa: int = TOTAL_QA, por_segmento: int = POR_SEGMENTO,
                               total_chat: int = TOTAL_CHAT, turnos: int = TURNOS,
                               progresso: bool = True) -> tuple[list, list, dict]:
    """Usada pelo notebook: divide os segmentos e gera perguntas e diálogos com o modelo.

    Devolve (qa, chat, estatísticas). O resultado vai para gravar_resultado."""
    seg_qa, seg_chat = planejar_divisao(segmentos, n_qa=math.ceil(total_qa / por_segmento), n_chat=total_chat)
    qa, est_qa = gerar_qa(seg_qa, gerar, total=total_qa, por_segmento=por_segmento,
                          pasta_cache=pasta_cache, progresso=progresso)
    chat, est_chat = gerar_chat(seg_chat, gerar, total=total_chat, turnos=turnos,
                                pasta_cache=pasta_cache, progresso=progresso)
    return qa, chat, {"qa": est_qa, "chat": est_chat}


def gravar_resultado(qa: list, chat: list, estatisticas: dict, caminho: str | Path = RESULTADO) -> Path:
    """Grava, no fim da geração, os exemplos aprovados e as estatísticas devolvidas pela geração."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {"versao_prompt": VERSAO_PROMPT, "modelo": MODELO_GERADOR,
             "estatisticas": estatisticas, "qa": qa, "chat": chat}
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return caminho


def ler_resultado(caminho: str | Path = RESULTADO) -> dict:
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe: rode a geração no Colab, que grava esse arquivo no fim")
    return json.loads(caminho.read_text(encoding="utf-8"))


# ------------------------------------------------------------ exportação
def exportar_texto(segmentos: list, saida: str | Path = SAIDA) -> dict:
    linhas, removidos = remover_duplicatas((linha_texto(s) for s in segmentos), lambda l: l["texto"])
    gravados = gravar_jsonl(linhas, Path(saida) / "corpus_texto.jsonl")
    return {"gravados": gravados, "duplicatas_removidas": removidos}


def exportar_qa_chat(resultado: str | Path = RESULTADO, saida: str | Path = SAIDA) -> dict:
    """Lê o arquivo de resultado da geração e grava corpus_qa.jsonl e corpus_chat.jsonl."""
    dados = ler_resultado(resultado)
    linhas_qa, rem_qa = remover_duplicatas((linha_qa(e) for e in dados["qa"]), lambda l: l["instruction"])
    linhas_chat, rem_chat = remover_duplicatas((linha_chat(e) for e in dados["chat"]), _texto_do_dialogo)
    return {
        "qa": {"gravados": gravar_jsonl(linhas_qa, Path(saida) / "corpus_qa.jsonl"), "duplicatas_removidas": rem_qa},
        "chat": {"gravados": gravar_jsonl(linhas_chat, Path(saida) / "corpus_chat.jsonl"),
                 "duplicatas_removidas": rem_chat},
        "geracao": {"versao_prompt": dados.get("versao_prompt"), "modelo": dados.get("modelo"),
                    **dados.get("estatisticas", {})},
    }


def exportar_rag(segmentos: list, saida: str | Path = SAIDA_RAG) -> dict:
    linhas, removidos = remover_duplicatas((linha_rag(s) for s in segmentos), lambda l: l["texto"])
    gravados = gravar_jsonl(linhas, Path(saida) / "corpus_rag.jsonl")
    por_fonte: dict[str, int] = {}
    for l in linhas:
        por_fonte[l["fonte"]] = por_fonte.get(l["fonte"], 0) + 1
    return {"gravados": gravados, "duplicatas_removidas": removidos, "por_fonte": por_fonte}


def exportar_tudo(com_qa_chat: bool = True, contar: Callable[[str], int] | None = None) -> dict:
    """Prepara as duas pastas e grava os corpus. com_qa_chat=False pula perguntas e diálogos
    (que exigem o arquivo de resultado da geração)."""
    seg_nlp, est_nlp = preparar_segmentos(ENTRADA, contar)
    seg_ia, est_ia = preparar_segmentos(ENTRADA_IA, contar)
    estat = {"preparacao": {"entrada": est_nlp, "entrada_ia_generativa": est_ia},
             "texto": exportar_texto(seg_nlp),
             "rag": exportar_rag(seg_nlp + seg_ia)}
    if com_qa_chat:
        estat.update(exportar_qa_chat(seg_nlp))
    return estat
