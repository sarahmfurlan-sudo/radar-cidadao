"""Etapas 3 e 4 da Fábrica de Corpus: limpeza e normalização.

Recebe os trechos da ingestão e devolve trechos com o mesmo formato
(fonte, tipo, pagina, texto), com o texto limpo. Não anonimiza nada:
isso é da etapa seguinte.

Ordem das regras (a ordem importa):
 1. normalizar_caracteres  - Unicode NFC, hífen invisível, espaços especiais, aspas, ligaduras
 2. remover_boilerplate    - menu, cookies, rodapé e copyright de páginas da web
 3. remover_repetidas      - cabeçalhos e rodapés que se repetem nas páginas do mesmo PDF (30%+)
 4. remover_numeros_pagina - linhas que só têm o número da página ("9", "16 17")
 5. remover_sumario        - linhas de sumário com pontilhado ("ALERTAS......07")
 6. juntar_hifenizacao     - "traba-\\nlhos" -> "trabalhos" e letra capitular "E\\nvidências"
 7. juntar_linhas          - linhas quebradas no meio da frase
 8. remover_referencias    - blocos de citações ABNT (com ou sem o título "REFERÊNCIAS")
 9. normalizar_espacos     - espaços repetidos e excesso de linhas em branco

Limites conhecidos (registrar no relatório):
 - espaço no meio da palavra por defeito da fonte do PDF só é corrigido no caso da
   letra capitular ("T odos" -> "Todos", só consoantes); fora disso ("ex emplo") não,
   porque uma regra geral erraria palavras normais;
 - espaço perdido entre duas palavras ("Vamosconversar") não é corrigido;
 - tabelas de PDF chegam com as colunas misturadas;
 - palavra composta quebrada exatamente no hífen ("bem-\\nestar") vira "bemestar".
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Iterable

# ----------------------------------------------------------------- 1. caracteres
_TROCAS = {
    "\u00ad": "",    # hífen invisível (soft hyphen)
    "\u200b": "",    # espaço de largura zero
    "\ufeff": "",    # marca de ordem de bytes
    "\u00a0": " ",   # espaço que não quebra
    "\u2009": " ", "\u202f": " ", "\u2002": " ", "\u2003": " ",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": " - ", "\u2212": "-",
    "\u2022": "-", "\uf0b7": "-", "\u25cf": "-",   # marcadores de lista
    "\ufb01": "fi", "\ufb02": "fl",                  # ligaduras
    "\r\n": "\n", "\r": "\n", "\t": " ",
}


def normalizar_caracteres(texto: str) -> str:
    # NFC junta letra + acento num só caractere. NFKC não: ele trocaria "º" por "o".
    texto = unicodedata.normalize("NFC", texto)
    # hífen invisível no fim da linha marca palavra quebrada: junta sem espaço
    texto = re.sub("\u00ad[ ]*\r?\n[ ]*", "", texto)
    for velho, novo in _TROCAS.items():
        texto = texto.replace(velho, novo)
    return texto


# -------------------------------------------------------------- 2. boilerplate web
# Blocos que começam e terminam em frases conhecidas (aviso de cookies).
_BLOCOS_WEB = [
    re.compile(r"[^\n]*valoriza sua privacidade.*?Saiba mais[^\n]*", re.S | re.I),
]
# Linhas inteiras de menu, navegação e rodapé.
_LINHAS_WEB = [
    re.compile(r"^\s*Acesso à informação\b.*$", re.I),
    re.compile(r"^\s*Órgãos Públicos\b.*$", re.I),
    re.compile(r"^\s*Início\s+Secretarias\b.*$", re.I),
    re.compile(r"^.*Procurar\.\.\..*$", re.I),
    re.compile(r"^.*(©|COPYRIGHT).*$", re.I),
    re.compile(r"^\s*(Configuração\s+)?Aceitar tudo\s+Recusar tudo\s*$", re.I),
    re.compile(r"^\s*(Info|Compartilhe|Imprimir)\s*$", re.I),
]


def remover_boilerplate(texto: str) -> str:
    for padrao in _BLOCOS_WEB:
        texto = padrao.sub("", texto)
    linhas = [l for l in texto.split("\n") if not any(p.match(l) for p in _LINHAS_WEB)]
    return "\n".join(linhas)


# ------------------------------------------------------- 3. cabeçalhos repetidos
def _chave_linha(linha: str) -> str:
    # números mudam de página para página ("Página 9", "16 17"): trocamos por #
    return re.sub(r"\d+", "#", linha.strip().lower())


# Cabeçalho e rodapé ficam nas 2 primeiras e 2 últimas linhas e são longos
# (título do livro). Olhar só as pontas e exigir 20+ caracteres evita apagar
# títulos de seção curtos que se repetem ("Caracterização", "Causas").
_ZONA = 2
_TAMANHO_MINIMO = 20


def _pontas(texto: str) -> list[tuple[int, str]]:
    linhas = [(i, l) for i, l in enumerate(texto.split("\n")) if l.strip()]
    if len(linhas) <= 2 * _ZONA:
        return linhas
    return linhas[:_ZONA] + linhas[-_ZONA:]


def linhas_repetidas(paginas: list[str], minimo_paginas: int = 3, proporcao: float = 0.3) -> set[str]:
    """Linhas das pontas da página que se repetem em pelo menos 30% das páginas.

    30%, e não 50%, porque muitos livros alternam o cabeçalho: o título do livro
    nas páginas ímpares e o do capítulo nas pares. Cada um fica em ~metade das
    páginas, ou menos, descontando capa e créditos.
    """
    if len(paginas) < minimo_paginas:
        return set()
    contagem = Counter()
    for texto in paginas:
        chaves = {_chave_linha(l) for _, l in _pontas(texto) if len(l.strip()) >= _TAMANHO_MINIMO}
        contagem.update(chaves)
    limite = max(minimo_paginas, proporcao * len(paginas))
    return {chave for chave, n in contagem.items() if n >= limite}


def remover_repetidas(texto: str, repetidas: set[str]) -> str:
    if not repetidas:
        return texto
    remover = {i for i, l in _pontas(texto) if _chave_linha(l) in repetidas}
    return "\n".join(l for i, l in enumerate(texto.split("\n")) if i not in remover)


# --------------------------------------------------------- 4. números de página
_NUMERO_PAGINA = re.compile(r"^\s*\d{1,4}(\s+\d{1,4})?\s*$")


def remover_numeros_pagina(texto: str) -> str:
    return "\n".join(l for l in texto.split("\n") if not _NUMERO_PAGINA.match(l))


# ----------------------------------------------------------------- 5. sumário
_SUMARIO = re.compile(r"\.{5,}\s*\d+\s*$")


def remover_sumario(texto: str) -> str:
    return "\n".join(l for l in texto.split("\n") if not _SUMARIO.search(l))


# ------------------------------------------------------------- 6. hifenização
# letra + hífen (com ou sem espaço antes/depois) + quebra de linha + letra minúscula
_HIFEN_QUEBRA = re.compile(r"(\w) ?-[ ]*\n[ ]*([a-zà-ÿ])")


# Letra capitular (a primeira letra grande do capítulo) vem sozinha na linha,
# sem espaço depois: "E\nvidências" -> "Evidências". Com espaço ("A \nerosão")
# é a palavra "A" e fica separada.
_CAPITULAR = re.compile(r"(^|\n)([A-ZÀ-Ú])\n([a-zà-ÿ])")


# Capitular com espaço perdido no PDF: "T odos", "T ambém", "T ente" -> "Todos"...
# Só consoante: A, E, O (e É, À) são palavras em português ("A erosão", "E depois")
# e ficam como estão. E não junta se o pedaço seguinte já é uma palavra curta comum
# ("X de", "P ou"), para não colar duas palavras de verdade.
_CAPITULAR_ESPACO = re.compile(r"(?<![\wÀ-ÿ])([B-DF-HJ-NP-TV-Z]) ([a-zà-ÿ]{2,})")
_PALAVRAS_CURTAS = {"de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "ou", "que", "se",
                    "um", "uma", "com", "por", "para", "ao", "aos", "as", "os", "é"}


def _juntar_capitular_espaco(m: re.Match) -> str:
    letra, resto = m.group(1), m.group(2)
    return m.group(0) if resto in _PALAVRAS_CURTAS else letra + resto


def juntar_hifenizacao(texto: str) -> str:
    texto = _CAPITULAR.sub(r"\1\2\3", texto)
    texto = _CAPITULAR_ESPACO.sub(_juntar_capitular_espaco, texto)
    return _HIFEN_QUEBRA.sub(r"\1\2", texto)


# ------------------------------------------------------------ 7. juntar linhas
_INICIO_LISTA = re.compile(r"^\s*(-|\d{1,2}[.)]|[a-z][.)])\s")


def juntar_linhas(texto: str) -> str:
    """Junta a linha seguinte quando ela continua a frase.

    Junta quando a próxima linha começa com letra minúscula ou com pontuação
    (",", ".", ")"), ou quando a linha anterior está "cheia" (60+ caracteres)
    e não terminou a frase. Item de lista e linha em branco nunca são juntados.
    """
    saida: list[str] = []
    for linha in texto.split("\n"):
        atual = linha.strip()
        if saida and atual and saida[-1].strip():
            anterior = saida[-1].rstrip()
            continua = re.match(r"^[a-zà-ÿ]", atual) and not _INICIO_LISTA.match(atual)
            pontuacao = re.match(r"^[,.;:)\]]", atual)
            if pontuacao:
                saida[-1] = anterior + atual
                continue
            # linha "cheia" (60+ caracteres) sem pontuação final quebrou por falta de espaço:
            # "o United\nNations Office" -> "o United Nations Office"
            linha_cheia = ((len(anterior) >= 60 or anterior.endswith(",")) and not re.search(r"[.!?:;]$", anterior)
                           and not _INICIO_LISTA.match(atual) and re.match(r"^[A-ZÀ-Úa-zà-ÿ(]", atual))
            if linha_cheia:
                saida[-1] = anterior + " " + atual
                continue
            if continua and not re.search(r"[.!?]$", anterior):
                saida[-1] = anterior + " " + atual
                continue
        saida.append(atual)
    return "\n".join(saida)


# ------------------------------------------------- 8. referências bibliográficas
# Usada quando as referências dividem a página com texto útil (Mapeamento),
# e por isso não dá para excluir a página inteira na seleção de páginas.
# Cada citação ABNT ocupa várias linhas: "IPCC. Climate Change 2022: Impacts..."
# / "Vulnerability. Contribution of..." / "University Press, 2022." A regra
# reconhece o BLOCO de citações pelo formato, com ou sem o título.
_TITULO_REFERENCIAS = re.compile(r"^\s*REFER[ÊE]NCIAS(\s+BIBLIOGR[ÁA]FICAS)?\s*:?\s*$", re.I)
# início de citação: SOBRENOME, X. / ENTIDADE. / SGB/CPRM.
_INICIO_CITACAO = re.compile(r"^\s*[A-ZÀ-Ú][A-ZÀ-Ú'/\-]+(\s+(DE|DA|DO|DOS|DAS|[A-ZÀ-Ú'/\-]+))*[,.]\s")
# outros sinais de citação: termina no ano, "Disponível em", "In:", "et al."
_SINAL_CITACAO = re.compile(r"(\b(1[89]|20)\d{2}[a-z]?\.\s*$|Disponível em|Acesso em|\bIn:|\bet al\.|\(Ed\.\)|\bv\. \d|\bn\. \d)", re.I)
_TITULO_MAIUSCULO = re.compile(r"^[^a-zà-ÿ]*[A-ZÀ-Ú]{3,}[^a-zà-ÿ]*$")


def _e_citacao(linha: str) -> bool:
    return bool(_INICIO_CITACAO.match(linha) or _SINAL_CITACAO.search(linha))


def remover_referencias(texto: str) -> tuple[str, int]:
    """Remove blocos de citações bibliográficas. Devolve (texto, linhas removidas).

    Um bloco começa numa linha com cara de citação e continua enquanto as linhas
    forem citação ou pedaço de citação (linha que não fecha frase). Termina no
    primeiro título em maiúsculas ou na primeira frase de texto normal. Só é
    removido se tiver pelo menos 2 inícios de citação: uma frase comum que
    comece com "BRASIL." não basta.
    """
    linhas = [l for l in texto.split("\n") if not _TITULO_REFERENCIAS.match(l)]
    remover: set[int] = set()
    i = 0
    while i < len(linhas):
        if not _e_citacao(linhas[i]) or _TITULO_MAIUSCULO.match(linhas[i]):
            i += 1
            continue
        j, inicios, anterior_fechou = i, 0, False
        while j < len(linhas):
            l = linhas[j].strip()
            if not l:
                j += 1
                continue
            if _TITULO_MAIUSCULO.match(l):
                break
            if _e_citacao(l):
                inicios += bool(_INICIO_CITACAO.match(l))
            elif anterior_fechou or re.search(r"[.!?]$", l):
                # depois de uma citação fechada ("..., 2018."), linha que não é
                # citação já é texto do livro; frase fechada também encerra o bloco
                break
            anterior_fechou = bool(re.search(r"[.!?]$", l))
            j += 1
        if inicios >= 2:
            remover.update(range(i, j))
        i = max(j, i + 1)
    saida = [l for k, l in enumerate(linhas) if k not in remover]
    removidas = sum(1 for k in remover if linhas[k].strip())
    return "\n".join(saida), removidas


# ------------------------------------------------------------ 9. espaços
def normalizar_espacos(texto: str) -> str:
    texto = re.sub(r"[ ]{2,}", " ", texto)
    texto = "\n".join(l.strip() for l in texto.split("\n"))
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


# ------------------------------------------------------------ orquestração
def _novo_trecho(trecho, texto: str):
    # funciona com dataclass ou namedtuple, sem depender da classe exata
    return type(trecho)(fonte=trecho.fonte, tipo=trecho.tipo, pagina=trecho.pagina, texto=texto)


def limpar_corpus(trechos: Iterable) -> tuple[list, dict]:
    """Limpa todos os trechos. Devolve (trechos_limpos, estatisticas).

    As estatísticas servem para o relatório: caracteres antes e depois,
    trechos descartados por ficarem vazios e linhas repetidas por documento.
    """
    trechos = list(trechos)
    estat = {"trechos_entrada": len(trechos), "trechos_vazios_descartados": 0,
             "caracteres_antes": 0, "caracteres_depois": 0, "repetidas_por_documento": {},
             "linhas_de_referencia_removidas": 0}

    # passo de documento: as linhas repetidas só fazem sentido comparando páginas do mesmo PDF
    pre = {}
    por_fonte: dict[str, list[str]] = {}
    for i, t in enumerate(trechos):
        estat["caracteres_antes"] += len(t.texto)
        texto = remover_boilerplate(normalizar_caracteres(t.texto))
        pre[i] = texto
        if t.tipo == "pdf":
            por_fonte.setdefault(t.fonte, []).append(texto)
    repetidas = {fonte: linhas_repetidas(paginas) for fonte, paginas in por_fonte.items()}
    estat["repetidas_por_documento"] = {f: len(r) for f, r in repetidas.items() if r}

    limpos = []
    for i, t in enumerate(trechos):
        texto = remover_repetidas(pre[i], repetidas.get(t.fonte, set()))
        texto = remover_numeros_pagina(texto)
        texto = remover_sumario(texto)
        texto = juntar_hifenizacao(texto)
        texto = juntar_linhas(texto)
        texto, n_ref = remover_referencias(texto)
        estat["linhas_de_referencia_removidas"] += n_ref
        texto = normalizar_espacos(texto)
        if not texto:
            estat["trechos_vazios_descartados"] += 1
            continue
        estat["caracteres_depois"] += len(texto)
        limpos.append(_novo_trecho(t, texto))
    return limpos, estat
