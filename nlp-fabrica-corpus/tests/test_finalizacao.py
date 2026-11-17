"""Testes da finalização (corpus revisados -> formatação -> validação -> gravação), sem modelo."""
import json

from fabrica_corpus.finalizacao import (
    chave_duplicata, conferir_formato, finalizar, formatar_chat, formatar_qa, recusa_valida, tirar_paginas,
)
from fabrica_corpus.segmentacao import Segmento


def qa(pergunta, resposta, fonte="ms_2017_cartilha_alerta_chuvas.pdf", seg="ms_2017_cartilha_alerta_chuvas_0001"):
    return {"instruction": pergunta, "input": "", "output": resposta, "fonte": fonte, "segmento_id": seg}


def chat(falas, tipo="chat", fonte="ms_2017_cartilha_alerta_chuvas.pdf", seg="ms_2017_cartilha_alerta_chuvas_0002"):
    mensagens = [{"role": "system", "content": "persona"}] + [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f} for i, f in enumerate(falas)]
    return {"messages": mensagens, "fonte": fonte, "tipo": tipo, "segmento_id": seg}


CITACAO = "\n\nFonte: Cartilha de Alerta de Chuvas Intensas, do Ministério da Saúde (2017)"


# 1. Páginas saem da citação; o nome do documento fica
def test_tirar_paginas_mantem_o_documento():
    assert tirar_paginas(f"Desligue a energia.{CITACAO}, p. 11-12.") == f"Desligue a energia.{CITACAO}."
    assert tirar_paginas(f"Procure o posto.{CITACAO}, p. 74.") == f"Procure o posto.{CITACAO}."
    sem = f"Desligue a energia.{CITACAO}."
    assert tirar_paginas(sem) == sem and tirar_paginas(tirar_paginas(sem)) == sem     # idempotente


def test_tirar_paginas_so_mexe_na_citacao():
    texto = "Veja o quadro da p. 12 do plano antes de sair."      # "p. " fora da citação não é tocado
    assert tirar_paginas(texto) == texto


# 2. Formatação mantém os campos e a ordem do formato entregue
def test_formatar_qa_e_chat():
    linha = formatar_qa(qa("Como me proteger da enchente?", f"Saia para um local seguro.{CITACAO}, p. 3-4."))
    assert list(linha) == ["instruction", "input", "output", "fonte", "segmento_id"]
    assert linha["output"].endswith("(2017).")
    dialogo = formatar_chat(chat(["A água está subindo, o que faço?", "Saia de casa.",
                                  "E depois?", f"Volte só com autorização.{CITACAO}, p. 9."]))
    assert list(dialogo) == ["messages", "fonte", "tipo", "segmento_id"]
    assert dialogo["messages"][-1]["content"].endswith("(2017).") and dialogo["messages"][0]["role"] == "system"


# 3. Validação: formato, ordem das falas e duplicatas sem acento/pontuação
def test_conferir_formato_e_duplicata():
    assert conferir_formato(qa("Curta?", "ok"), "qa") == "pergunta ou resposta curta"
    fora_de_ordem = chat(["Pergunta do morador sobre a chuva", "Resposta", "Outra", "Resposta"])
    fora_de_ordem["messages"][2]["role"] = "user"
    assert conferir_formato(fora_de_ordem, "chat") == "menos de 2 trocas ou falas fora de ordem"
    a, b = qa("O que é enchente?", "x" * 20), qa("o que e  enchente", "y" * 20)
    assert chave_duplicata(a, "qa") == chave_duplicata(b, "qa")


# 4. Recusa com marcador no lugar da pergunta não conta para o mínimo
def test_recusa_com_marcador_nao_e_valida():
    assert not recusa_valida(chat(["pedido inicial", "Não posso diagnosticar. Procure a unidade de saúde.",
                                   "Tá bom", "Procure a unidade de saúde."], tipo="recusa", fonte="recusa", seg=""))
    assert recusa_valida(chat(["Estou com febre depois da enchente, é leptospirose?", "Procure a unidade de saúde.",
                               "Obrigado", "Procure a unidade de saúde."], tipo="recusa", fonte="recusa", seg=""))


