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
 4. nada de marcações da anonimização ([NOME] etc.) nem de nomes inventados;
 5. nada de falar "do trecho" ou "disso aqui", como se o leitor visse o documento;
 6. juiz de coerência: o próprio modelo relê cada par com o trecho e confere se a
    resposta responde a pergunta e se quem age é o mesmo nos dois.

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

MODELO_GERADOR = "Qwen/Qwen2.5-14B-Instruct"  # 14B em 4 bits: segue melhor as regras (o 7B confundia quem age)
VERSAO_PROMPT = "v5"   # v5: modelo 14B + juiz de coerência + trava de referência ao texto
EMERGENCIA = {"190", "192", "193", "199", "40199", "156"}

# Título legível de cada documento, para o assistente citar a fonte na resposta
# ("Segundo a Cartilha do Ministério da Saúde (2017), ...") em vez do nome do arquivo.
TITULOS = {
    "mcid_2026_mapeamento_riscos.pdf": "Mapeamento de Riscos, do Ministério das Cidades (2026)",
    "ms_2025_plano_contingencia_chuvas.pdf": "Plano de Contingência para Chuvas Intensas, do Ministério da Saúde (2025)",
    "mcid_2024_periferia_sem_risco.pdf": "Periferia Sem Risco, do Ministério das Cidades (2024)",
    "ms_2017_cartilha_alerta_chuvas.pdf": "Cartilha de Alerta de Chuvas Intensas, do Ministério da Saúde (2017)",
    "ms_2026_enchentes.html": "página Enchentes, do Ministério da Saúde",
    "mdr_2021_guia_alertas_desastres.pdf": "Guia Prático de Alertas, do Ministério do Desenvolvimento Regional (2021)",
    "mi_2003_manual_desastres_naturais.pdf": "Manual de Desastres Naturais, do Ministério da Integração Nacional (2003)",
    "pmsp_2024_chuvas_excessivas.pdf": "orientações da Defesa Civil da Prefeitura de São Paulo (2024)",
    "cgesp_2026_dicas_alagamentos.docx": "dicas do CGE da Prefeitura de São Paulo",
}


def titulo(fonte: str) -> str:
    return TITULOS.get(fonte, fonte)


def citacao(fonte: str, paginas: list) -> str:
    """Citação da fonte, acrescentada pelo código no fim das respostas.

    O modelo não cita de forma confiável (no teste de 13/11 ignorou o pedido),
    então a citação é garantida aqui, sempre no mesmo formato:
    "Fonte: Periferia Sem Risco, do Ministério das Cidades (2024), p. 7-9."
    """
    paginas = paginas or []
    if not paginas:
        return f"Fonte: {titulo(fonte)}."
    pags = f"p. {paginas[0]}" if len(paginas) == 1 else f"p. {paginas[0]}-{paginas[-1]}"
    return f"Fonte: {titulo(fonte)}, {pags}."
TENTATIVAS = 3

PERSONA_ASSISTENTE = (
    "Você é o assistente do Radar Cidadão, um app que orienta moradores de áreas sujeitas "
    "a alagamento e deslizamento. Fale de forma acolhedora, direta e com frases curtas. "
    "Responda SOMENTE com base no trecho oficial fornecido, citando a fonte; não acrescente "
    "nada que não esteja nele. Em situação de risco imediato, oriente primeiro a ligar para a Defesa "
    "Civil (199) ou os Bombeiros (193). Se o trecho não traz a resposta, diga que não sabe."
)
# No prompt de geração, a persona vai sem o "citando a fonte": a citação é colocada
# pelo código depois, e pedir ao modelo geraria citação duplicada.
PERSONA_GERACAO = PERSONA_ASSISTENTE.replace(", citando a fonte", "")

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
resposta do assistente. Regras:
- a pergunta diz o assunto e faz sentido sozinha (ruim: "Como me preparar?"; bom:
  "Como me preparar para um deslizamento de terra?");
- a resposta responde exatamente o que foi perguntado, usando só informação do trecho;
- a pergunta segue QUEM AGE no trecho: se o trecho diz o que o morador faz, pergunte
  "o que eu faço..."; se diz o que a prefeitura, a Defesa Civil ou a saúde fazem,
  pergunte "o que a prefeitura faz..." (nunca "como eu me preparo" para uma ação do
  governo); se explica um conceito, pergunte "o que é..." ou "por que acontece...";
