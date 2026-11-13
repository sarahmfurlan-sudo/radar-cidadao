"""Testes da geração com um gerador falso (sem GPU). O Qwen de verdade roda no Colab."""
import json

from fabrica_corpus.geracao import (
    amostra_revisao, conferir_fidelidade, gerar_chat, gerar_qa, selecionar,
)
from fabrica_corpus.segmentacao import Segmento
import pytest
import fabrica_corpus.geracao as geracao


@pytest.fixture(autouse=True)
def sem_juiz_por_padrao(monkeypatch):
    """Os testes antigos usam geradores falsos que não sabem responder ao juiz;
    os testes do juiz ligam ele explicitamente (juiz=True)."""
    monkeypatch.setattr(geracao, "USAR_JUIZ", False)
    monkeypatch.setattr(geracao, "USAR_FATOS", False)

TEXTO = ("Durante a enchente, não atravesse ruas alagadas, pois a correnteza pode arrastar você. "
         "Desligue a energia elétrica da casa antes que a água chegue às tomadas. "
         "Em caso de risco, ligue para a Defesa Civil no 199. A água da enchente pode transmitir leptospirose.")


def seg(i, fonte="plano.pdf", texto=TEXTO, tokens=300):
    return Segmento(id=f"{fonte[:5]}_{i:04d}", fonte=fonte, tipo="pdf", paginas=[i], texto=texto, tokens=tokens)


def gerador_fiel(mensagens):
    return json.dumps({"perguntas": [
        {"pergunta": "Posso atravessar a rua alagada?", "resposta": "Não atravesse ruas alagadas, a correnteza pode arrastar você."},
        {"pergunta": "E a luz?", "resposta": "Desligue a energia elétrica da casa antes que a água chegue às tomadas."}],
        "mensagens": [
        {"papel": "cidadao", "texto": "A água está subindo aqui, o que eu faço?"},
        {"papel": "assistente", "texto": "Em caso de risco, ligue para a Defesa Civil no 199."},
        {"papel": "cidadao", "texto": "E a energia?"},
        {"papel": "assistente", "texto": "Desligue a energia elétrica da casa antes que a água chegue às tomadas."}]})


def test_fidelidade_bloqueia_numero_inventado():
    ok, motivo = conferir_fidelidade("Ligue para 0800 123 456 e espere 48 horas.", TEXTO)
    assert not ok and "número" in motivo


def test_fidelidade_aceita_numero_de_emergencia_e_texto_do_trecho():
    assert conferir_fidelidade("Ligue para a Defesa Civil no 199 e para os Bombeiros no 193.", TEXTO)[0]


def test_fidelidade_bloqueia_resposta_que_foge_do_trecho():
    ok, motivo = conferir_fidelidade("Compre um gerador movido a diesel e estoque combustível no telhado.", TEXTO)
    assert not ok and "palavras" in motivo


def test_fidelidade_bloqueia_marcacao_da_anonimizacao():
    assert not conferir_fidelidade("Fale com [NOME] na associação.", TEXTO)[0]


def test_qa_gera_quantidade_pedida_com_fonte_e_paginas():
    segs = [seg(i) for i in range(1, 60)]
    exemplos, estat = gerar_qa(segs, gerador_fiel, total=10, por_segmento=2)
    assert len(exemplos) == 10 and estat["exemplos"] == 10
    assert all(e["fonte"] == "plano.pdf" and e["paginas"] and e["segmento_id"] for e in exemplos)
    assert len({e["id"] for e in exemplos}) == 10


def test_qa_refaz_quando_o_modelo_inventa_e_pula_depois_de_3_tentativas():
    chamadas = []

    def gerador_mentiroso(mensagens):
        chamadas.append(1)
        return json.dumps({"perguntas": [{"pergunta": "Quanto custa?", "resposta": "Custa 350 reais na farmácia."}]})
    exemplos, estat = gerar_qa([seg(1)], gerador_mentiroso, total=2)
    assert exemplos == [] and len(chamadas) == 3 and estat["segmentos_pulados"] == ["plano_0001"]


