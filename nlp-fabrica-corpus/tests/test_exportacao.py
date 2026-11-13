"""Testes da exportação dos corpus JSONL (sem GPU e sem modelo)."""
import json

import pytest

import fabrica_corpus.geracao as geracao
from fabrica_corpus.exportacao import (
    CacheIncompleto, exportar_qa_chat, exportar_rag, exportar_texto, gerar_perguntas_e_dialogos,
    gravar_jsonl, linha_chat, linha_qa, preparar_segmentos, remover_duplicatas, sem_modelo,
)
from fabrica_corpus.segmentacao import Segmento


@pytest.fixture(autouse=True)
def geracao_simples(monkeypatch):
    """Gerador falso não sabe fazer fatos nem juiz: testa a exportação, não a geração."""
    monkeypatch.setattr(geracao, "USAR_JUIZ", False)
    monkeypatch.setattr(geracao, "USAR_FATOS", False)


TEXTO = ("Durante a enchente, não atravesse ruas alagadas, pois a correnteza pode arrastar você. "
         "Desligue a energia elétrica da casa antes que a água chegue às tomadas. "
         "Em caso de risco, ligue para a Defesa Civil no 199. A água da enchente pode transmitir leptospirose.")


def seg(i, fonte="ms_2017_cartilha_alerta_chuvas.pdf", texto=TEXTO):
    return Segmento(id=f"seg_{i:04d}", fonte=fonte, tipo="pdf", paginas=[i], texto=f"{texto} Parte {i}.", tokens=300)


def gerador_falso(mensagens):
    prompt = mensagens[0]["content"]
    n = prompt.split("Parte ")[1].split(".")[0]      # pergunta diferente por segmento
    return json.dumps({
        "perguntas": [
            {"pergunta": f"Posso atravessar a rua alagada? ({n})", "resposta": "Não atravesse ruas alagadas, a correnteza pode arrastar você."},
            {"pergunta": f"O que faço com a energia elétrica? ({n})", "resposta": "Desligue a energia elétrica da casa antes que a água chegue às tomadas."}],
        "mensagens": [
            {"papel": "cidadao", "texto": f"A água está subindo, o que eu faço? ({n})"},
            {"papel": "assistente", "texto": "Em caso de risco, ligue para a Defesa Civil no 199."},
            {"papel": "cidadao", "texto": "E a energia?"},
            {"papel": "assistente", "texto": "Desligue a energia elétrica da casa antes que a água chegue às tomadas."}]})


def ler(caminho):
    texto = caminho.read_text(encoding="utf-8")
    return texto, [json.loads(l) for l in texto.splitlines()]


# 1. Duplicatas: espaços e caixa não contam
def test_remover_duplicatas_normaliza_espacos_e_caixa():
    itens = ["Ligue para o 199.", "ligue  para o\n199.", "LIGUE PARA O 199.", "Saia de casa."]
    unicos, removidos = remover_duplicatas(itens, lambda x: x)
    assert unicos == ["Ligue para o 199.", "Saia de casa."] and removidos == 2


# 2. Gravação: UTF-8, um JSON por linha, acentos sem escape
def test_gravar_jsonl_utf8_uma_linha_por_objeto(tmp_path):
    caminho = tmp_path / "x.jsonl"
    assert gravar_jsonl([{"texto": "água e lama"}, {"texto": "Defesa Civil: 199"}], caminho) == 2
    bruto, linhas = ler(caminho)
    assert "água" in bruto and "\\u" not in bruto
    assert len(bruto.splitlines()) == 2 and linhas[1]["texto"] == "Defesa Civil: 199"


# 3. Formato das perguntas: instruction / input / output
def test_linha_qa_no_formato_do_enunciado():
    exemplo = {"id": "qa_0001", "pergunta": "O que é enchente?", "resposta": "É a cheia do rio.\n\nFonte: X, p. 3.",
               "fonte": "a.pdf", "paginas": [3], "segmento_id": "a_0001", "modelo": "m"}
    assert linha_qa(exemplo) == {"instruction": "O que é enchente?", "input": "",
                                 "output": "É a cheia do rio.\n\nFonte: X, p. 3.",
                                 "fonte": "a.pdf", "paginas": [3], "segmento_id": "a_0001"}