- a resposta usa linguagem simples, sem acrescentar nada que o trecho não diga;
- não cite nomes de pessoas; não invente números, telefones nem prazos;
- não escreva a fonte na resposta: ela é acrescentada automaticamente.
Responda APENAS com JSON, sem texto antes ou depois:
{{"perguntas": [{{"pergunta": "...", "resposta": "..."}}]}}"""

PROMPT_CHAT = """{persona_assistente}

{persona_cidadao}

Trecho oficial (fonte: {fonte}):
\"\"\"{texto}\"\"\"

Escreva um diálogo de {turnos} trocas entre o cidadão e o assistente sobre o que o
trecho explica. O cidadão começa. Regras:
- o cidadão só pergunta coisas que o trecho responde, e cada fala do assistente
  responde exatamente a pergunta anterior (se perguntarem "o que fazer depois",
  a resposta é sobre depois);
- as perguntas do cidadão seguem QUEM AGE no trecho: o que ele mesmo pode fazer, o que
  a prefeitura, a Defesa Civil ou a saúde fazem, ou o que significa um conceito; nunca
  peça ao morador uma ação que no trecho é do governo;
- o assistente responde em linguagem simples, sem acrescentar nada;
- não cite nomes de pessoas; não invente números, telefones nem prazos;
- não escreva a fonte: ela é acrescentada automaticamente.
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
    """Radicais das palavras importantes: as 5 primeiras letras.

    "alagamentos" e "alagamento", "moradores" e "morador" contam como a mesma
    palavra. Assim a trava aceita a resposta reescrita em linguagem simples e
    continua recusando a que fala de coisas que não estão no trecho.
    """
    return {p[:5] for p in re.findall(r"[a-zà-ÿ]{4,}", texto.lower()) if p not in _STOP}


def _numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", texto))


def conferir_fidelidade(resposta: str, trecho: str, minimo: float = 0.4) -> tuple[bool, str]:
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


def _extrair_json(saida: str, chave: str = "mensagens") -> dict:
    """Lê o JSON da saída do modelo, mesmo quando ele foge do formato.

    O Qwen às vezes escreve vários objetos seguidos (um bloco por troca do
    diálogo, uma fala por objeto, ou o bloco repetido) em vez de um só. Aqui
    todos os objetos são lidos e juntados: blocos de "mensagens" viram um
    diálogo só; blocos de "perguntas" são somados sem repetir; falas soltas
    ({"papel": ..., "texto": ...}) viram a lista "mensagens".
    """
    decoder = json.JSONDecoder()
    objetos, i = [], saida.find("{")
    while 0 <= i < len(saida):
        try:
            obj, fim = decoder.raw_decode(saida, i)
        except json.JSONDecodeError:
            i = saida.find("{", i + 1)
            continue
        objetos.append(obj)
        i = saida.find("{", fim)
    if not objetos:
        raise ValueError("saída sem JSON")
    # junta todos os blocos que têm a chave pedida ("perguntas" ou "mensagens"):
    # o Qwen às vezes escreve cada troca do diálogo num bloco separado
    blocos = [o[chave] for o in objetos if isinstance(o, dict) and isinstance(o.get(chave), list)]
    if blocos:
        vistos, juntos = set(), []
        for item in (i for bloco in blocos for i in bloco):
            marca = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if chave == "mensagens" or marca not in vistos:   # bloco repetido não duplica perguntas
                vistos.add(marca)
                juntos.append(item)
        return {chave: juntos}
    falas = [o for o in objetos if isinstance(o, dict) and "papel" in o and "texto" in o]
    if falas:
        return {"mensagens": falas}
    perguntas = [o for o in objetos if isinstance(o, dict) and "pergunta" in o and "resposta" in o]
    if perguntas:
        return {"perguntas": perguntas}
    raise ValueError("JSON sem perguntas nem mensagens")



# ------------------------------------------------------------ juiz de coerência
# As travas acima pegam invenção (números, palavras fora do trecho). Não pegam
# incoerência: pergunta de um agente e resposta de outro, resposta que não
# responde, texto que fala "do trecho". A revisão de 13/11 achou ~35% assim no 7B.
# O juiz é o próprio modelo relendo cada par com o trecho e respondendo 3 perguntas.
USAR_JUIZ = True