def test_json_quebrado_e_refeito():
    respostas = iter(["desculpe, não consigo", gerador_fiel(None)])
    exemplos, _ = gerar_qa([seg(1)], lambda m: next(respostas), total=2)
    assert len(exemplos) == 2


def test_chat_no_formato_de_mensagens_com_persona():
    exemplos, _ = gerar_chat([seg(i) for i in range(1, 10)], gerador_fiel, total=3)
    assert len(exemplos) == 3
    papeis = [m["role"] for m in exemplos[0]["mensagens"]]
    assert papeis == ["system", "user", "assistant", "user", "assistant"]
    assert "Radar Cidadão" in exemplos[0]["mensagens"][0]["content"]


def test_chat_recusa_dialogo_sem_alternancia():
    ruim = json.dumps({"mensagens": [{"papel": "assistente", "texto": "Olá."}, {"papel": "assistente", "texto": "Oi."}]})
    exemplos, estat = gerar_chat([seg(1)], lambda m: ruim, total=1)
    assert exemplos == [] and estat["segmentos_pulados"] == ["plano_0001"]


def test_cache_reaproveita_sem_chamar_o_modelo(tmp_path):
    chamadas = []

    def contando(m):
        chamadas.append(1)
        return gerador_fiel(m)
    segs = [seg(i) for i in range(1, 6)]
    gerar_qa(segs, contando, total=4, pasta_cache=tmp_path)
    antes = len(chamadas)
    gerar_qa(segs, contando, total=4, pasta_cache=tmp_path)
    assert len(chamadas) == antes and len(list(tmp_path.iterdir())) == antes


def test_selecao_espalha_entre_documentos_e_prefere_o_tema():
    segs = [seg(i, "mapa.pdf", "Erosão e intemperismo das rochas em detalhe técnico.") for i in range(1, 40)]
    segs += [seg(i, "cartilha.pdf") for i in range(1, 5)]
    escolhidos = selecionar(segs, 6)
    assert {s.fonte for s in escolhidos} == {"mapa.pdf", "cartilha.pdf"}
    assert sum(s.fonte == "cartilha.pdf" for s in escolhidos) == 3


def test_amostra_de_revisao_tem_no_minimo_20_por_cento():
    exemplos = [{"id": i} for i in range(103)]
    assert len(amostra_revisao(exemplos)) == 21
    assert amostra_revisao(exemplos) == amostra_revisao(exemplos)      # sempre a mesma (semente)


def test_citar_a_fonte_pelo_titulo_nao_conta_como_invencao():
    from fabrica_corpus.geracao import TITULOS, titulo
    s = seg(1, fonte="ms_2025_plano_contingencia_chuvas.pdf")
    citando = json.dumps({"perguntas": [{"pergunta": "Posso atravessar a rua alagada?",
        "resposta": f"Segundo o {titulo(s.fonte)}, não atravesse ruas alagadas, a correnteza pode arrastar você."}]})
    exemplos, _ = gerar_qa([s], lambda m: citando, total=1)
    assert len(exemplos) == 1 and "2025" in exemplos[0]["resposta"]
    assert set(TITULOS) >= {"mcid_2026_mapeamento_riscos.pdf", "ms_2026_enchentes.html", "cgesp_2026_dicas_alagamentos.docx"}


def test_prompt_recebe_titulo_e_nao_o_nome_do_arquivo():
    recebidos = []

    def espiao(mensagens):
        recebidos.append(mensagens[0]["content"])
        return gerador_fiel(mensagens)
    gerar_qa([seg(1, fonte="ms_2017_cartilha_alerta_chuvas.pdf")], espiao, total=1)
    assert "Cartilha de Alerta de Chuvas Intensas" in recebidos[0] and ".pdf" not in recebidos[0]