# 4. Formato dos diálogos: messages com role/content e system primeiro
def test_linha_chat_no_formato_do_enunciado():
    exemplo = {"mensagens": [{"role": "system", "content": "persona"}, {"role": "user", "content": "oi"},
                             {"role": "assistant", "content": "olá"}],
               "fonte": "a.pdf", "paginas": [3], "segmento_id": "a_0001"}
    linha = linha_chat(exemplo)
    assert list(linha) == ["messages", "fonte", "paginas", "segmento_id"]
    assert [m["role"] for m in linha["messages"]] == ["system", "user", "assistant"]


# 5. Perguntas e diálogos saem do cache, sem chamar o modelo
def test_exportar_qa_chat_do_cache_sem_modelo(tmp_path):
    segs = [seg(i) for i in range(1, 13)]
    cache = tmp_path / "cache"
    qa, chat, _ = gerar_perguntas_e_dialogos(segs, gerador_falso, cache, total_qa=6, total_chat=2)
    assert len(qa) == 6 and len(chat) == 2 and any(cache.iterdir())

    # a exportação usa sem_modelo, que dá erro se for chamado: tudo tem que vir do cache
    estat = exportar_qa_chat(segs, pasta_cache=cache, saida=tmp_path / "saida", total_qa=6, total_chat=2)

    assert estat["qa"] == {"gravados": 6, "duplicatas_removidas": 0}
    assert estat["chat"] == {"gravados": 2, "duplicatas_removidas": 0}
    _, linhas_qa = ler(tmp_path / "saida" / "corpus_qa.jsonl")
    assert set(linhas_qa[0]) == {"instruction", "input", "output", "fonte", "paginas", "segmento_id"}
    assert "\n\nFonte: " in linhas_qa[0]["output"]           # citação já vem na resposta
    _, linhas_chat = ler(tmp_path / "saida" / "corpus_chat.jsonl")
    assert linhas_chat[0]["messages"][0]["role"] == "system"


# 6. Cache vazio: a exportação para em vez de carregar modelo
def test_cache_incompleto_da_erro(tmp_path):
    with pytest.raises(CacheIncompleto):
        gerar_perguntas_e_dialogos([seg(i) for i in range(1, 5)], sem_modelo, tmp_path / "vazio",
                                   total_qa=2, total_chat=1)


# 7. Perguntas repetidas são removidas na exportação
def test_qa_duplicada_removida():
    linhas = [linha_qa({"pergunta": p, "resposta": "r", "fonte": "a", "paginas": [], "segmento_id": "s"})
              for p in ["O que é enchente?", "o que é  enchente?", "O que é alagamento?"]]
    unicos, removidos = remover_duplicatas(linhas, lambda l: l["instruction"])
    assert len(unicos) == 2 and removidos == 1


# 8. corpus_texto e corpus_rag: campos e título legível
def test_texto_e_rag_com_campos_pedidos(tmp_path):
    segs = [seg(1), seg(1), seg(2, fonte="cgesp_2026_dicas_alagamentos.docx")]   # o primeiro repetido
    est_texto = exportar_texto(segs, tmp_path)
    est_rag = exportar_rag(segs, tmp_path)
    assert est_texto == {"gravados": 2, "duplicatas_removidas": 1}
    assert est_rag["gravados"] == 2 and est_rag["duplicatas_removidas"] == 1
    _, texto = ler(tmp_path / "corpus_texto.jsonl")
    assert set(texto[0]) == {"id", "texto", "fonte", "paginas", "tokens"}
    _, rag = ler(tmp_path / "corpus_rag.jsonl")
    assert set(rag[0]) == {"id", "texto", "fonte", "titulo", "paginas", "tokens"}
    assert rag[1]["titulo"] == "dicas do CGE da Prefeitura de São Paulo"


# 9. Preparação de uma pasta: sai segmentado e anonimizado
def test_preparar_segmentos_anonimiza(tmp_path):
    (tmp_path / "relato.txt").write_text(
        "Moradora com CPF 123.456.789-10 e e-mail maria@example.com relatou a rua alagada. "
        "Em caso de risco, ligue para a Defesa Civil no 199.", encoding="utf-8")
    segmentos, estat = preparar_segmentos(tmp_path, contar=lambda t: len(t.split()))
    texto = " ".join(s.texto for s in segmentos)
    assert "123.456.789-10" not in texto and "maria@example.com" not in texto
    assert "[CPF]" in texto and "199" in texto
    assert estat["anonimizacao"]["cpf"] == 1 and segmentos[0].fonte == "relato.txt"