_REFERENCIA_AO_TEXTO = re.compile(
    r"\b(o|este|esse|neste|nesse|do|no)\s+(trecho|texto|documento|material)\b|\bisso aqui\b|\bde acordo com o trecho\b",
    re.I)

PROMPT_JUIZ = """Você revisa exemplos de perguntas e respostas para um assistente que orienta moradores
de áreas de risco de alagamento e deslizamento. Leia o trecho oficial e AVALIE cada par.

Trecho oficial:
\"\"\"{texto}\"\"\"

Pares:
{pares}

Para cada par, responda:
- responde: a resposta responde exatamente o que a pergunta pede? (false se fala de outra coisa,
  só repete a pergunta, ou responde "antes" quando perguntaram "depois")
- mesmo_agente: quem age é o mesmo na pergunta e na resposta? (false se a pergunta é "o que EU
  faço" e a resposta é uma ação da prefeitura, da Defesa Civil ou da saúde, ou o contrário; e
  false se a pergunta cita a prefeitura mas o trecho fala de outro órgão)
- motivo: uma frase curta quando algum item for false.
Responda APENAS com JSON:
{{"avaliacoes": [{{"par": 1, "responde": true, "mesmo_agente": true, "motivo": ""}}]}}"""


def _referencia_ao_texto(*textos: str) -> bool:
    return any(_REFERENCIA_AO_TEXTO.search(t or "") for t in textos)


def julgar(pares: list[tuple[str, str]], trecho: str, gerar) -> list[tuple[bool, str]]:
    """Avalia cada (pergunta, resposta) com o modelo. Devolve [(aprovado, motivo)]."""
    texto_pares = "\n".join(f"{i}. Pergunta: {p}\n   Resposta: {r}" for i, (p, r) in enumerate(pares, start=1))
    saida = gerar(_mensagens(PROMPT_JUIZ.format(texto=trecho, pares=texto_pares)))
    try:
        avaliacoes = _extrair_json(saida, "avaliacoes")["avaliacoes"]
    except (ValueError, KeyError, TypeError):
        return [(False, "juiz: saída ilegível")] * len(pares)
    resultado = []
    for i in range(len(pares)):
        a = next((x for x in avaliacoes if isinstance(x, dict) and x.get("par") == i + 1),
                 avaliacoes[i] if i < len(avaliacoes) and isinstance(avaliacoes[i], dict) else None)
        if a is None:
            resultado.append((False, "juiz: par sem avaliação"))
        elif a.get("responde") is True and a.get("mesmo_agente") is True:
            resultado.append((True, "ok"))
        else:
            falhas = [nome for nome in ("responde", "mesmo_agente") if a.get(nome) is not True]
            resultado.append((False, f"juiz ({', '.join(falhas)}): {a.get('motivo', '')}".strip()))
    return resultado


# ------------------------------------------------------------ cache
def _chave(tipo: str, seg, extra: str) -> str:
    extra = f"{extra}|juiz={USAR_JUIZ}"
    h = hashlib.sha256(f"{VERSAO_PROMPT}|{MODELO_GERADOR}|{tipo}|{extra}|{seg.texto}".encode()).hexdigest()[:12]
    return f"{tipo}_{seg.id}_{VERSAO_PROMPT}_{h}.json"


def _deu_certo(dados: dict) -> bool:
    return bool(dados.get("itens") or dados.get("mensagens"))


def _com_cache(pasta: Path | None, nome: str, produzir: Callable[[], dict]) -> dict:
    """Reaproveita o que já deu certo. Recusa não é guardada: depois de um ajuste
    no código ou no prompt, o segmento é tentado de novo."""
    if pasta is None:
        return produzir()
    arquivo = Path(pasta) / nome
    if arquivo.exists():
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        if _deu_certo(dados):
            return dados
    dados = produzir()
    if _deu_certo(dados):
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return dados


# ------------------------------------------------------------ geração
def _mensagens(prompt: str) -> list[dict]:
    return [{"role": "user", "content": prompt}]