def test_citacao_automatica_no_fim_da_resposta_e_do_dialogo():
    s = seg(1, fonte="mcid_2024_periferia_sem_risco.pdf")
    s.paginas = [7, 8, 9]
    qa, _ = gerar_qa([s], gerador_fiel, total=1, progresso=False)
    assert qa[0]["resposta"].endswith("Fonte: Periferia Sem Risco, do Ministério das Cidades (2024), p. 7-9.")
    chat, _ = gerar_chat([s], gerador_fiel, total=1, progresso=False)
    falas = [m for m in chat[0]["mensagens"] if m["role"] == "assistant"]
    assert falas[-1]["content"].endswith("p. 7-9.") and "Fonte:" not in falas[0]["content"]


def test_prompt_nao_pede_citacao_ao_modelo_e_traz_as_regras_novas():
    recebidos = []
    gerar_qa([seg(1)], lambda m: recebidos.append(m[0]["content"]) or gerador_fiel(m), total=1, progresso=False)
    prompt = recebidos[0]
    assert "citando a fonte" not in prompt and "acrescentada automaticamente" in prompt
    assert "Como me preparar para um deslizamento" in prompt and "QUEM AGE" in prompt


def test_progresso_aparece_na_tela(capsys):
    gerar_qa([seg(1)], gerador_fiel, total=2)
    assert "[perguntas] 2/2" in capsys.readouterr().out


def test_json_em_varios_blocos_e_lido():
    # o que o Qwen fez no teste real: uma fala por objeto, em sequência
    falas = ['{"papel": "cidadao", "texto": "A água está subindo aqui, o que eu faço?"}',
             '{"papel": "assistente", "texto": "Em caso de risco, ligue para a Defesa Civil no 199."}',
             '{"papel": "cidadao", "texto": "E a energia?"}',
             '{"papel": "assistente", "texto": "Desligue a energia elétrica da casa antes que a água chegue às tomadas."}']
    exemplos, _ = gerar_chat([seg(1)], lambda m: "\n".join(falas), total=1, progresso=False)
    assert len(exemplos) == 1 and len(exemplos[0]["mensagens"]) == 5


def test_bloco_repetido_vale_o_primeiro():
    duplicado = gerador_fiel(None) + "\n" + gerador_fiel(None)
    exemplos, _ = gerar_qa([seg(1)], lambda m: duplicado, total=2, progresso=False)
    assert len(exemplos) == 2


def test_teto_de_segmentos_evita_laco_sem_fim():
    chamadas = []
    exemplos, estat = gerar_chat([seg(i) for i in range(1, 300)],
                                 lambda m: chamadas.append(1) or "nada", total=1, progresso=False)
    assert exemplos == [] and estat["segmentos_tentados"] == 6 and len(chamadas) == 18


def test_recusa_nao_fica_no_cache(tmp_path):
    gerar_qa([seg(1)], lambda m: "sem json", total=2, pasta_cache=tmp_path, progresso=False)
    assert list(tmp_path.iterdir()) == []
    exemplos, _ = gerar_qa([seg(1)], gerador_fiel, total=2, pasta_cache=tmp_path, progresso=False)
    assert len(exemplos) == 2 and len(list(tmp_path.iterdir())) == 1


def test_dialogo_em_um_bloco_por_troca_e_juntado():
    # o que o Qwen fez no teste real: {"mensagens": [pergunta, resposta]}`{"mensagens": [...]}`
    b1 = '{"mensagens":[{"papel":"cidadao","texto":"A água está subindo, o que eu faço?"},{"papel":"assistente","texto":"Em caso de risco, ligue para a Defesa Civil no 199."}]}'
    b2 = '{"mensagens":[{"papel":"cidadao","texto":"E a energia?"},{"papel":"assistente","texto":"Desligue a energia elétrica antes que a água chegue às tomadas."}]}'
    exemplos, _ = gerar_chat([seg(1)], lambda m: b1 + "`" + b2 + "`", total=1, progresso=False)
    assert len(exemplos) == 1 and [m["role"] for m in exemplos[0]["mensagens"]] == [
        "system", "user", "assistant", "user", "assistant"]


