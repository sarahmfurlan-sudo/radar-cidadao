import json
from fabrica_corpus import geracao as g


def _duas_mensagens(m):
    return json.dumps({"mensagens": [
        {"papel": "cidadao", "texto": "Tenho febre depois da enchente. É leptospirose?"},
        {"papel": "assistente", "texto": "Não posso diagnosticar. Procure uma unidade de saúde ou um médico."},
    ]}, ensure_ascii=False)


def test_recusa_curta_real_do_qwen_e_completada():
    msgs = g._extrair_json(_duas_mensagens(None), "mensagens")["mensagens"]
    novo = g._completar_recusa_curta(msgs, g.TEMAS_RECUSA[0])
    assert len(novo) == 4
    assert [m["papel"] for m in novo] == ["cidadao", "assistente", "cidadao", "assistente"]
    assert g._conferir_recusa(novo, g.TEMAS_RECUSA[0]) == (True, "ok")
    assert novo[-1]["texto"] == msgs[1]["texto"]


def test_recusa_sem_encaminhamento_nao_e_completada():
    msgs = [{"papel": "cidadao", "texto": "Oi"},
            {"papel": "assistente", "texto": "Não sei."}]
    assert g._completar_recusa_curta(msgs, g.TEMAS_RECUSA[0]) == msgs
    assert not g._conferir_recusa(msgs, g.TEMAS_RECUSA[0])[0]


def test_recusa_com_numero_inventado_nao_e_completada():
    msgs = [{"papel": "cidadao", "texto": "Oi"},
            {"papel": "assistente", "texto": "Procure a unidade de saúde amanhã às 123456."}]
    assert g._completar_recusa_curta(msgs, g.TEMAS_RECUSA[0]) == msgs


def test_recusas_de_uma_troca_geram_dialogo_valido(tmp_path):
    exemplos, estat = g.gerar_recusas(_duas_mensagens, total=1, pasta_cache=tmp_path, progresso=False)
    assert estat["exemplos"] == 1
    assert len(exemplos[0]["mensagens"]) == 5  # system + 4 mensagens
    assert [m["role"] for m in exemplos[0]["mensagens"]] == ["system", "user", "assistant", "user", "assistant"]
    assert len(list(tmp_path.glob("*v8_2_r2_*.json"))) == 1


def test_recusa_valida_com_quatro_mensagens_nao_muda():
    tema = g.TEMAS_RECUSA[0]
    msgs = g._completar_recusa_curta(g._extrair_json(_duas_mensagens(None), "mensagens")["mensagens"], tema)
    assert g._completar_recusa_curta(msgs, tema) == msgs
