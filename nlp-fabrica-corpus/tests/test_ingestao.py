"""Testes da ingestão e extração (etapas 1 e 2)."""

import logging
from pathlib import Path

from bs4 import BeautifulSoup

from fabrica_corpus.ingestao import (
    carregar_selecao,
    extrair_arquivo,
    extrair_texto_colado,
    ingerir_pasta,
)

DADOS = Path(__file__).resolve().parents[1] / "dados"
ENTRADA = DADOS / "entrada"
ENTRADA_IA = DADOS / "entrada_ia_generativa"
TESTE = DADOS / "teste"


# 1. TXT de teste
def test_txt_de_teste():
    trechos = extrair_arquivo(TESTE / "teste_dados_ficticios.txt")
    assert len(trechos) == 1
    t = trechos[0]
    assert t.fonte == "teste_dados_ficticios.txt"
    assert t.tipo == "txt"
    assert t.pagina is None
    assert "Mariana Toledo Vasconcelos" in t.texto
    assert "40199" in t.texto
    assert "Ministério da Saúde" in t.texto  # acentos preservados
    assert "Luíza Andrade Siqueira – Presidente da associação" in t.texto


# 2. DOCX de teste, com parágrafos e tabela
def test_docx_de_teste_com_tabela():
    trechos = extrair_arquivo(TESTE / "teste_dados_ficticios.docx")
    assert len(trechos) == 1
    t = trechos[0]
    assert t.fonte == "teste_dados_ficticios.docx"
    assert t.tipo == "docx"
    assert "Secretário: Rafael Monteiro Dantas" in t.texto  # parágrafos
    assert t.texto.count("987.654.321-99") == 2  # no texto e na tabela
    # tabela no formato "cabeçalho: valor" (opção B)
    assert (
        "Nome: Mariana Toledo Vasconcelos; CPF: 123.456.789-10; "
        "E-mail: mariana.toledo@example.com; Telefone: (20) 99999-0001"
    ) in t.texto


# 3. Texto colado
def test_texto_colado():
    texto = "Moro perto do córrego e a rua alagou. Ligar para 199?"
    trechos = extrair_texto_colado(texto)
    assert len(trechos) == 1
    assert trechos[0].fonte == "texto_colado"
    assert trechos[0].tipo == "colado"
    assert trechos[0].texto == texto
    assert extrair_texto_colado("   ") == []


# 4. HTML: sem script, style, noscript, nav, header e footer
def test_html_enchentes():
    caminho = ENTRADA / "ms_2026_enchentes.html"
    trechos = extrair_arquivo(caminho)
    assert len(trechos) == 1
    texto = trechos[0].texto
    assert trechos[0].fonte == "ms_2026_enchentes.html"
    assert texto.strip()

    original = BeautifulSoup(caminho.read_bytes(), "html.parser")
    removidos = [
        tag.get_text(" ", strip=True)
        for tag in original(["script", "style", "noscript", "nav", "header", "footer"])
    ]
    # Cada bloco removido com texto próprio (40+ caracteres) não pode aparecer na saída
    amostras = [r[:40] for r in removidos if len(r) >= 40]
    assert amostras, "o HTML deveria ter conteúdo nessas tags para o teste ser útil"
    for amostra in amostras:
        assert amostra not in " ".join(texto.split())


# 5. Seleção do Manual: só as 17 páginas escolhidas, sem a página 3
def test_selecao_manual():
    nome = "mi_2003_manual_desastres_naturais.pdf"
    regra = carregar_selecao(ENTRADA_IA)[nome]
    trechos = extrair_arquivo(ENTRADA_IA / nome, regra)
    paginas = [t.pagina for t in trechos]
    esperadas = [40, 41, 48, 49, 50, 51, 52] + list(range(108, 118))
    assert paginas == esperadas
    assert len(trechos) == 17
    assert 3 not in paginas


# 6. Seleção do Guia: todas as páginas menos a 2
def test_selecao_guia():
    nome = "mdr_2021_guia_alertas_desastres.pdf"
    regra = carregar_selecao(ENTRADA_IA)[nome]
    trechos = extrair_arquivo(ENTRADA_IA / nome, regra)
    paginas = [t.pagina for t in trechos]
    assert len(trechos) == 45
    assert 2 not in paginas


# 7. Pasta como parâmetro
def test_pasta_como_parametro():
    fontes_nlp = {t.fonte for t in ingerir_pasta(ENTRADA)}
    assert fontes_nlp == {
        "mcid_2024_periferia_sem_risco.pdf",
        "mcid_2026_mapeamento_riscos.pdf",
        "ms_2017_cartilha_alerta_chuvas.pdf",
        "ms_2025_plano_contingencia_chuvas.pdf",
        "ms_2026_enchentes.html",
    }

    fontes_ia = {t.fonte for t in ingerir_pasta(ENTRADA_IA)}
    assert fontes_ia == {
        "mdr_2021_guia_alertas_desastres.pdf",
        "mi_2003_manual_desastres_naturais.pdf",
        "pmsp_2024_chuvas_excessivas.pdf",
        "cgesp_2026_dicas_alagamentos.docx",
    }  # selecao_paginas.json não conta como documento

    fontes_teste = {t.fonte for t in ingerir_pasta(TESTE)}
    assert fontes_teste == {"teste_dados_ficticios.txt", "teste_dados_ficticios.docx"}  # sem gerar_docx.py


# 8. Formato não aceito: pulado e registrado no log, sem interromper
def test_formato_nao_aceito(tmp_path, caplog):
    (tmp_path / "planilha.xlsx").write_bytes(b"conteudo qualquer")
    (tmp_path / "relato.txt").write_text("Rua alagada na Vila Esperança.", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="fabrica_corpus.ingestao"):
        trechos = ingerir_pasta(tmp_path)

    assert [t.fonte for t in trechos] == ["relato.txt"]
    assert "planilha.xlsx" in caplog.text
