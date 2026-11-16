import json
from types import SimpleNamespace
from fabrica_corpus import geracao as g


def test_filtro_parafrase_resposta_mesmo_sentido():
    anteriores = [{"pergunta": "O que fazer com o animal?", "resposta": "Providencie uma guia ou uma caixa para transportar seu animal."}]
    novo = {"pergunta": "Como levo meu animal?", "resposta": "Providencie uma guia ou uma caixa para transportar seu animal."}
    assert g._repeticao(novo, anteriores)


def test_filtro_nao_remove_orientacoes_distintas():
    ant = [{"pergunta": "O que faço com animais?", "resposta": "Providencie uma guia para seu animal."}]
    assert not g._repeticao({"pergunta": "Onde me informar?", "resposta": "Procure a Defesa Civil."}, ant)


def test_estagio_alerta_nao_e_da_pessoa():
    assert g._risco_qa("O que acontece com a chuva?", "Você entra em estágio de alerta.")


def test_monitoramento_nao_e_conselho_para_morador():
    assert g._risco_qa("O que eu faço para me proteger?", "Monitoramento periódico deve ser realizado e manutenção rotineira dos sistemas de drenagem é recomendada.")


def test_limiar_saude_nao_e_condicao_exclusiva():
    assert g._risco_qa("Tenho diarreia depois da enchente, quando procurar atendimento?", "Procure atendimento somente se tiver 3 episódios de diarreia.")


def test_resposta_saude_segura_nao_bloqueada():
    assert not g._risco_qa("Estou com febre depois da enchente. O que faço?", "Procure uma unidade de saúde.")


def test_cache_qa_chat_novo_sem_perder_recusas():
    seg = SimpleNamespace(id="abc", texto="Evite áreas alagadas", fonte="foo.pdf")
    assert "_v8_3_" in g._chave("qa", seg, "2")
    assert g.VERSAO_PROMPT == "v8_2"


def test_qa_segmento_recusa_duplicadas(monkeypatch):
    seg = SimpleNamespace(id="abc", texto="Providencie uma guia ou uma caixa para transportar seu animal.", fonte="foo.pdf", paginas=[1])
    monkeypatch.setattr(g, "USAR_FATOS", False)
    bloco = {"perguntas": [
      {"pergunta":"O que faço para transportar meu animal?", "resposta":"Providencie uma guia ou uma caixa para transportar seu animal."},
      {"pergunta":"Como posso levar meu animal?", "resposta":"Providencie uma guia ou uma caixa para transportar seu animal."},
    ]}
    r=g._gerar_qa_segmento(seg,lambda m:json.dumps(bloco),2,juiz=False)
    assert len(r["itens"]) == 1
    assert any("redundante" in m for m in r["descartados"])


def test_saude_real_v82_sintomas_multiplo_limiar_diarrreia():
    p = "O que eu faço se tiver sintomas como diarreia, febre ou dor de cabeça depois de uma enchente?"
    r = "Procure atendimento médico se houver três ou mais episódios de diarreia em 24 horas."
    assert g._risco_qa(p, r)


def test_qa_repeticao_global_e_opt_in(monkeypatch):
    """A filtragem nova não deve alterar chamadas legadas de gerar_qa."""
    from types import SimpleNamespace
    segmentos = [SimpleNamespace(id=f'seg_{i}', texto='texto do risco', fonte='fonte.pdf', paginas=[i]) for i in range(6)]
    monkeypatch.setattr(g, 'selecionar', lambda ss, n, **kw: [s for s in ss if s.id not in kw.get('excluir', set())][:n])
    monkeypatch.setattr(g, '_gerar_qa_segmento', lambda seg, gerar, n, juiz: {
        'itens': [{'pergunta': 'Como agir na chuva?', 'resposta': 'Evite a água da enchente.'}],
        'tentativas': 1, 'descartados': []
    })
    sem_filtro, _ = g.gerar_qa(segmentos, lambda m:'', total=4, por_segmento=1, progresso=False)
    com_filtro, estat = g.gerar_qa(segmentos, lambda m:'', total=4, por_segmento=1, progresso=False, filtrar_repeticoes=True)
    assert len(sem_filtro) == 4
    assert len(com_filtro) == 1
    assert estat['motivos_descarte']['duplicação entre segmentos'] >= 1
