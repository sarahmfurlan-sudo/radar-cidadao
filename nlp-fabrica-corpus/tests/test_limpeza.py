"""Testes da limpeza, com trechos reais da amostra dos documentos."""
import pytest

from fabrica_corpus.ingestao import Trecho
from fabrica_corpus.limpeza import (
    juntar_hifenizacao, juntar_linhas, limpar_corpus, normalizar_caracteres,
    remover_boilerplate, remover_numeros_pagina, remover_referencias, remover_sumario, vocabulario,
)

CABECALHO = ("Mapeamento de Riscos: Conceitos e métodos aplicados a processos geológicos e hidrológicos "
             "Mapeamento de Riscos: Conceitos e métodos aplicados a processos geológicos e hidrológicos")


def test_hifenizacao_com_e_sem_espaco():
    assert juntar_hifenizacao("esses traba-\nlhos") == "esses trabalhos"
    assert juntar_hifenizacao("aqueci -\nmento global") == "aquecimento global"
    assert juntar_hifenizacao("matas cilia -\nres") == "matas ciliares"


def test_hifenizacao_nao_mexe_em_hifen_normal():
    assert juntar_hifenizacao("1-Enchentes") == "1-Enchentes"
    assert juntar_hifenizacao("Brasília / DF - 2017") == "Brasília / DF - 2017"
    # próxima linha começa com maiúscula: não é palavra quebrada
    assert juntar_hifenizacao("CODAR -\nNE.HIG") == "CODAR -\nNE.HIG"


def test_hifen_invisivel_e_espacos_especiais():
    assert normalizar_caracteres("moni\u00adtoramento") == "monitoramento"
    assert normalizar_caracteres("Defesa\u00a0Civil") == "Defesa Civil"
    assert normalizar_caracteres("\u201cAceitar todos\u201d") == '"Aceitar todos"'


def test_numero_de_pagina_sozinho():
    texto = "Vamos juntos?\n1\nfim\n16 17\n212 213"
    assert remover_numeros_pagina(texto) == "Vamos juntos?\nfim"


def test_numero_dentro_da_frase_fica():
    texto = "ligue 199 ou 193"
    assert remover_numeros_pagina(texto) == texto


def test_sumario_com_pontilhado():
    texto = "PARTE I\nDEFINIÇÕES DE ALERTAS..........................07\nOBJETIVOS"
    assert remover_sumario(texto) == "PARTE I\nOBJETIVOS"


def test_boilerplate_da_prefeitura():
    texto = (
        "Acesso à informação Transparência São Paulo Legislação Ouvidoria 156\n"
        "Início Secretarias Defesa CivilDefesa Civil Cuidados Importantes\n"
        "Chuvas excessivas\n"
        "© COPYRIGHT 2026, Prefeitura Municipal de São Paulo\n"
        "A Prefeitura de São Paulo valoriza sua privacidade!\n"
        "Em nosso site, utilizamos cookies.\n"
        "utilização de cookies. Saiba mais\n"
        "Configuração Aceitar tudo Recusar tudo"
    )
    assert remover_boilerplate(texto).strip() == "Chuvas excessivas"


def test_juntar_linhas_da_mesma_frase():
    texto = "As enchentes e inundações\nsão eventos naturais."
    assert juntar_linhas(texto) == "As enchentes e inundações são eventos naturais."


def test_nao_junta_itens_de_lista_nem_frase_terminada():
    texto = "Cuidados antes da enchente:\n1. Moradores devem se informar;\n2. Feche portas."
    assert juntar_linhas(texto) == texto
    texto2 = "Vamos juntos?\nque tal"  # frase terminada com '?' não é continuada
    assert juntar_linhas(texto2) == texto2


def test_html_com_link_em_linha_propria():
    texto = "infecções, como \nleptospirose\n e \ndengue\n. Além disso"
    limpo, _ = limpar_corpus([Trecho(fonte="ms_2026_enchentes.html", tipo="html", pagina=None, texto=texto)])
    assert limpo[0].texto == "infecções, como leptospirose e dengue. Além disso"


def test_html_muitas_linhas_em_branco():
    texto = "\n" * 60 + "Enchentes — Ministério da Saúde" + "\n" * 40 + "Medidas de segurança."
    limpo, _ = limpar_corpus([Trecho(fonte="x.html", tipo="html", pagina=None, texto=texto)])
    assert limpo[0].texto == "Enchentes - Ministério da Saúde\n\nMedidas de segurança."


CONTEUDOS = ["A erosão remove partículas.", "O risco R3 é alto.", "Mapear orienta decisões.",
             "Chuvas intensas agravam.", "A ocupação é desordenada."]


