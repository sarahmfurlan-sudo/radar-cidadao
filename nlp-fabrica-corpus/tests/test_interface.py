"""Testes da interface (a lógica, sem abrir o Gradio)."""
import json
from pathlib import Path

import pytest

from fabrica_corpus.interface import arquivos_corpus, exemplos_corpus, processar, resumo_corpus

TESTE = Path(__file__).resolve().parents[1] / "dados" / "teste"
ENTRADA = Path(__file__).resolve().parents[1] / "dados" / "entrada"
contar = lambda t: len(t.split())          # contador simples no lugar do tokenizador do Qwen


def test_processar_docx_txt_e_texto_colado(tmp_path):
    r = processar([str(TESTE / "teste_dados_ficticios.docx"), str(TESTE / "teste_dados_ficticios.txt")],
                  "Moro perto do córrego e a rua alagou. Liguei para o 199.", contar, tmp_path)
    assert "teste_dados_ficticios.docx" in r["extracao"] and "texto_colado" in r["extracao"]
    assert "Primeiro trecho, antes" in r["limpeza"]
    assert "123.456.789-10" not in r["anonimizacao"] and "[NOME]" in r["anonimizacao"]
    linhas = [json.loads(l) for l in Path(r["jsonl"]).read_text(encoding="utf-8").splitlines()]
    assert linhas and list(linhas[0]) == ["text", "fonte", "segmento_id"]
    tudo = " ".join(l["text"] for l in linhas)
    assert "987.654.321-99" not in tudo and "Mariana Toledo" not in tudo and "199" in tudo
    assert {l["fonte"] for l in linhas} == {"teste_dados_ficticios.docx", "teste_dados_ficticios.txt", "texto_colado"}


def test_processar_html_sem_rodape_do_govbr(tmp_path):
    r = processar([str(ENTRADA / "ms_2026_enchentes.html")], "", contar, tmp_path)
    tudo = Path(r["jsonl"]).read_text(encoding="utf-8")
    assert "leptospirose" in tudo and "Responder pesquisa" not in tudo


def test_processar_formato_nao_aceito_e_envio_vazio(tmp_path):
    planilha = tmp_path / "dados.xlsx"
    planilha.write_bytes(b"x")
    r = processar([str(planilha)], "", contar, tmp_path)
    assert "formato não aceito" in r["extracao"] and r["jsonl"] is None
    assert processar(None, "  ", contar)["jsonl"] is None


def test_aba_corpus_finais():
    md = resumo_corpus()
    assert "Recusas válidas:** 11" in md and "corpus_qa.jsonl" in md and "opcional" in md
    ex = exemplos_corpus(semente=1)
    assert ex.count("###") == 3 and ex == exemplos_corpus(semente=1)
    assert all(Path(p).exists() for p in arquivos_corpus())


def test_app_monta_sem_abrir():
    pytest.importorskip("gradio")
    from fabrica_corpus.interface import criar_app
    app = criar_app(contar=contar)
    assert app is not None