def _gerar_qa_segmento(seg, gerar, n: int, juiz: bool | None = None) -> dict:
    prompt = PROMPT_QA.format(persona_assistente=PERSONA_GERACAO, persona_cidadao=PERSONA_CIDADAO,
                              fonte=titulo(seg.fonte), texto=seg.texto, n=n)
    ultimo_motivo = ""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            itens = _extrair_json(gerar(_mensagens(prompt)), "perguntas")["perguntas"]
        except (ValueError, KeyError, TypeError) as erro:
            ultimo_motivo = f"JSON inválido: {erro}"
            continue
        aprovados, motivos = [], []
        for item in itens:
            p, r = str(item.get("pergunta", "")).strip(), str(item.get("resposta", "")).strip()
            ok, motivo = conferir_fidelidade(r, seg.texto + " " + titulo(seg.fonte))
            if ok and _referencia_ao_texto(p, r):
                ok, motivo = False, "fala do trecho como se o leitor visse o documento"
            if p and r and ok:
                aprovados.append({"pergunta": p, "resposta": r})
            else:
                motivos.append(motivo)
        if aprovados and (USAR_JUIZ if juiz is None else juiz):
            vereditos = julgar([(a["pergunta"], a["resposta"]) for a in aprovados], seg.texto, gerar)
            motivos += [m for ok, m in vereditos if not ok]
            aprovados = [a for a, (ok, _) in zip(aprovados, vereditos) if ok]
        if aprovados:
            return {"itens": aprovados[:n], "tentativas": tentativa, "descartados": motivos}
        ultimo_motivo = "; ".join(motivos) or "nenhum item"
    return {"itens": [], "tentativas": TENTATIVAS, "descartados": [ultimo_motivo]}


def _gerar_chat_segmento(seg, gerar, turnos: int, juiz: bool | None = None) -> dict:
    prompt = PROMPT_CHAT.format(persona_assistente=PERSONA_GERACAO, persona_cidadao=PERSONA_CIDADAO,
                                fonte=titulo(seg.fonte), texto=seg.texto, turnos=turnos)
    ultimo_motivo = ""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            msgs = _extrair_json(gerar(_mensagens(prompt)), "mensagens")["mensagens"]
        except (ValueError, KeyError, TypeError) as erro:
            ultimo_motivo = f"JSON inválido: {erro}"
            continue
        papeis = [m.get("papel") for m in msgs]
        if len(msgs) < 4 or papeis[0] != "cidadao" or any(
                papeis[i] == papeis[i + 1] for i in range(len(papeis) - 1)):
            ultimo_motivo = "diálogo sem alternância cidadão/assistente ou curto demais"
            continue
        respostas = [m.get("texto", "") for m in msgs if m.get("papel") == "assistente"]
        referencia = seg.texto + " " + titulo(seg.fonte)   # citar a fonte não conta como invenção
        falhas = [motivo for ok, motivo in (conferir_fidelidade(r, referencia) for r in respostas) if not ok]
        if not falhas and _referencia_ao_texto(*(m.get("texto", "") for m in msgs)):
            falhas = ["fala do trecho como se o leitor visse o documento"]
        if not falhas and (USAR_JUIZ if juiz is None else juiz):
            pares = [(msgs[i].get("texto", ""), msgs[i + 1].get("texto", ""))
                     for i in range(0, len(msgs) - 1, 2)]
            falhas = [m for ok, m in julgar(pares, seg.texto, gerar) if not ok]
        if not falhas:
            return {"mensagens": msgs, "tentativas": tentativa, "descartados": []}
        ultimo_motivo = "; ".join(falhas)
    return {"mensagens": [], "tentativas": TENTATIVAS, "descartados": [ultimo_motivo]}