def test_reescrita_em_linguagem_simples_e_aceita():
    trecho = ("É importante conversar com os moradores mais antigos e lembrar dos locais onde já houve "
              "deslizamentos ou inundações, registrando essas informações em mapas.")
    resposta = "Converse com os moradores antigos e marque no mapa onde já houve deslizamentos ou inundações."
    assert conferir_fidelidade(resposta, trecho)[0]



# ------------------------------------------------------------ juiz e referência ao texto
def gerador_com_juiz(veredito_par2=True):
    """Responde à geração com 2 perguntas e, ao juiz, aprova o par 1 e o par 2 conforme o pedido."""
    def gerar(mensagens):
        prompt = mensagens[0]["content"]
        if "AVALIE" in prompt:
            return json.dumps({"avaliacoes": [
                {"par": 1, "apoiada": True, "responde": True, "mesmo_agente": True, "motivo": ""},
                {"par": 2, "apoiada": True, "responde": veredito_par2, "mesmo_agente": True,
                 "motivo": "" if veredito_par2 else "responde outra coisa"}]})
        return gerador_fiel(mensagens)
    return gerar


def test_juiz_aprova_e_reprova_por_par():
    exemplos, estat = gerar_qa([seg(1)], gerador_com_juiz(veredito_par2=False), total=2,
                               progresso=False, juiz=True)
    assert len(exemplos) == 1 and estat["respostas_descartadas"] == 1


def test_juiz_ilegivel_reprova_e_refaz():
    chamadas = []

    def gerar(m):
        chamadas.append(1)
        return "não sei" if "AVALIE" in m[0]["content"] else gerador_fiel(m)
    exemplos, estat = gerar_qa([seg(1)], gerar, total=2, progresso=False, juiz=True)
    assert exemplos == [] and len(chamadas) == 6          # 3 tentativas x (geração + juiz)


def test_juiz_no_dialogo_avalia_cada_troca():
    exemplos, _ = gerar_chat([seg(1)], gerador_com_juiz(True), total=1, progresso=False, juiz=True)
    assert len(exemplos) == 1
    exemplos, estat = gerar_chat([seg(2)], gerador_com_juiz(False), total=1, progresso=False, juiz=True)
    assert exemplos == [] and estat["segmentos_pulados"] == ["plano_0002"]


def test_referencia_ao_texto_e_recusada_sem_chamar_o_juiz():
    ruim = json.dumps({"perguntas": [{"pergunta": "O que isso aqui fala sobre ruas alagadas?",
                                      "resposta": "Não atravesse ruas alagadas, a correnteza pode arrastar você."},
                                     {"pergunta": "O que o trecho diz da energia?",
                                      "resposta": "Desligue a energia elétrica da casa."}]})
    exemplos, estat = gerar_qa([seg(1)], lambda m: ruim, total=2, progresso=False, juiz=True)
    assert exemplos == [] and estat["segmentos_pulados"] == ["plano_0001"]


def test_prompt_do_juiz_traz_trecho_e_pares():
    recebidos = []

    def gerar(m):
        recebidos.append(m[0]["content"])
        return gerador_com_juiz()(m)
    gerar_qa([seg(1)], gerar, total=2, progresso=False, juiz=True)
    juiz = next(p for p in recebidos if "AVALIE" in p)
    assert "Durante a enchente" in juiz and "1. Pergunta:" in juiz and "2. Pergunta:" in juiz