def test_cabecalho_repetido_em_varias_paginas():
    paginas = [
        Trecho(fonte="mapa.pdf", tipo="pdf", pagina=n, texto=f"{2*n} {2*n+1}\n{CABECALHO}\n{texto}")
        for n, texto in enumerate(CONTEUDOS, start=1)
    ]
    limpo, estat = limpar_corpus(paginas)
    assert [t.texto for t in limpo] == CONTEUDOS
    assert estat["repetidas_por_documento"]["mapa.pdf"] >= 1


def test_linha_que_aparece_pouco_nao_e_removida():
    paginas = [Trecho(fonte="doc.pdf", tipo="pdf", pagina=n, texto=f"Texto {n}.") for n in range(1, 6)]
    paginas[0] = Trecho(fonte="doc.pdf", tipo="pdf", pagina=1, texto="Linha única importante.\nTexto 1.")
    limpo, _ = limpar_corpus(paginas)
    assert "Linha única importante." in limpo[0].texto


def test_metadados_preservados_e_vazios_descartados():
    trechos = [Trecho(fonte="a.pdf", tipo="pdf", pagina=7, texto="Texto real\nda página."), Trecho(fonte="a.pdf", tipo="pdf", pagina=8, texto="8")]
    limpo, estat = limpar_corpus(trechos)
    assert len(limpo) == 1
    assert (limpo[0].fonte, limpo[0].tipo, limpo[0].pagina) == ("a.pdf", "pdf", 7)
    assert estat["trechos_vazios_descartados"] == 1
    assert estat["caracteres_depois"] < estat["caracteres_antes"]


def test_dados_pessoais_nao_sao_tocados():
    # a limpeza não anonimiza: o CPF tem que continuar lá para a próxima etapa
    texto = "Nome: Mariana Toledo Vasconcelos; CPF: 123.456.789-10"
    limpo, _ = limpar_corpus([Trecho(fonte="teste.docx", tipo="docx", pagina=None, texto=texto)])
    assert limpo[0].texto == texto


def test_titulo_de_secao_repetido_no_meio_fica():
    # "Caracterização" aparece em todas as páginas do Manual, mas no meio do texto
    paginas = [Trecho(fonte="manual.pdf", tipo="pdf", pagina=n, texto=f"{n} - Capítulo {n}\nCODAR: {n}\nCaracterização\nTexto do capítulo {n}, parte um.\n"
                      f"Mais texto.\nCausas\nTexto das causas.\nOcorrência\nFim do capítulo.")
               for n in range(1, 7)]
    limpo, _ = limpar_corpus(paginas)
    assert all("Caracterização" in t.texto and "Causas" in t.texto for t in limpo)


def test_letra_capitular():
    assert juntar_hifenizacao("E\nvidências técnicas") == "Evidências técnicas"
    # com espaço depois é a palavra "A", não capitular
    assert juntar_linhas(juntar_hifenizacao("A \nerosão é definida")) == "A erosão é definida"


def test_hifen_invisivel_no_fim_da_linha():
    assert normalizar_caracteres("o moni\u00ad\ntoramento e a") == "o monitoramento e a"


def test_linha_cheia_continua_com_maiuscula():
    texto = ("Nesse contexto, destacam-se os eventos conduzidos pela ONU, como o United\n"
             "Nations Office for Disaster Risk Reduction (UNDRR).")
    assert juntar_linhas(texto) == texto.replace("United\n", "United ")


def test_titulo_curto_nao_e_juntado():
    texto = "SETOR AÇÕES\nAtenção Primária à Saúde\n1. Participar da Sala."
    assert juntar_linhas(texto) == texto


def test_cabecalho_alternado_em_paginas_impares():
    titulo = "Plano de contingência nacional para emergências em saúde pública por chuvas intensas"
    paginas = []
    for n in range(1, 11):
        topo = titulo if n % 2 else "Capítulo sobre vigilância em saúde ambiental"
        paginas.append(Trecho(fonte="plano.pdf", tipo="pdf", pagina=n, texto=f"{topo}\n{n}\nTexto próprio da página {n}."))
    paginas[0] = Trecho(fonte="plano.pdf", tipo="pdf", pagina=1, texto="PLANO DE CONTINGÊNCIA (capa)")
    limpo, _ = limpar_corpus(paginas)
    assert all(titulo not in t.texto for t in limpo)


def test_linha_terminada_em_virgula_continua():
    assert juntar_linhas("biomas do país - Cerrado,\nCaatinga, Mata Atlântica") == "biomas do país - Cerrado, Caatinga, Mata Atlântica"