def gerar_qa(segmentos: Iterable, gerar: Callable[[list], str], total: int = 100, por_segmento: int = 2,
             pasta_cache: Path | None = None, progresso: bool = True,
             juiz: bool | None = None) -> tuple[list[dict], dict]:
    """Gera cerca de `total` perguntas e respostas. Devolve (exemplos, estatísticas).

    juiz: None usa USAR_JUIZ (ligado); False desliga a checagem de coerência."""
    segmentos = list(segmentos)
    exemplos, pulados, descartes = [], [], 0
    usados: set = set()
    teto = max(3 * -(-total // por_segmento), 6)        # no máximo 3 segmentos por segmento necessário
    while len(exemplos) < total and len(usados) < teto:
        faltam = total - len(exemplos)
        lote = selecionar(segmentos, min(-(-faltam // por_segmento), teto - len(usados)), excluir=usados)
        if not lote:
            break
        for seg in lote:
            usados.add(seg.id)
            res = _com_cache(pasta_cache, _chave("qa", seg, str(por_segmento)),
                             lambda: _gerar_qa_segmento(seg, gerar, por_segmento, juiz))
            descartes += len(res["descartados"])
            if not res["itens"]:
                pulados.append(seg.id)
            for item in res["itens"]:
                if len(exemplos) < total:
                    resposta = f"{item['resposta']}\n\n{citacao(seg.fonte, seg.paginas)}"
                    exemplos.append({"id": f"qa_{len(exemplos) + 1:04d}", "pergunta": item["pergunta"],
                                     "resposta": resposta, "fonte": seg.fonte, "paginas": seg.paginas,
                                     "segmento_id": seg.id, "modelo": MODELO_GERADOR})
            if progresso:
                print(f"[perguntas] {len(exemplos)}/{total} | segmento {seg.id} | "
                      f"{len(res['itens'])} aprovadas, {res['tentativas']} tentativa(s)", flush=True)
    return exemplos, {"exemplos": len(exemplos), "segmentos_usados": len(usados),
                      "segmentos_pulados": pulados, "respostas_descartadas": descartes}


def gerar_chat(segmentos: Iterable, gerar: Callable[[list], str], total: int = 30, turnos: int = 3,
               pasta_cache: Path | None = None, excluir: set = frozenset(),
               progresso: bool = True, juiz: bool | None = None) -> tuple[list[dict], dict]:
    """Gera cerca de `total` diálogos no formato de mensagens (system/user/assistant)."""
    segmentos = list(segmentos)
    exemplos, pulados = [], []
    usados: set = set(excluir)
    tentados, teto = 0, max(3 * total, 6)               # no máximo 3 segmentos por diálogo pedido
    while len(exemplos) < total and tentados < teto:
        lote = selecionar(segmentos, min(total - len(exemplos), teto - tentados), semente=7, excluir=usados)
        if not lote:
            break
        for seg in lote:
            usados.add(seg.id)
            tentados += 1
            res = _com_cache(pasta_cache, _chave("chat", seg, str(turnos)),
                             lambda: _gerar_chat_segmento(seg, gerar, turnos, juiz))
            if progresso:
                print(f"[diálogos] {len(exemplos) + bool(res['mensagens'])}/{total} | segmento {seg.id} | "
                      f"{'ok' if res['mensagens'] else 'pulado'}, {res['tentativas']} tentativa(s)", flush=True)
            if not res["mensagens"]:
                pulados.append(seg.id)
                continue
            mensagens = [{"role": "system", "content": PERSONA_ASSISTENTE}] + [
                {"role": "user" if m["papel"] == "cidadao" else "assistant", "content": m["texto"]}
                for m in res["mensagens"]]
            # citação automática na última fala do assistente
            ultima = max(i for i, m in enumerate(mensagens) if m["role"] == "assistant")
            mensagens[ultima]["content"] += f"\n\n{citacao(seg.fonte, seg.paginas)}"
            exemplos.append({"id": f"chat_{len(exemplos) + 1:04d}", "mensagens": mensagens, "fonte": seg.fonte,
                             "paginas": seg.paginas, "segmento_id": seg.id, "modelo": MODELO_GERADOR})
    return exemplos, {"exemplos": len(exemplos), "segmentos_tentados": tentados, "segmentos_pulados": pulados}


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
        # return_dict=True: no transformers 5 o apply_chat_template devolve um dicionário
        # (input_ids + attention_mask); pedir explicitamente funciona no 4 e no 5
        entrada = tok.apply_chat_template(mensagens, add_generation_prompt=True,
                                          return_tensors="pt", return_dict=True).to(lm.device)
        saida = lm.generate(**entrada, max_new_tokens=max_tokens, do_sample=True,
                            temperature=0.4, top_p=0.9, pad_token_id=tok.eos_token_id)
        inicio = entrada["input_ids"].shape[1]
        return tok.decode(saida[0][inicio:], skip_special_tokens=True)
    return gerar
