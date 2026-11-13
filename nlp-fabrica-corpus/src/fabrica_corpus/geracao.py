"""Etapa 7 da Fábrica de Corpus: geração das perguntas e dos diálogos.

Um modelo aberto da família Qwen, rodando na GPU do Colab, lê um segmento real
e escreve perguntas e respostas (corpus_qa) e diálogos (corpus_chat) SOMENTE
com o que está no segmento. Cada exemplo guarda a fonte, as páginas e o id do
segmento de origem.

Travas contra invenção (cada exemplo passa por todas, senão é refeito; depois
de 3 tentativas, o segmento é pulado e contado no relatório):
 1. a saída tem que ser um JSON no formato pedido;
 2. todo número citado na resposta (telefone, prazo, quantidade) tem que estar
    no segmento, salvo os números de emergência;
 3. a maior parte das palavras importantes da resposta tem que estar no segmento;
 4. nada de marcações da anonimização ([NOME] etc.) nem de nomes inventados.

Cache: cada resposta do modelo é guardada em dados/cache_geracao/, com a versão
do prompt no nome. Rodar de novo (no vídeo ou na correção) reaproveita tudo e
leva segundos; só o que mudou é gerado outra vez.

O modelo é "plugável": gerar_qa e gerar_chat recebem uma função
gerar(mensagens) -> texto. No Colab, ela vem de carregar_qwen(); nos testes,
de um gerador falso. Assim a lógica é testada sem GPU.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Callable, Iterable

MODELO_GERADOR = "Qwen/Qwen2.5-7B-Instruct"   # confirmar no primeiro teste no Colab
VERSAO_PROMPT = "v1"
EMERGENCIA = {"190", "192", "193", "199", "40199", "156"}
TENTATIVAS = 3

PERSONA_ASSISTENTE = (
    "Você é o assistente do Radar Cidadão, um app que orienta moradores de áreas sujeitas "
    "a alagamento e deslizamento. Fale de forma acolhedora, direta e com frases curtas. "
    "Responda SOMENTE com base no trecho oficial fornecido; não acrescente nada que não "
    "esteja nele. Em situação de risco imediato, oriente primeiro a ligar para a Defesa "
    "Civil (199) ou os Bombeiros (193). Se o trecho não traz a resposta, diga que não sabe."
)
PERSONA_CIDADAO = (
    "O cidadão mora em bairro de periferia, em área de risco, usa o celular e fala de forma "
    "simples, às vezes com pressa ou medo. Pergunta sobre o antes (como se preparar), o "
    "durante (o que fazer na hora) e o depois (limpeza, doenças, documentos)."
)

PROMPT_QA = """{persona_assistente}

{persona_cidadao}

Trecho oficial (fonte: {fonte}):
\"\"\"{texto}\"\"\"

Escreva {n} perguntas que esse cidadão faria e que o trecho responde, cada uma com a
resposta do assistente. Regras: a resposta usa só informação do trecho; não cite
nomes de pessoas; não invente números, telefones nem prazos.
Responda APENAS com JSON, sem texto antes ou depois:
{{"perguntas": [{{"pergunta": "...", "resposta": "..."}}]}}"""

PROMPT_CHAT = """{persona_assistente}

{persona_cidadao}

Trecho oficial (fonte: {fonte}):
\"\"\"{texto}\"\"\"

