"""Testes da anonimização, incluindo o gabarito obrigatório com o arquivo de teste.

O arquivo dados/teste/teste_dados_ficticios.txt (e o DOCX gerado dele) só tem
dados pessoais fictícios. O gabarito abaixo lista o que TEM que sumir e o que
TEM que ficar. O teste confere as duas coisas: um teste que só olhasse se
sumiu passaria mesmo se o texto não tivesse chegado à anonimização.
"""
from pathlib import Path

import pytest

from fabrica_corpus.anonimizacao import anonimizar_corpus, anonimizar_texto

PASTA_TESTE = Path(__file__).resolve().parents[1] / "dados" / "teste"

# ------------------------------------------------------------------ gabarito
DEVEM_SUMIR = [
    "123.456.789-10", "987.654.321-99",
    "mariana.toledo@example.com", "joaquim.lins@example.com", "associacao.vilaesperanca@example.com",
    "99999-0001", "98888-0002", "3000-0003",
    "Mariana Toledo Vasconcelos", "Joaquim Pereira Lins", "JOAQUIM PEREIRA LINS",
    "Benedita Arruda", "Luíza Andrade Siqueira", "Rafael Monteiro Dantas",
    "Mariana também",       # primeiro nome sozinho, depois de aparecer completo
]
DEVEM_FICAR = [
    "199", "193", "192", "190", "40199",                 # emergência
    "Defesa Civil", "Corpo de Bombeiros", "SAMU", "Polícia Militar", "Ministério da Saúde",
    "Rua das Palmeiras", "Rua do Córrego", "Vila Esperança",
    "12 de janeiro de 2026", "40 centímetros", "78 anos", "leptospirose",
    "Secretário:", "Presidente da associação",
]
MARCACOES_MINIMAS = {"cpf": 2, "email": 3, "telefone": 3, "nome": 8}


def _confere_gabarito(texto: str, contagem: dict):
    for item in DEVEM_SUMIR:
        assert item not in texto, f"ficou no texto: {item}"
    for item in DEVEM_FICAR:
        assert item in texto, f"sumiu do texto: {item}"
    for tipo, minimo in MARCACOES_MINIMAS.items():
        assert contagem[tipo] >= minimo, f"{tipo}: {contagem[tipo]} < {minimo}"


def test_gabarito_no_txt_de_teste():
    texto = (PASTA_TESTE / "teste_dados_ficticios.txt").read_text(encoding="utf-8")
    anon, contagem = anonimizar_texto(texto)
    _confere_gabarito(anon, contagem)


def test_gabarito_passando_pela_ingestao_txt_e_docx():
    """O caminho real: ingestão -> anonimização, nos dois arquivos de teste."""
    ingestao = pytest.importorskip("fabrica_corpus.ingestao")
    if not hasattr(ingestao, "ingerir_pasta"):
        pytest.skip("ingestão real não disponível neste ambiente")
    trechos = [t for t in ingestao.ingerir_pasta(str(PASTA_TESTE)) if t.tipo in ("txt", "docx")]
    assert {t.tipo for t in trechos} == {"txt", "docx"}
    anon, _ = anonimizar_corpus(trechos)
    for t in anon:
        _, contagem = anonimizar_texto(t.texto)        # rodar de novo não acha mais nada
        assert contagem == {"cpf": 0, "email": 0, "telefone": 0, "nome": 0}, t.fonte
        for item in DEVEM_SUMIR:
            assert item not in t.texto, f"{t.fonte}: ficou {item}"
    docx = next(t for t in anon if t.tipo == "docx")
    # a tabela do DOCX chegou e foi anonimizada (não sumiu na ingestão)
    assert "Nome: [NOME]; CPF: [CPF]" in docx.texto


