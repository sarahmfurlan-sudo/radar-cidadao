import csv
import json
from types import SimpleNamespace
from fabrica_corpus import geracao as g


def _seg(ident, texto, paginas):
    return SimpleNamespace(id=ident, fonte="documento.pdf", texto=texto, paginas=paginas)


def _juiz_ok(mensagens):
    prompt = mensagens[0]["content"]
    pares = prompt.split("Pares:", 1)[-1].count("Pergunta:")
    return json.dumps({"avaliacoes": [
        {"par": i, "apoiada": True, "responde": True, "mesmo_agente": True, "motivo": ""}
        for i in range(1, pares + 1)]})


def _csv(tmp_path, pagina="[1, 2]", rotulo="S"):
    arquivo = tmp_path / "rotulos.csv"
    with arquivo.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "motivo", "fonte", "paginas", "pergunta / dialogo", "resposta", "rotulo (S/N)", "motivo do N"])
        w.writerow(["qa_0001", "amostra", "documento.pdf", pagina,
                    "O que fazer antes da enchente?", "Evite ruas alagadas.", rotulo, ""])
    return arquivo


def test_v82_avaliacao_legada_concatenando_trechos_ambiguos(tmp_path):
    segs = [_seg("a", "Evite ruas alagadas.", [1, 2]),
            _seg("b", "Observe o nivel da agua.", [1, 2])]
    result = g.medir_juiz(_csv(tmp_path), segs, _juiz_ok)
    assert result["itens"] == 1
    assert result["itens_csv"] == 1
    assert result["itens_contexto_expandido"] == 1
    assert result["itens_nao_avaliados"] == 0
    assert result["humano_S_sistema_aprova"] == 1


def test_v82_avaliacao_legada_paginas_sobrepostas(tmp_path):
    segs = [_seg("a", "Evite ruas alagadas.", [1]),
            _seg("b", "Observe o nivel da agua.", [2])]
    result = g.medir_juiz(_csv(tmp_path), segs, _juiz_ok)
    assert result["itens"] == 1
    assert result["itens_contexto_expandido"] == 1


def test_v82_avaliacao_legada_sem_segmento_nao_inventa_resultado(tmp_path):
    result = g.medir_juiz(_csv(tmp_path, pagina="[99]"),
                          [_seg("a", "Evite ruas alagadas.", [1])], _juiz_ok)
    assert result["itens"] == 0
    assert result["itens_csv"] == 1
    assert result["itens_nao_avaliados"] == 1


def test_v82_qa_retentativa_acumula_sem_duplicar(monkeypatch):
    seg = _seg("x", "Evite ruas alagadas. Observe o nivel da agua.", [1])
    monkeypatch.setattr(g, "USAR_FATOS", False)
    valores = [
        {"perguntas": [{"pergunta": "Onde evitar?", "resposta": "Evite ruas alagadas."}]},
        {"perguntas": [{"pergunta": "Onde evitar?", "resposta": "Evite ruas alagadas."},
                        {"pergunta": "O que observar?", "resposta": "Observe o nivel da agua."}]},
    ]
    chamadas = []
    def gerar(m):
        chamadas.append(1)
        return json.dumps(valores[min(len(chamadas) - 1, 1)])
    r = g._gerar_qa_segmento(seg, gerar, n=2, juiz=False)
    assert len(r["itens"]) == 2
    assert r["tentativas"] == 2
    assert len({x["pergunta"] for x in r["itens"]}) == 2