Escreva um diálogo de {turnos} trocas entre o cidadão e o assistente sobre o que o
trecho explica. O cidadão começa. Regras: o assistente usa só informação do trecho;
não cite nomes de pessoas; não invente números, telefones nem prazos.
Responda APENAS com JSON, sem texto antes ou depois:
{{"mensagens": [{{"papel": "cidadao", "texto": "..."}}, {{"papel": "assistente", "texto": "..."}}]}}"""

# palavras que indicam conteúdo útil para o cidadão (para escolher segmentos)
_TEMAS = re.compile(r"chuva|alag|enchente|inunda|desliza|encosta|defesa civil|água|leptospirose|"
                    r"abrigo|evacua|alerta|risco|doença|limpeza|lama|córrego|bueiro", re.I)
_STOP = set("a o os as de da do das dos e em no na nos nas um uma para por com que se ao à é "
            "ser ou mais como seu sua seus suas sobre pelo pela pelos pelas não sim já".split())


# ------------------------------------------------------------ escolha dos segmentos
def selecionar(segmentos: list, quantidade: int, semente: int = 42, excluir: set = frozenset()) -> list:
    """Escolhe segmentos úteis ao cidadão, espalhados entre os documentos.

    Prioriza segmentos com mais termos do tema; reparte entre as fontes para
    não sair tudo do Mapeamento (o maior documento). Determinístico (semente).
    """
    candidatos = [s for s in segmentos if s.id not in excluir and s.tokens >= 120]
    rng = random.Random(semente)
    por_fonte: dict[str, list] = {}
    for s in candidatos:
        por_fonte.setdefault(s.fonte, []).append(s)
    for lista in por_fonte.values():
        rng.shuffle(lista)
        lista.sort(key=lambda s: len(_TEMAS.findall(s.texto)), reverse=True)
    escolhidos = []
    while len(escolhidos) < quantidade and any(por_fonte.values()):
        for fonte in sorted(por_fonte):
            if por_fonte[fonte] and len(escolhidos) < quantidade:
                escolhidos.append(por_fonte[fonte].pop(0))
    return escolhidos


# ------------------------------------------------------------ travas
def _palavras(texto: str) -> set[str]:
    return {p for p in re.findall(r"[a-zà-ÿ]{4,}", texto.lower()) if p not in _STOP}


def _numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", texto))


def conferir_fidelidade(resposta: str, trecho: str, minimo: float = 0.6) -> tuple[bool, str]:
    """Confere se a resposta não inventa nada que não esteja no trecho."""
    if re.search(r"\[(NOME|CPF|EMAIL|TELEFONE)\]", resposta):
        return False, "marcação de anonimização na resposta"
    novos = _numeros(resposta) - _numeros(trecho) - EMERGENCIA
    if novos:
        return False, f"número que não está no trecho: {sorted(novos)}"
    palavras = _palavras(resposta)
    if palavras:
        cobertura = len(palavras & _palavras(trecho)) / len(palavras)
        if cobertura < minimo:
            return False, f"só {cobertura:.0%} das palavras da resposta estão no trecho"
    return True, "ok"


def _extrair_json(saida: str) -> dict:
    inicio, fim = saida.find("{"), saida.rfind("}")
    if inicio < 0 or fim < 0:
        raise ValueError("saída sem JSON")
    return json.loads(saida[inicio:fim + 1])


# ------------------------------------------------------------ cache
def _chave(tipo: str, seg, extra: str) -> str:
    h = hashlib.sha256(f"{VERSAO_PROMPT}|{MODELO_GERADOR}|{tipo}|{extra}|{seg.texto}".encode()).hexdigest()[:12]
    return f"{tipo}_{seg.id}_{VERSAO_PROMPT}_{h}.json"


def _com_cache(pasta: Path | None, nome: str, produzir: Callable[[], dict]) -> dict:
    if pasta is None:
        return produzir()
    arquivo = Path(pasta) / nome
    if arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))
    dados = produzir()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return dados


# ------------------------------------------------------------ geração
def _mensagens(prompt: str) -> list[dict]:
    return [{"role": "user", "content": prompt}]


def _gerar_qa_segmento(seg, gerar, n: int) -> dict:
    prompt = PROMPT_QA.format(persona_assistente=PERSONA_ASSISTENTE, persona_cidadao=PERSONA_CIDADAO,
                              fonte=seg.fonte, texto=seg.texto, n=n)
    ultimo_motivo = ""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            itens = _extrair_json(gerar(_mensagens(prompt)))["perguntas"]
        except (ValueError, KeyError, TypeError) as erro:
            ultimo_motivo = f"JSON inválido: {erro}"
            continue
        aprovados, motivos = [], []
        for item in itens:
            p, r = str(item.get("pergunta", "")).strip(), str(item.get("resposta", "")).strip()
            ok, motivo = conferir_fidelidade(r, seg.texto)
            if p and r and ok:
                aprovados.append({"pergunta": p, "resposta": r})
            else:
                motivos.append(motivo)
        if aprovados:
            return {"itens": aprovados[:n], "tentativas": tentativa, "descartados": motivos}
        ultimo_motivo = "; ".join(motivos) or "nenhum item"
    return {"itens": [], "tentativas": TENTATIVAS, "descartados": [ultimo_motivo]}


def _gerar_chat_segmento(seg, gerar, turnos: int) -> dict:
    prompt = PROMPT_CHAT.format(persona_assistente=PERSONA_ASSISTENTE, persona_cidadao=PERSONA_CIDADAO,
                                fonte=seg.fonte, texto=seg.texto, turnos=turnos)
    ultimo_motivo = ""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            msgs = _extrair_json(gerar(_mensagens(prompt)))["mensagens"]
        except (ValueError, KeyError, TypeError) as erro:
            ultimo_motivo = f"JSON inválido: {erro}"
            continue
        papeis = [m.get("papel") for m in msgs]
        if len(msgs) < 4 or papeis[0] != "cidadao" or any(
                papeis[i] == papeis[i + 1] for i in range(len(papeis) - 1)):
            ultimo_motivo = "diálogo sem alternância cidadão/assistente ou curto demais"
            continue
        respostas = [m.get("texto", "") for m in msgs if m.get("papel") == "assistente"]
        falhas = [motivo for ok, motivo in (conferir_fidelidade(r, seg.texto) for r in respostas) if not ok]
        if not falhas:
            return {"mensagens": msgs, "tentativas": tentativa, "descartados": []}
        ultimo_motivo = "; ".join(falhas)
    return {"mensagens": [], "tentativas": TENTATIVAS, "descartados": [ultimo_motivo]}


def gerar_qa(segmentos: Iterable, gerar: Callable[[list], str], total: int = 100, por_segmento: int = 2,
             pasta_cache: Path | None = None) -> tuple[list[dict], dict]:
    """Gera cerca de `total` perguntas e respostas. Devolve (exemplos, estatísticas)."""
    segmentos = list(segmentos)
    exemplos, pulados, descartes = [], [], 0
    usados: set = set()
    while len(exemplos) < total:
        faltam = total - len(exemplos)
        lote = selecionar(segmentos, -(-faltam // por_segmento), excluir=usados)
        if not lote:
            break
        for seg in lote:
            usados.add(seg.id)
            res = _com_cache(pasta_cache, _chave("qa", seg, str(por_segmento)),
                             lambda: _gerar_qa_segmento(seg, gerar, por_segmento))
            descartes += len(res["descartados"])
            if not res["itens"]:
                pulados.append(seg.id)
            for item in res["itens"]:
                if len(exemplos) < total:
                    exemplos.append({"id": f"qa_{len(exemplos) + 1:04d}", **item, "fonte": seg.fonte,
                                     "paginas": seg.paginas, "segmento_id": seg.id, "modelo": MODELO_GERADOR})
    return exemplos, {"exemplos": len(exemplos), "segmentos_usados": len(usados),
                      "segmentos_pulados": pulados, "respostas_descartadas": descartes}


def gerar_chat(segmentos: Iterable, gerar: Callable[[list], str], total: int = 30, turnos: int = 3,
               pasta_cache: Path | None = None, excluir: set = frozenset()) -> tuple[list[dict], dict]:
    """Gera cerca de `total` diálogos no formato de mensagens (system/user/assistant)."""
    segmentos = list(segmentos)
    exemplos, pulados = [], []
    usados: set = set(excluir)
    while len(exemplos) < total:
        lote = selecionar(segmentos, total - len(exemplos), semente=7, excluir=usados)
        if not lote:
            break
        for seg in lote:
            usados.add(seg.id)
            res = _com_cache(pasta_cache, _chave("chat", seg, str(turnos)),
                             lambda: _gerar_chat_segmento(seg, gerar, turnos))
            if not res["mensagens"]:
                pulados.append(seg.id)
                continue
            mensagens = [{"role": "system", "content": PERSONA_ASSISTENTE}] + [
                {"role": "user" if m["papel"] == "cidadao" else "assistant", "content": m["texto"]}
                for m in res["mensagens"]]
            exemplos.append({"id": f"chat_{len(exemplos) + 1:04d}", "mensagens": mensagens, "fonte": seg.fonte,
                             "paginas": seg.paginas, "segmento_id": seg.id, "modelo": MODELO_GERADOR})
    return exemplos, {"exemplos": len(exemplos), "segmentos_pulados": pulados}


def amostra_revisao(exemplos: list[dict], proporcao: float = 0.2, semente: int = 2026) -> list[dict]:
    """Sorteia a amostra (mínimo 20%) que o grupo revisa à mão."""
    n = max(1, math.ceil(len(exemplos) * proporcao))
    return random.Random(semente).sample(exemplos, min(n, len(exemplos)))


# ------------------------------------------------------------ Qwen no Colab
def carregar_qwen(modelo: str = MODELO_GERADOR, max_tokens: int = 700):
    """Carrega o Qwen quantizado em 4 bits na GPU do Colab e devolve gerar(mensagens)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tok = AutoTokenizer.from_pretrained(modelo)
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_quant_type="nf4")
    lm = AutoModelForCausalLM.from_pretrained(modelo, quantization_config=quant, device_map="auto")

    def gerar(mensagens: list[dict]) -> str:
        entrada = tok.apply_chat_template(mensagens, add_generation_prompt=True, return_tensors="pt").to(lm.device)
        saida = lm.generate(entrada, max_new_tokens=max_tokens, do_sample=True, temperature=0.4, top_p=0.9)
        return tok.decode(saida[0][entrada.shape[1]:], skip_special_tokens=True)
    return gerar