REFS = ("Os riscos devem ser mapeados com participação social.\n"
        "REFERÊNCIAS\n"
        "BRASIL. Ministério das Cidades. Plano de ação para riscos. Brasília, 2024.\n"
        "SOUZA, L. A.; MOURA, R. B. Mapeamento de riscos. Disponível em: https://exemplo.gov.br. Acesso em: 10 jan. 2025.\n"
        "\n"
        "JACOBI, P. R. Gestão de riscos. São Paulo: Annablume, 2018.\n"
        "Capítulo 2 - Medidas não estruturais\n"
        "As medidas não estruturais complementam as obras.")


def test_referencias_cortadas_e_texto_seguinte_fica():
    texto, n = remover_referencias(REFS)
    assert n == 3
    assert "SOUZA" not in texto and "JACOBI" not in texto and "REFERÊNCIAS" not in texto
    assert texto.startswith("Os riscos devem ser mapeados")
    assert texto.endswith("As medidas não estruturais complementam as obras.")


def test_citacao_em_varias_linhas_sem_titulo():
    # trecho real do Mapeamento, p. 39 e 59
    texto = ("IPCC. Climate Change 2022: Impacts, Adaptation and\n"
             "Vulnerability. Contribution of Working Group II to the\n"
             "Sixth Assessment Report of the Intergovernmental\n"
             "Panel on Climate Change. Cambridge: Cambridge\n"
             "University Press, 2022.\n"
             "STERNBERG, H. O'R. A água e o homem na várzea do Careiro.\n"
             "Belém: Museu Paraense Emílio Goeldi, 1998.\n"
             "SGB/CPRM. Manual de mapeamento de perigo e risco geológico. Brasília: Serviço Geológico do Brasil, 2015.\n"
             "Paralelamente, as ações não estruturais são imprescindíveis para todas as classes de risco.")
    limpo, n = remover_referencias(texto)
    assert limpo == "Paralelamente, as ações não estruturais são imprescindíveis para todas as classes de risco."
    assert n == 8


def test_titulo_de_capitulo_depois_das_referencias_fica():
    texto = ("TRICART, J. Tipos de planícies aluviais. Revista Brasileira de Geografia, v. 39, n. 2, 1977.\n"
             "UNDRR. Global Assessment Report on Disaster Risk\n"
             "Reduction (GAR 2023). Geneva: UNDRR, 2023.\n"
             "CAPÍTULO 4 MOVIMENTOS DE MASSA\n"
             "Os movimentos de massa ocorrem em encostas.")
    limpo, _ = remover_referencias(texto)
    assert limpo == "CAPÍTULO 4 MOVIMENTOS DE MASSA\nOs movimentos de massa ocorrem em encostas."


def test_sem_titulo_de_referencias_nada_muda():
    texto = "BRASIL. Ministério da Saúde orienta a população.\nVeja as dicas."
    assert remover_referencias(texto) == (texto, 0)


def test_texto_com_ano_no_fim_nao_e_referencia():
    texto = "A cheia mais alta foi registrada em 2009.\nAs famílias foram removidas."
    assert remover_referencias(texto) == (texto, 0)


def test_referencias_contadas_nas_estatisticas():
    limpo, estat = limpar_corpus([Trecho(fonte="map.pdf", tipo="pdf", pagina=9, texto=REFS)])
    assert estat["linhas_de_referencia_removidas"] == 3
    assert "Capítulo 2" in limpo[0].texto


def test_capitular_com_espaco_e_juntada_quando_o_corpus_confirma():
    texto = "T odos os anos chove. T ambém há deslizamentos. T ente avisar os vizinhos."
    vocab = vocabulario(["Todos ajudam. Também. Tente de novo."])
    assert juntar_hifenizacao(texto, vocab) == "Todos os anos chove. Também há deslizamentos. Tente avisar os vizinhos."


def test_capitular_nao_junta_letra_solta_antes_de_palavra_de_verdade():
    # os 9 erros da primeira versão no Mapeamento e no Guia
    corpus = ("A abrangência do risco. As consequências e os sinais. Sobre o tema. Souza et al. 2020. "
              "P abrangência P consequências P sinais S sobre F et T tradu")
    vocab = vocabulario([corpus])
    texto = "P abrangência P consequências P sinais S sobre F et al. T tradu"
    assert juntar_hifenizacao(texto, vocab) == texto


def test_capitular_nao_junta_palavras_de_verdade():
    texto = "A erosão aumenta. E depois a água baixa. O ponto X de encontro fica na praça."
    assert juntar_hifenizacao(texto) == texto


def test_limpar_corpus_usa_o_vocabulario_de_todos_os_documentos():
    a = Trecho(fonte="a.pdf", tipo="pdf", pagina=1, texto="T odos os anos chove forte.")
    b = Trecho(fonte="b.pdf", tipo="pdf", pagina=1, texto="Todos devem se preparar.")
    limpos, _ = limpar_corpus([a, b])
    assert limpos[0].texto.startswith("Todos os anos")