def test_juiz_reprova_resposta_nao_apoiada_no_trecho():
    def gerar(m):
        if "AVALIE" in m[0]["content"]:
            return json.dumps({"avaliacoes": [
                {"par": 1, "apoiada": False, "responde": True, "mesmo_agente": True, "motivo": "acrescenta orientação"},
                {"par": 2, "apoiada": True, "responde": True, "mesmo_agente": True, "motivo": ""}]})
        return gerador_fiel(m)
    exemplos, estat = gerar_qa([seg(1)], gerar, total=2, progresso=False, juiz=True)
    assert len(exemplos) == 1 and estat["respostas_descartadas"] == 1


def test_reescrita_livre_do_14b_passa_no_filtro_de_25():
    trecho = ("Converse com os moradores mais antigos da comunidade e lembre os locais onde já houve "
              "deslizamentos ou inundações. Registre tudo em mapas e desenhos.")
    resposta = "Pergunte aos vizinhos mais velhos sobre desastres passados e veja onde já houve alagamentos ou deslizamentos."
    assert conferir_fidelidade(resposta, trecho)[0]


def test_cidadao_na_geracao_nao_recebe_lista_de_assuntos():
    recebidos = []
    gerar_qa([seg(1)], lambda m: recebidos.append(m[0]["content"]) or gerador_fiel(m), total=1, progresso=False)
    assert "limpeza, doenças" not in recebidos[0] and "SÓ pergunta sobre o que o trecho" in recebidos[0]



# ------------------------------------------------------------ v8: geração em etapas
FATOS_OK = json.dumps({"util": True, "fatos": [
    {"fato": "Não atravesse ruas alagadas, pois a correnteza pode arrastar você.", "quem_age": "morador", "orgao": ""},
    {"fato": "Desligue a energia elétrica da casa antes que a água chegue às tomadas.", "quem_age": "morador", "orgao": ""},
    {"fato": "A Defesa Civil atende pelo 199 em caso de risco.", "quem_age": "poder_publico", "orgao": "Defesa Civil"}]})


def gerador_v8(fatos=FATOS_OK):
    def gerar(m):
        prompt = m[0]["content"]
        if "LISTE OS FATOS" in prompt:
            return fatos
        if "AVALIE" in prompt:
            return json.dumps({"avaliacoes": [{"par": i, "apoiada": True, "responde": True, "mesmo_agente": True}
                                              for i in range(1, 4)]})
        return gerador_fiel(m)
    return gerar


def test_v8_perguntas_nascem_dos_fatos_com_quem_age(monkeypatch):
    monkeypatch.setattr(geracao, "USAR_FATOS", True)
    recebidos = []
    g = gerador_v8()
    exemplos, _ = gerar_qa([seg(1)], lambda m: recebidos.append(m[0]["content"]) or g(m), total=2,
                           progresso=False, juiz=True)
    assert len(exemplos) == 2
    prompt_qa = next(p for p in recebidos if "Fatos tirados" in p)
    assert "[morador] Não atravesse" in prompt_qa and "[poder_publico (Defesa Civil)]" in prompt_qa
    assert "Durante a enchente" not in prompt_qa       # a etapa 2 vê só os fatos, não o trecho


def test_v8_fato_inventado_e_descartado_na_extracao(monkeypatch):
    monkeypatch.setattr(geracao, "USAR_FATOS", True)
    inventado = json.dumps({"util": True, "fatos": [
        {"fato": "Ligue para 0800 777 1234 e espere 48 horas.", "quem_age": "morador"},
        {"fato": "Compre um gerador movido a diesel para o telhado.", "quem_age": "morador"}]})
    exemplos, estat = gerar_qa([seg(1)], gerador_v8(inventado), total=2, progresso=False)
    assert exemplos == [] and estat["segmentos_pulados"] == ["plano_0001"]


def test_v8_segmento_sem_fatos_uteis_e_pulado_sem_gerar(monkeypatch):
    monkeypatch.setattr(geracao, "USAR_FATOS", True)
    chamadas = []
    vazio = json.dumps({"util": False, "fatos": []})
    gerar_qa([seg(1)], lambda m: chamadas.append(1) or vazio, total=2, progresso=False)
    assert len(chamadas) == 1          # só a extração; nada de geração nem juiz


