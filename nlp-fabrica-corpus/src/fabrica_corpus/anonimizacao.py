"""Etapa 5 da Fábrica de Corpus: anonimização.

Mascara CPF, e-mail, telefone e nomes de pessoas antes de gerar qualquer corpus.
Marcações usadas: [CPF], [EMAIL], [TELEFONE] e [NOME].

Preservados (decisão do grupo, 13/11/2026): números de emergência (190, 192,
193, 199, 40199), o 156 e os contatos de órgãos públicos (e-mails .gov.br e os
telefones listados em CONTATOS_PUBLICOS). São serviços de que o cidadão
precisa numa enchente, não dados de pessoas.

Como os nomes são encontrados (em camadas, porque nenhuma sozinha basta):
 1. spaCy (pt_core_news_md): entidades PER com 2 palavras ou mais;
 2. contexto de rótulo: "Nome: Fulano de Tal" (tabelas do DOCX);
 3. repetição: um nome já encontrado é mascarado em qualquer forma em que
    reapareça no mesmo texto: todo em maiúsculas ("JOAQUIM PEREIRA LINS") ou só
    o primeiro nome ("Mariana também relatou").

Filtro contra falsos positivos (o modelo marca "Chuvas Intensas" e "Marco de
Ação de Hyogo" como pessoa): palavra que aparece em minúscula em algum lugar
do corpus é palavra comum, não nome. Entidade cujo primeiro nome ou a maioria
das palavras é comum é descartada, e o primeiro nome só é mascarado sozinho
quando nunca aparece em minúscula.

Sobrenomes de autores em citações (decisão de 17/11/2026), contados à parte em
"citacao": "(Sulaiman, Moura & Nogueira, 2021)" -> "([NOME], [NOME] & [NOME], 2021)"
e as citações narrativas "Santos et al.,(2007)" -> "[NOME] et al.,(2007)" e
"Hermelin (2005)" / "Gramani e Massad (2022)" -> "[NOME] (2005)" / "[NOME] e [NOME] (2022)". Ficam o ano,
"et al.", "Jr.", "Filho", "Apud", a pontuação e os autores institucionais ("Brasil",
"Brasil-Japão", siglas e a lista _NAO_PESSOA). Parêntese que não tem só autores e
anos ("(entre 2010 e 2020)", "(Lei nº 12.608, 2012)") não é tocado.

Limites conhecidos (registrar no relatório):
 - nome isolado de uma palavra só, sem ter aparecido completo antes, não é
   mascarado (evita falsos positivos como "Secretário", "CPF");
 - autor institucional por extenso que não está em _NAO_PESSOA (ex.: "(Cemaden
   Educação, 2020)") é mascarado como se fosse pessoa.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

# ---------------------------------------------------------------- exceções
CONTATOS_PUBLICOS = {
    "(11) 3124-5157",   # Defesa Civil da Prefeitura de São Paulo
    "(61) 3213-8510",   # Ministério da Saúde - SVS
}
_DOMINIO_PUBLICO = re.compile(r"\.gov\.br$|\.leg\.br$|\.jus\.br$", re.I)

# Entidades que o modelo às vezes marca como pessoa e que nunca são pessoas.
_NAO_PESSOA = {
    "cpf", "cnpj", "rg", "cep", "secretário", "secretária", "presidente", "contato",
    "defesa civil", "corpo de bombeiros", "polícia militar", "ministério da saúde",
    "ministério das cidades", "radar cidadão", "samu",
}
_TRATAMENTOS = re.compile(r"^(dona|dom|sr\.?|sra\.?|srta\.?|dr\.?|dra\.?|seu|sra|senhor|senhora)\s+", re.I)

# ---------------------------------------------------------------- padrões
_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
# telefone brasileiro com DDD: (20) 99999-0001, +55 20 98888-0002, (23) 3000-0003, 11 3124-5157
_TELEFONE = re.compile(r"(?<!\w)(\+55\s?)?\(?\d{2}\)?[\s.-]?9?\d{4}[\s.-]?\d{4}(?!\w)")
_ROTULO_NOME = re.compile(r"(Nome\s*:\s*)([A-ZÀ-Ú][\wÀ-ÿ'-]+(?:\s+(?:d[aeo]s?|e|[A-ZÀ-Ú][\wÀ-ÿ'-]+))+)")


def _mascarar_cpf(texto: str) -> tuple[str, int]:
    return _CPF.subn("[CPF]", texto)


def _mascarar_email(texto: str) -> tuple[str, int]:
    n = 0

    def troca(m):
        nonlocal n
        dominio = m.group(0).split("@")[1]
        if _DOMINIO_PUBLICO.search(dominio):
            return m.group(0)
        n += 1
        return "[EMAIL]"
    return _EMAIL.sub(troca, texto), n


def _mascarar_telefone(texto: str) -> tuple[str, int]:
    n = 0

    def troca(m):
        nonlocal n
        if m.group(0).strip() in CONTATOS_PUBLICOS:
            return m.group(0)
        n += 1
        return "[TELEFONE]"
    return _TELEFONE.sub(troca, texto), n


# ---------------------------------------------------------------- nomes
@lru_cache(maxsize=1)
def _nlp():
    import spacy
    try:
        return spacy.load("pt_core_news_md", disable=["parser", "lemmatizer"])
    except OSError as erro:
        raise RuntimeError(
            "Modelo do spaCy não instalado. Rode: python -m spacy download pt_core_news_md"
        ) from erro


_PREFIXOS_DE_LUGAR = {"santo", "santa", "são", "rio", "vila", "porto", "monte", "serra", "nossa", "ponte", "lagoa"}
_CONECTORES = {"de", "da", "do", "dos", "das", "e"}


def vocabulario_minusculas(textos) -> set[str]:
    """Palavras que aparecem escritas em minúscula em algum lugar do texto.

    Nome de pessoa quase nunca aparece em minúscula ("leonardo", "vasconcelos");
    palavra comum aparece ("chuvas", "deslizamentos", "transtorno"). É o que
    separa "Fernando Rocha Nogueira" de "Chuvas Intensas" sem lista de nomes.
    """
    if isinstance(textos, str):
        textos = [textos]
    vocab = set()
    for t in textos:
        # e-mails e sites têm nomes em minúscula ("mariana.toledo@..."): fora do vocabulário
        t = _EMAIL.sub(" ", t)
        t = re.sub(r"(https?://|www\.)\S+", " ", t)
        vocab.update(re.findall(r"(?<![\wÀ-ÿ.@])[a-zà-ÿ][a-zà-ÿ\-]+(?![\w@])", t))
    return vocab


def _limpar_nome(nome: str, vocab: set[str] = frozenset()) -> str | None:
    nome = _TRATAMENTOS.sub("", nome.strip(" .,;:-–"))
    palavras = nome.split()
    # o modelo às vezes cola um título em maiúsculas no nome:
    # "HIDROLÓGICOS Leonardo Andrade de Souza" -> "Leonardo Andrade de Souza"
    if any(p[:1].isupper() and not p.isupper() for p in palavras):
        while palavras and len(palavras[0]) >= 3 and palavras[0].isupper():
            palavras.pop(0)
        while palavras and len(palavras[-1]) >= 3 and palavras[-1].isupper():
            palavras.pop()
    else:
        return None                     # tudo em maiúsculas: título, não nome
    # palavra comum colada no fim: "Leonardo ... Varallo Rastejos" -> sem "Rastejos"
    while len(palavras) > 2 and palavras[-1].lower() in vocab:
        palavras.pop()
    nome = " ".join(palavras)
    principais = [p for p in palavras if p.lower() not in _CONECTORES]
    if len(principais) < 2 or any(ch.isdigit() for ch in nome) or "[" in nome:
        return None
    if nome.lower() in _NAO_PESSOA:
        return None
    if not all(p[0].isupper() or p.lower() in _CONECTORES for p in palavras):
        return None
    if re.fullmatch(r"[A-ZÀ-Ú]\.?", principais[0]):            # "V. Uma"
        return None
    if len({p.lower() for p in principais}) < len(principais):  # "Ameaça Ameaça"
        return None
    primeiro = principais[0].lower()
    if primeiro in vocab or primeiro in _PREFIXOS_DE_LUGAR:      # "Chuvas Intensas", "Santo António"
        return None
    comuns = sum(1 for p in principais if p.lower() in vocab)
    if comuns * 2 >= len(principais):                           # maioria palavra comum
        return None
    return nome


def encontrar_nomes(texto: str, vocab: set[str] | None = None) -> set[str]:
    """Nomes completos de pessoas no texto (spaCy + rótulo "Nome:").

    vocab: palavras vistas em minúscula; por padrão, as do próprio texto.
    Passar o vocabulário do corpus inteiro deixa o filtro mais seguro.
    """
    vocab = vocabulario_minusculas(texto) if vocab is None else vocab
    nomes = set()
    for ent in _nlp()(texto).ents:
        if ent.label_ == "PER":
            nome = _limpar_nome(ent.text, vocab)
            if nome:
                nomes.add(nome)
    for m in _ROTULO_NOME.finditer(texto):
        nome = _limpar_nome(m.group(2), vocab)
        if nome:
            nomes.add(nome)
    return nomes


def _mascarar_nomes(texto: str, nomes: set[str], vocab: set[str] = frozenset()) -> tuple[str, int]:
    if not nomes:
        return texto, 0
    n = 0
    # nomes completos primeiro (os mais longos antes), em qualquer caixa
    for nome in sorted(nomes, key=len, reverse=True):
        padrao = re.compile(r"(?<![\wÀ-ÿ])" + re.escape(nome) + r"(?![\wÀ-ÿ])", re.I)
        texto, k = padrao.subn("[NOME]", texto)
        n += k
    # primeiro nome sozinho, só com inicial maiúscula ("Mariana também relatou")
    # só se o primeiro nome nunca aparece como palavra comum (evita "Marco", "Santo")
    primeiros = {nome.split()[0] for nome in nomes
                 if len(nome.split()[0]) >= 3 and nome.split()[0].lower() not in vocab
                 and nome.split()[0].lower() not in _PREFIXOS_DE_LUGAR}
    for primeiro in primeiros:
        padrao = re.compile(r"(?<![\wÀ-ÿ\[])" + re.escape(primeiro) + r"(?![\wÀ-ÿ])")
        texto, k = padrao.subn("[NOME]", texto)
        n += k
    return texto, n


# ---------------------------------------------------------------- citações de autores
_ANO = r"(?:1[5-9]|20)\d{2}[a-z]?"
_ANOS = rf"{_ANO}(?:\s*,\s*{_ANO})*"
_PALAVRA = r"[A-ZÀ-Ú][\wÀ-ÿ'’-]*"
# sequência de palavras com inicial maiúscula, que pode ter "de/da/do/dos/das" no meio
_AUTOR = re.compile(rf"\[NOME\]|{_PALAVRA}(?:\s+(?:d[aeo]s?\s+)?{_PALAVRA})*")
_PARENTESE_COM_ANO = re.compile(rf"\(([^()]*?\b{_ANO})\s*\)")
_SO_SEPARADORES = re.compile(r"(?:[\s,;&.]|\be\b|\bet\s+al\b)*")
_CITACAO_NARRATIVA = re.compile(rf"\b({_PALAVRA})(\s+et\s+al\.?\s*,?\s*\(\s*{_ANOS}\s*\))")
# autor seguinte da mesma lista: "Santos et al.,(2007), Sulaiman e Jacobi (2018)"; no
# Mapeamento p. 9 a página acaba em "Sulaiman" e a lista continua na p. 10
_CONTINUACAO_NARRATIVA = re.compile(rf"(et\s+al\.?\s*,?\s*\(\s*{_ANOS}\s*\)\s*,\s+)({_PALAVRA})(?=[ \t]*(?:\n|$)|\s+e\s|\s*,)")
# narrativa sem "et al.": "Hermelin (2005)", "Gramani e Massad (2022)", "Fornasari Filho (2018)"
_AUTOR_NARRATIVO = rf"{_PALAVRA}(?:\s+(?:Jr\.?|Júnior|Filho|Neto|Sobrinho))?"
_CITACAO_NARRATIVA_SIMPLES = re.compile(
    rf"(?<![\wÀ-ÿ\[])({_AUTOR_NARRATIVO}(?:\s*(?:,|\be\b|&)\s*{_AUTOR_NARRATIVO})*)(\s+\(\s*{_ANOS}\s*\))")
_SUFIXOS = {"jr", "jr.", "júnior", "junior", "filho", "neto", "sobrinho"}
# autores institucionais que não são sigla em maiúsculas (siglas como IPCC e ANA já ficam)
_INSTITUCIONAIS = {"brasil", "brasil-japão", "apud", "gides", "maceió", "cemaden", "inmet"}


def _mascarar_autor(m: re.Match) -> tuple[str, int]:
    """Uma sequência de palavras de um autor -> "[NOME]" (mantém Apud, Jr., Filho e instituições)."""
    palavras = m.group(0).split()
    inicio = ["Apud"] if palavras[0] == "Apud" else []
    palavras = palavras[len(inicio):]
    fim = []
    while palavras and palavras[-1].lower() in _SUFIXOS:
        fim.insert(0, palavras.pop())
    nucleo = " ".join(palavras)
    if (not nucleo or nucleo == "[NOME]" or nucleo.lower() in _INSTITUCIONAIS or nucleo.lower() in _NAO_PESSOA
            or nucleo.isupper()):
        return m.group(0), 0
    return " ".join(inicio + ["[NOME]"] + fim), 1


def _mascarar_citacoes(texto: str) -> tuple[str, int]:
    """Mascara sobrenomes de autores em citações autor-ano. Devolve (texto, autores mascarados)."""
    total = 0

    def parentese(m: re.Match) -> str:
        nonlocal total
        conteudo = m.group(1)
        sem_anos = re.sub(_ANOS, " ", conteudo)
        # só autores, separadores, "et al." e anos: senão não é citação ("entre 2010 e 2020")
        if not _AUTOR.search(sem_anos) or not _SO_SEPARADORES.fullmatch(_AUTOR.sub(" ", sem_anos)):
            return m.group(0)
        partes, n = [], 0
        ultimo = 0
        for a in _AUTOR.finditer(conteudo):
            novo, k = _mascarar_autor(a)
            partes.append(conteudo[ultimo:a.start()] + novo)
            ultimo, n = a.end(), n + k
        total += n
        return "(" + "".join(partes) + conteudo[ultimo:] + ")"

    def narrativa(m: re.Match) -> str:
        nonlocal total
        novo, k = _mascarar_autor(re.match(r".+", m.group(1)))
        total += k
        return novo + m.group(2)

    def continuacao(m: re.Match) -> str:
        nonlocal total
        novo, k = _mascarar_autor(re.match(r".+", m.group(2)))
        total += k
        return m.group(1) + novo

    def narrativa_simples(m: re.Match) -> str:
        nonlocal total
        autores, partes, ultimo = m.group(1), [], 0
        for a in re.finditer(_AUTOR_NARRATIVO, autores):
            novo, k = _mascarar_autor(a)
            partes.append(autores[ultimo:a.start()] + novo)
            ultimo, total = a.end(), total + k
        return "".join(partes) + autores[ultimo:] + m.group(2)

    texto = _PARENTESE_COM_ANO.sub(parentese, texto)
    texto = _CITACAO_NARRATIVA.sub(narrativa, texto)
    texto = _CONTINUACAO_NARRATIVA.sub(continuacao, texto)
    texto = _CITACAO_NARRATIVA_SIMPLES.sub(narrativa_simples, texto)
    return texto, total


# ---------------------------------------------------------------- orquestração
def anonimizar_texto(texto: str, vocab: set[str] | None = None) -> tuple[str, dict]:
    """Devolve (texto anonimizado, contagem por tipo)."""
    vocab = vocabulario_minusculas(texto) if vocab is None else vocab
    contagem = {}
    texto, contagem["cpf"] = _mascarar_cpf(texto)
    texto, contagem["email"] = _mascarar_email(texto)
    texto, contagem["telefone"] = _mascarar_telefone(texto)
    texto, contagem["citacao"] = _mascarar_citacoes(texto)
    nomes = encontrar_nomes(texto, vocab)
    texto, contagem["nome"] = _mascarar_nomes(texto, nomes, vocab)
    return texto, contagem


def anonimizar_corpus(trechos: Iterable) -> tuple[list, dict]:
    """Anonimiza todos os trechos. Devolve (trechos, estatísticas por tipo)."""
    trechos = list(trechos)
    vocab = vocabulario_minusculas(t.texto for t in trechos)   # vocabulário do corpus inteiro
    total = {"cpf": 0, "email": 0, "telefone": 0, "citacao": 0, "nome": 0}
    saida = []
    for t in trechos:
        texto, contagem = anonimizar_texto(t.texto, vocab)
        for tipo, k in contagem.items():
            total[tipo] += k
        saida.append(type(t)(fonte=t.fonte, tipo=t.tipo, pagina=t.pagina, texto=texto))
    return saida, total