# 5. Finalização: grava na própria pasta, sem páginas, e preserva os campos da revisão humana
def test_finalizar_grava_sem_paginas_e_preserva_revisao(tmp_path):
    respostas = [qa(f"Pergunta número {i} sobre a enchente?", f"Resposta número {i} do trecho.{CITACAO}, p. {i}.")
                 for i in range(1, 4)]
    respostas.append(qa("Pergunta número 1 sobre a enchente", "Repetida, deve sair."))     # duplicata
    dialogos = [chat(["A água está subindo, o que faço?", "Saia de casa.", "E a energia?",
                      f"Desligue a energia.{CITACAO}, p. 5."]),
                chat(["pedido inicial", "Não posso ajudar. Procure a Defensoria Pública.", "Certo",
                      "Procure a Defensoria Pública."], tipo="recusa", fonte="recusa", seg="")]
    for nome, itens in (("corpus_qa.jsonl", respostas), ("corpus_chat.jsonl", dialogos)):
        (tmp_path / nome).write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in itens), encoding="utf-8")
    (tmp_path / "estatisticas.json").write_text(json.dumps(
        {"revisora_humana": "Sarah", "qa": {"duplicatas_removidas": 15}}), encoding="utf-8")
    segmentos = [Segmento(id="ms_2017_cartilha_alerta_chuvas_0001", fonte="ms_2017_cartilha_alerta_chuvas.pdf",
                          tipo="pdf", paginas=[1], texto="Durante a enchente, desligue a energia elétrica da casa.")]

    m = finalizar(tmp_path, segmentos=segmentos)

    assert m["qa"]["quantidade"] == 3 and m["qa"]["duplicatas_removidas"] == 1
    assert m["paginas_removidas"] == {"qa": 3, "chat": 1} and m["respostas_com_paginas"] == 0
    assert m["recusas"] == 1 and m["recusas_validas"] == 0 and not m["recusas_atingidas"]
    gravado = [json.loads(l) for l in (tmp_path / "corpus_qa.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all("p. " not in e["output"] for e in gravado)
    texto = json.loads((tmp_path / "corpus_texto.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert texto == {"text": segmentos[0].texto, "fonte": segmentos[0].fonte, "segmento_id": segmentos[0].id}
    estat = json.loads((tmp_path / "estatisticas.json").read_text(encoding="utf-8"))
    assert estat["revisora_humana"] == "Sarah" and estat["qa"]["duplicatas_removidas"] == 15   # preservados
    assert estat["qa"]["quantidade"] == 3 and estat["finalizacao"]["qa"]["duplicatas_removidas"] == 1
    assert (tmp_path / "amostras_5_por_corpus.json").exists()

    # rodar de novo dá o mesmo resultado
    antes = (tmp_path / "corpus_qa.jsonl").read_text(encoding="utf-8")
    finalizar(tmp_path, segmentos=segmentos)
    assert (tmp_path / "corpus_qa.jsonl").read_text(encoding="utf-8") == antes


# 6. Segmentação mudou: o exemplo passa a apontar para o segmento com o mesmo conteúdo
def test_finalizar_remapeia_segmento_deslocado(tmp_path):
    base = "mcid_2026_mapeamento_riscos"
    antigo = [{"text": "Capa e referências que a limpeza nova remove.", "fonte": f"{base}.pdf", "segmento_id": f"{base}_0001"},
              {"text": "Enxurradas acontecem quando a água corre rápido pelas ruas íngremes.", "fonte": f"{base}.pdf",
               "segmento_id": f"{base}_0002"}]
    (tmp_path / "corpus_texto.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in antigo),
                                                 encoding="utf-8")
    pergunta = qa("O que é uma enxurrada na cidade?", "É a água que corre rápido pelas ruas íngremes.",
                  fonte=f"{base}.pdf", seg=f"{base}_0002")
    (tmp_path / "corpus_qa.jsonl").write_text(json.dumps(pergunta, ensure_ascii=False) + "\n", encoding="utf-8")
    (tmp_path / "corpus_chat.jsonl").write_text("", encoding="utf-8")
    novos = [Segmento(id=f"{base}_0001", fonte=f"{base}.pdf", tipo="pdf", paginas=[2],
                      texto="Enxurradas acontecem quando a água corre rápido pelas ruas íngremes.")]

    m = finalizar(tmp_path, segmentos=novos)

    assert m["segmento_id_remapeados"] == {f"{base}_0002": f"{base}_0001"}
    gravado = json.loads((tmp_path / "corpus_qa.jsonl").read_text(encoding="utf-8"))
    assert gravado["segmento_id"] == f"{base}_0001"
