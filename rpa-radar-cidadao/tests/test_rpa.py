import csv
import json
from pathlib import Path

import pytest

from radar_rpa.cli import avaliar, processar
from radar_rpa.core import classificar, criar_modelo, proteger_dados


@pytest.fixture(scope="module")
def modelo():
    return criar_modelo()


def criar_csv(path, linhas):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "relato"])
        w.writerows(linhas)


def test_treino_e_classificacao(modelo):
    assert classificar("Rua inundada por enchente", modelo, 0).categoria == "alagamento"


def test_sinal_urgente_prevalece(modelo):
    r = classificar("Socorro estou preso na enchente", modelo)
    assert r.status == "encaminhar_imediatamente"
    assert "nao aciona" in r.orientacao.lower()


def test_entrada_vazia_revisao(modelo):
    assert classificar("", modelo).status == "revisao"


def test_anonimizacao():
    txt = proteger_dados("email: exemplo@teste.com CPF 123.456.789-09 telefone (11) 99999-8888")
    assert "exemplo@teste.com" not in txt
    assert "123.456.789-09" not in txt
    assert "99999-8888" not in txt
    assert "[CPF]" in txt and "[EMAIL]" in txt and "[TELEFONE]" in txt


def test_falha_arquivo_ausente(tmp_path):
    out = processar(tmp_path / "faltando.csv", tmp_path / "saida")
    assert out["erros"] and out["processados"] == 0
    assert (tmp_path / "saida" / "execucao.log").exists()


def test_falha_cabecalho(tmp_path):
    entrada = tmp_path / "ruim.csv"
    entrada.write_text("coluna_errada\nabc\n", encoding="utf-8")
    out = processar(entrada, tmp_path / "saida")
    assert out["erros"]


def test_linha_invalida_nao_aborta(tmp_path):
    entrada = tmp_path / "a.csv"
    criar_csv(entrada, [("a", ""), ("b", "Rua inundada")])
    out = processar(entrada, tmp_path / "saida")
    assert out["total_linhas"] == 2 and out["invalidos"] == 1 and out["processados"] == 1


def test_idempotencia(tmp_path):
    entrada = tmp_path / "a.csv"
    criar_csv(entrada, [("a", "Rua inundada")])
    destino = tmp_path / "saida"
    primeiro = processar(entrada, destino)
    segundo = processar(entrada, destino)
    assert primeiro["processados"] == 1 and segundo["duplicados"] == 1
    with (destino / "resultados.csv").open(encoding="utf-8-sig", newline="") as f:
        assert len(list(csv.DictReader(f, delimiter=";"))) == 1


def test_saida_sem_dados_pessoais(tmp_path):
    entrada = tmp_path / "a.csv"
    criar_csv(entrada, [("a", "A rua alagou. email teste@example.org CPF 123.456.789-09")])
    destino = tmp_path / "saida"
    processar(entrada, destino)
    txt = (destino / "resultados.csv").read_text(encoding="utf-8-sig")
    assert "teste@example.org" not in txt and "123.456.789-09" not in txt
    assert "[EMAIL]" in txt and "[CPF]" in txt


def test_csv_formula_escapada(tmp_path):
    entrada = tmp_path / "a.csv"
    criar_csv(entrada, [("=HYPERLINK(\"x\")", "Rua alagada")])
    destino = tmp_path / "saida"
    processar(entrada, destino)
    with (destino / "resultados.csv").open(encoding="utf-8-sig", newline="") as f:
        dados = list(csv.DictReader(f, delimiter=";"))
    assert dados[0]["id"].startswith("'=")


def test_amostra_metrica(tmp_path):
    entrada = tmp_path / "rotulos.csv"
    entrada.write_text("texto;classe_esperada\nRua alagada;alagamento\n", encoding="utf-8")
    resultado = avaliar(entrada, tmp_path / "saida")
    assert resultado["amostra"] == 1
    assert resultado["acertos"] + resultado["erros"] == 1
