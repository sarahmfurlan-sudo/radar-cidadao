"""Testes da geração com um gerador falso (sem GPU). O Qwen de verdade roda no Colab."""
import json

from fabrica_corpus.geracao import (
    amostra_revisao, conferir_fidelidade, gerar_chat, gerar_qa, selecionar,
)
from fabrica_corpus.segmentacao import Segmento

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
