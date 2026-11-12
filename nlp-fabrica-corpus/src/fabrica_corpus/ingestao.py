"""Etapas 1 e 2: ingestão de documentos e extração de texto.

Formatos aceitos: PDF, TXT, DOCX, HTML e texto colado.
Cada trecho extraído guarda o arquivo de origem (campo ``fonte``), que segue
até os corpus JSONL.

Uso principal:
    trechos = ingerir_pasta("dados/entrada")

A pasta é parâmetro: a mesma função lê ``dados/entrada`` (corpus da NLP) e
``dados/entrada_ia_generativa`` (corpus ampliado). Se a pasta tiver um
``selecao_paginas.json``, a seleção de páginas dos PDFs é aplicada.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Extensão do arquivo -> tipo registrado no trecho
EXTENSOES_ACEITAS = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".docx": "docx",
    ".html": "html",
    ".htm": "html",
}

# Arquivos de apoio que podem estar nas pastas de dados e não são documentos.
# São ignorados sem aviso no log.
EXTENSOES_DE_APOIO = {".py", ".json", ".md"}

ARQUIVO_SELECAO = "selecao_paginas.json"

# Tags HTML que não são conteúdo. O resto da sujeira fica para a limpeza.
TAGS_HTML_REMOVIDAS = ("script", "style", "noscript", "nav", "header", "footer")

# Codificações tentadas para TXT, em ordem. latin-1 nunca falha (último recurso).
CODIFICACOES_TXT = ("utf-8-sig", "cp1252", "latin-1")


@dataclass
class Trecho:
    """Um pedaço de texto extraído, com a sua origem."""

    fonte: str  # nome do arquivo de origem (ou "texto_colado")
    tipo: str  # pdf, txt, docx, html ou colado
    pagina: Optional[int]  # página do PDF (a partir de 1); None nos outros formatos
    texto: str

    def para_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Seleção de páginas
# ---------------------------------------------------------------------------

def carregar_selecao(pasta: str | Path) -> dict:
    """Lê o selecao_paginas.json da pasta. Devolve {} se ele não existir."""
    caminho = Path(pasta) / ARQUIVO_SELECAO
    if not caminho.exists():
        return {}
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def paginas_selecionadas(n_paginas: int, regra: Optional[dict]) -> list[int]:
    """Devolve as páginas (a partir de 1) que entram, segundo a regra.

    regra = {"modo": "incluir" | "excluir", "paginas": [[inicio, fim], ...]}
    Sem regra, entram todas as páginas.
    """
    todas = list(range(1, n_paginas + 1))
    if not regra:
        return todas

    marcadas: set[int] = set()
    for inicio, fim in regra["paginas"]:
        marcadas.update(range(inicio, fim + 1))

    fora_do_documento = sorted(p for p in marcadas if p > n_paginas or p < 1)
    if fora_do_documento:
        logger.warning("Seleção cita páginas que não existem no documento: %s", fora_do_documento)

    modo = regra.get("modo")
    if modo == "incluir":
        return [p for p in todas if p in marcadas]
    if modo == "excluir":
        return [p for p in todas if p not in marcadas]
    raise ValueError(f"Modo de seleção desconhecido: {modo!r} (use 'incluir' ou 'excluir')")


# ---------------------------------------------------------------------------
# Leitores por formato
# ---------------------------------------------------------------------------

def _extrair_pdf(caminho: Path, regra: Optional[dict]) -> list[Trecho]:
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    trechos = []
    for numero in paginas_selecionadas(len(leitor.pages), regra):
        texto = leitor.pages[numero - 1].extract_text() or ""
        if not texto.strip():
            logger.info("%s: página %d sem texto extraível, ignorada", caminho.name, numero)
            continue
        trechos.append(Trecho(caminho.name, "pdf", numero, texto))
    return trechos


def _extrair_txt(caminho: Path) -> list[Trecho]:
    dados = caminho.read_bytes()
    for codificacao in CODIFICACOES_TXT:
        try:
            texto = dados.decode(codificacao)
        except UnicodeDecodeError:
            continue
        logger.info("%s: lido como %s", caminho.name, codificacao)
        return [Trecho(caminho.name, "txt", None, texto)]
    raise ValueError("não foi possível decodificar o arquivo")  # inalcançável com latin-1


def _tabela_para_texto(tabela) -> str:
    """Converte uma tabela do DOCX em linhas "cabeçalho: valor; ..." (opção B)."""
    linhas = [[celula.text.strip() for celula in linha.cells] for linha in tabela.rows]
    if not linhas:
        return ""
    if len(linhas) == 1:
        return "; ".join(v for v in linhas[0] if v)

    cabecalho, corpo = linhas[0], linhas[1:]
    saida = []
    for linha in corpo:
        pares = [f"{c}: {v}" if c else v for c, v in zip(cabecalho, linha) if v]
        if pares:
            saida.append("; ".join(pares))
    return "\n".join(saida)


def _extrair_docx(caminho: Path) -> list[Trecho]:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    documento = Document(str(caminho))
    blocos = []
    # iter_inner_content() percorre parágrafos e tabelas na ordem do documento
    for item in documento.iter_inner_content():
        if isinstance(item, Paragraph):
            texto = item.text
        elif isinstance(item, Table):
            texto = _tabela_para_texto(item)
        else:
            continue
        if texto.strip():
            blocos.append(texto)
    return [Trecho(caminho.name, "docx", None, "\n\n".join(blocos))]


def _extrair_html(caminho: Path) -> list[Trecho]:
    from bs4 import BeautifulSoup

    # Passar bytes deixa o BeautifulSoup detectar a codificação (meta charset)
    sopa = BeautifulSoup(caminho.read_bytes(), "html.parser")
    for tag in sopa(TAGS_HTML_REMOVIDAS):
        tag.decompose()
    texto = sopa.get_text("\n")
    return [Trecho(caminho.name, "html", None, texto)]


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def extrair_arquivo(caminho: str | Path, regra_paginas: Optional[dict] = None) -> list[Trecho]:
    """Extrai o texto de um arquivo, de acordo com a extensão.

    regra_paginas: regra de seleção de páginas (só vale para PDF).
    """
    caminho = Path(caminho)
    tipo = EXTENSOES_ACEITAS.get(caminho.suffix.lower())
    if tipo is None:
        raise ValueError(f"formato não aceito: {caminho.suffix or '(sem extensão)'}")
    if regra_paginas and tipo != "pdf":
        logger.warning("%s: seleção de páginas ignorada (só vale para PDF)", caminho.name)

    if tipo == "pdf":
        return _extrair_pdf(caminho, regra_paginas)
    if tipo == "txt":
        return _extrair_txt(caminho)
    if tipo == "docx":
        return _extrair_docx(caminho)
    return _extrair_html(caminho)


def extrair_texto_colado(texto: str, nome: str = "texto_colado") -> list[Trecho]:
    """Recebe o texto colado na interface. Texto vazio não gera trecho."""
    if not texto or not texto.strip():
        return []
    return [Trecho(nome, "colado", None, texto)]


def ingerir_pasta(pasta: str | Path) -> list[Trecho]:
    """Lê todos os documentos aceitos de uma pasta (sem entrar em subpastas).

    Arquivos de formato não aceito ou ilegíveis vão para o log e são pulados;
    a ingestão continua com os demais.
    """
    pasta = Path(pasta)
    selecao = carregar_selecao(pasta)

    arquivos = sorted(p for p in pasta.iterdir() if p.is_file())
    nomes = {p.name for p in arquivos}
    for nome_citado in selecao:
        if nome_citado not in nomes:
            logger.warning("%s cita um arquivo que não está na pasta: %s", ARQUIVO_SELECAO, nome_citado)

    trechos: list[Trecho] = []
    for arquivo in arquivos:
        extensao = arquivo.suffix.lower()
        if arquivo.name.startswith(".") or extensao in EXTENSOES_DE_APOIO:
            continue  # .gitkeep, scripts e o próprio arquivo de seleção
        if extensao not in EXTENSOES_ACEITAS:
            logger.warning("Formato não aceito, arquivo ignorado: %s", arquivo.name)
            continue
        try:
            novos = extrair_arquivo(arquivo, selecao.get(arquivo.name))
        except Exception:
            logger.exception("Erro ao ler %s; arquivo ignorado", arquivo.name)
            continue
        logger.info("%s: %d trecho(s) extraído(s)", arquivo.name, len(novos))
        trechos.extend(novos)
    return trechos