# ------------------------------------------------------------- regras isoladas
def test_contatos_publicos_preservados():
    texto = ("Defesa Civil: Telefone: (11) 3124-5157, e-mail smsuimprensa@prefeitura.sp.gov.br, "
             "SVS: Tel.: (61) 3213-8510, svs@saude.gov.br. Central 156.")
    anon, contagem = anonimizar_texto(texto)
    assert anon == texto
    assert contagem == {"cpf": 0, "email": 0, "telefone": 0, "nome": 0}


def test_telefone_particular_mascarado():
    anon, c = anonimizar_texto("Ligue para (21) 97777-1234 ou 11 3456-7890.")
    assert anon == "Ligue para [TELEFONE] ou [TELEFONE]."
    assert c["telefone"] == 2


def test_numeros_que_nao_sao_telefone_ficam():
    texto = "Em 2015-2030, 40 centímetros, CEP 01301-100, ISBN 978-65-5993-924-4, Lei 12.608/2012."
    anon, c = anonimizar_texto(texto)
    assert c["telefone"] == 0 and c["cpf"] == 0


def test_titulo_em_maiusculas_nao_e_engolido_pelo_nome():
    texto = "RISCOS GEOLÓGICOS E HIDROLÓGICOS Leonardo Andrade de Souza;\nFernando Rocha Nogueira;"
    anon, _ = anonimizar_texto(texto)
    assert anon == "RISCOS GEOLÓGICOS E HIDROLÓGICOS [NOME];\n[NOME];"


def test_orgaos_e_siglas_nao_sao_nomes():
    texto = ("Articular com o Departamento de Assistência Farmacêutica (DAF), o Cievs, o Instituto "
             "Nacional de Meteorologia (Inmet) e a Organização das Nações Unidas (ONU).")
    anon, c = anonimizar_texto(texto)
    assert anon == texto and c["nome"] == 0


def test_metadados_preservados():
    from fabrica_corpus.ingestao import Trecho
    t = Trecho(fonte="x.pdf", tipo="pdf", pagina=12, texto="Contato: joao.silva@example.com")
    anon, total = anonimizar_corpus([t])
    assert (anon[0].fonte, anon[0].tipo, anon[0].pagina) == ("x.pdf", "pdf", 12)
    assert anon[0].texto == "Contato: [EMAIL]" and total["email"] == 1


# ------------------------------------------- falsos positivos vistos no corpus real
def test_palavras_comuns_nao_viram_nome_nem_somem_do_texto():
    # o spaCy marcou "Chuvas Intensas" e "Deslizamentos Planares" como pessoa no corpus real;
    # antes da correção, "Chuvas" e "Deslizamentos" passavam a ser mascarados em todo o texto
    texto = ("Plano para Chuvas Intensas. As chuvas intensas provocam deslizamentos.\n"
             "Deslizamentos Planares ocorrem em encostas. Marco de Ação de Hyogo. "
             "Os deslizamentos planares são comuns. O marco legal define regras.")
    anon, c = anonimizar_texto(texto)
    assert anon == texto and c["nome"] == 0


def test_vocabulario_do_corpus_inteiro():
    from fabrica_corpus.ingestao import Trecho
    # "Transtorno" só aparece em maiúscula neste trecho, mas em minúscula no outro
    t1 = Trecho(fonte="a.html", tipo="html", pagina=None, texto="Transtorno de Estresse Pós-Traumático após a enchente.")
    t2 = Trecho(fonte="b.pdf", tipo="pdf", pagina=1, texto="O transtorno de estresse é comum depois de desastres.")
    anon, total = anonimizar_corpus([t1, t2])
    assert total["nome"] == 0 and anon[0].texto == t1.texto


def test_autor_com_sobrenome_que_e_palavra_comum_continua_mascarado():
    # "rocha" aparece em minúscula (geologia), mas "Fernando" não: é nome
    texto = "Autores: Fernando Rocha Nogueira; Leonardo Andrade de Souza. A rocha alterada desliza."
    anon, c = anonimizar_texto(texto)
    assert "Fernando" not in anon and "Leonardo" not in anon and "A rocha alterada desliza." in anon
