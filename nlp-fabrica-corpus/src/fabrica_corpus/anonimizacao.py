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

Limites conhecidos (registrar no relatório):
 - nome isolado de uma palavra só, sem ter aparecido completo antes, não é
   mascarado (evita falsos positivos como "Secretário", "CPF");
 - sobrenome de autor em citação ("Jacobi, 2018") não é dado pessoal e fica.
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


# ---------------------------------------------------------------- orquestração
def anonimizar_texto(texto: str, vocab: set[str] | None = None) -> tuple[str, dict]:
    """Devolve (texto anonimizado, contagem por tipo)."""
    vocab = vocabulario_minusculas(texto) if vocab is None else vocab
    contagem = {}
    texto, contagem["cpf"] = _mascarar_cpf(texto)
    texto, contagem["email"] = _mascarar_email(texto)
    texto, contagem["telefone"] = _mascarar_telefone(texto)
    nomes = encontrar_nomes(texto, vocab)
    texto, contagem["nome"] = _mascarar_nomes(texto, nomes, vocab)
    return texto, contagem


def anonimizar_corpus(trechos: Iterable) -> tuple[list, dict]:
    """Anonimiza todos os trechos. Devolve (trechos, estatísticas por tipo)."""
    trechos = list(trechos)
    vocab = vocabulario_minusculas(t.texto for t in trechos)   # vocabulário do corpus inteiro
    total = {"cpf": 0, "email": 0, "telefone": 0, "nome": 0}
    saida = []
    for t in trechos:
        texto, contagem = anonimizar_texto(t.texto, vocab)
        for tipo, k in contagem.items():
            total[tipo] += k
        saida.append(type(t)(fonte=t.fonte, tipo=t.tipo, pagina=t.pagina, texto=texto))
    return saida, total
