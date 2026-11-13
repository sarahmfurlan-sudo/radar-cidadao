"""Etapa 6 da Fábrica de Corpus: segmentação.

Junta os trechos de cada documento e corta em segmentos de 256 a 512 tokens,
sempre terminando em fim de frase ou de parágrafo. Cada segmento guarda a
fonte e as páginas de onde veio, para o RAG citar e para a análise de
alucinação conferir.

Tokens: contados com o tokenizador do Qwen (o mesmo modelo que vai ver o
texto). A família Qwen 2.5 / 3 usa o mesmo vocabulário, então a contagem vale
para o modelo que o grupo escolher dentro dela. Para trocar, mude
MODELO_TOKENIZADOR. Nos testes, um contador simples é passado no lugar.

Regras:
 - um segmento nunca mistura documentos;
 - um segmento pode atravessar páginas (o parágrafo continua na página seguinte);
 - corta em fim de frase; nunca no meio de uma frase, salvo frase com mais de
   512 tokens sozinha (tabela achatada), que é cortada por palavras;
 - sobra menor que 256 tokens no fim do documento é juntada ao segmento
   anterior se couber em 512; senão fica como segmento curto (contado no
   relatório). Documento inteiro menor que 256 vira um segmento curto.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Iterable

MODELO_TOKENIZADOR = "Qwen/Qwen2.5-7B-Instruct"
MINIMO, MAXIMO = 256, 512


@dataclass
class Segmento:
    id: str
    fonte: str
    tipo: str
    paginas: list = field(default_factory=list)   # vazio para TXT, DOCX, HTML e texto colado
    texto: str = ""
    tokens: int = 0


# ------------------------------------------------------------ contagem de tokens
@lru_cache(maxsize=1)
def _tokenizador():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODELO_TOKENIZADOR)


def contar_tokens_qwen(texto: str) -> int:
    return len(_tokenizador().encode(texto, add_special_tokens=False))


# ------------------------------------------------------------ frases
# abreviações que terminam em ponto mas não terminam frase
_ABREV = ["Sr", "Sra", "Dr", "Dra", "Art", "art", "n", "p", "v", "ex", "Ltda", "al", "Prof", "aprox"]
_ABREVIACOES = "".join(rf"(?<!\b{a}\.)" for a in _ABREV)
_FIM_DE_FRASE = re.compile(r"(?<=[.!?;:])" + _ABREVIACOES + r"\s+(?=[\"'(]?[A-ZÀ-Ú0-9\-•])")


def dividir_frases(texto: str) -> list[str]:
    """Divide em frases. Parágrafo e item de lista também encerram frase."""
    frases = []
    for paragrafo in re.split(r"\n+", texto):
        paragrafo = paragrafo.strip()
        if paragrafo:
            frases.extend(f.strip() for f in _FIM_DE_FRASE.split(paragrafo) if f.strip())
    return frases


# ------------------------------------------------------------ segmentação
def _cortar_frase_grande(frase: str, contar: Callable[[str], int]) -> list[str]:
    """Frase maior que o máximo (tabela achatada): corta por palavras."""
    partes, atual = [], []
    for palavra in frase.split():
        if atual and contar(" ".join(atual + [palavra])) > MAXIMO:
            partes.append(" ".join(atual))
            atual = []
        atual.append(palavra)
    if atual:
        partes.append(" ".join(atual))
    return partes


def _segmentar_documento(frases: list[tuple[str, object]], contar) -> list[tuple[str, list]]:
    """frases: (frase, pagina). Devolve [(texto, paginas)]."""
    blocos: list[tuple[list[str], list]] = []
    atual, paginas, tokens_atual = [], [], 0
    for frase, pagina in frases:
        pedacos = [frase] if contar(frase) <= MAXIMO else _cortar_frase_grande(frase, contar)
        for pedaco in pedacos:
            t = contar(pedaco)
            if atual and tokens_atual + t + 1 > MAXIMO:
                blocos.append((atual, paginas))
                atual, paginas, tokens_atual = [], [], 0
            atual.append(pedaco)
            if pagina is not None and pagina not in paginas:
                paginas.append(pagina)
            tokens_atual = contar(" ".join(atual))
    if atual:
        blocos.append((atual, paginas))

    # sobra curta no fim: junta ao anterior se couber
    if len(blocos) >= 2:
        ultimo, penultimo = blocos[-1], blocos[-2]
        if contar(" ".join(ultimo[0])) < MINIMO:
            juntos = penultimo[0] + ultimo[0]
            if contar(" ".join(juntos)) <= MAXIMO:
                paginas_juntas = penultimo[1] + [p for p in ultimo[1] if p not in penultimo[1]]
                blocos[-2:] = [(juntos, paginas_juntas)]
    return [(" ".join(frases_bloco), pags) for frases_bloco, pags in blocos]


def segmentar(trechos: Iterable, contar: Callable[[str], int] | None = None) -> tuple[list[Segmento], dict]:
    """Segmenta os trechos já limpos e anonimizados. Devolve (segmentos, estatísticas)."""
    contar = contar or contar_tokens_qwen
    por_fonte: dict[str, list] = {}
    for t in trechos:
        por_fonte.setdefault(t.fonte, []).append(t)

    segmentos: list[Segmento] = []
    for fonte, lista in por_fonte.items():
        lista.sort(key=lambda t: (t.pagina is None, t.pagina or 0))
        frases = [(f, t.pagina) for t in lista for f in dividir_frases(t.texto)]
        base = re.sub(r"\.[^.]+$", "", fonte)
        for n, (texto, paginas) in enumerate(_segmentar_documento(frases, contar), start=1):
            segmentos.append(Segmento(id=f"{base}_{n:04d}", fonte=fonte, tipo=lista[0].tipo,
                                      paginas=paginas, texto=texto, tokens=contar(texto)))

    tokens = [s.tokens for s in segmentos]
    estat = {
        "segmentos": len(segmentos),
        "tokens_media": round(sum(tokens) / len(tokens), 1) if tokens else 0,
        "tokens_min": min(tokens, default=0),
        "tokens_max": max(tokens, default=0),
        "segmentos_curtos": sum(1 for t in tokens if t < MINIMO),
        "segmentos_por_fonte": {f: sum(1 for s in segmentos if s.fonte == f) for f in por_fonte},
    }
    return segmentos, estat