def test_v8_dialogo_tem_tantas_trocas_quantos_fatos(monkeypatch):
    monkeypatch.setattr(geracao, "USAR_FATOS", True)
    recebidos = []
    dois = json.dumps({"util": True, "fatos": json.loads(FATOS_OK)["fatos"][:2]})
    g = gerador_v8(dois)
    gerar_chat([seg(1)], lambda m: recebidos.append(m[0]["content"]) or g(m), total=1, progresso=False)
    assert any("diálogo de 2 trocas" in p for p in recebidos)


def test_v8_dialogo_precisa_de_2_fatos(monkeypatch):
    monkeypatch.setattr(geracao, "USAR_FATOS", True)
    um = json.dumps({"util": True, "fatos": json.loads(FATOS_OK)["fatos"][:1]})
    exemplos, estat = gerar_chat([seg(1)], gerador_v8(um), total=1, progresso=False)
    assert exemplos == [] and estat["segmentos_pulados"] == ["plano_0001"]


def test_divisao_planejada_reparte_cada_documento_entre_perguntas_e_dialogos():
    from fabrica_corpus.geracao import planejar_divisao
    segs = [seg(i, f) for f in ("periferia.pdf", "cartilha.pdf", "mapa.pdf") for i in range(1, 9)]
    qa, chat = planejar_divisao(segs, n_qa=10, n_chat=6)
    assert {s.fonte for s in qa} == {s.fonte for s in chat} == {"periferia.pdf", "cartilha.pdf", "mapa.pdf"}
    assert not {s.id for s in qa} & {s.id for s in chat} and len(qa) + len(chat) == 24


def test_conjunto_de_avaliacao_e_fixo_e_espalhado():
    from fabrica_corpus.geracao import conjunto_avaliacao
    segs = [seg(i, f) for f in ("a.pdf", "b.pdf", "c.pdf", "d.pdf") for i in range(1, 20)]
    um, dois = conjunto_avaliacao(segs), conjunto_avaliacao(segs)
    assert [s.id for s in um] == [s.id for s in dois] and len(um) == 12
    assert {s.fonte for s in um} == {"a.pdf", "b.pdf", "c.pdf", "d.pdf"}


def test_medir_juiz_contra_revisao_humana(tmp_path):
    from fabrica_corpus.geracao import medir_juiz
    import csv
    rot = tmp_path / "rotulos.csv"
    with open(rot, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "motivo", "fonte", "paginas", "pergunta / diálogo", "resposta", "rotulo", "motivo do N"])
        w.writerow(["qa_1", "", "plano.pdf", "[1]", "Posso atravessar a rua alagada?",
                    "Não atravesse ruas alagadas, a correnteza pode arrastar você.\n\nFonte: X, p. 1.", "S", ""])
        w.writerow(["chat_1", "", "plano.pdf", "[1]",
                    "user: O que isso aqui fala da energia?\nassistant: Desligue a energia elétrica da casa.\n\nFonte: X.",
                    "", "N", "fala do texto"])
        w.writerow(["qa_2", "", "plano.pdf", "[1]", "E a energia?", "Desligue a energia elétrica da casa.", "N", "teste"])
    aprova_tudo = lambda m: json.dumps({"avaliacoes": [{"par": 1, "apoiada": True, "responde": True, "mesmo_agente": True}]})
    r = medir_juiz(rot, [seg(1)], aprova_tudo)
    assert r["itens"] == 3 and r["humano_S_sistema_aprova"] == 1 and r["humano_N_sistema_reprova"] == 1
    assert r["humano_N_sistema_aprova"] == 1 and r["concordancia"] == 0.67
    assert [d[0] for d in r["divergencias"]] == ["qa_2"]
