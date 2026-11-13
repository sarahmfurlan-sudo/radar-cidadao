"""Testes da segmentação. Usam um contador simples (1 palavra = 1 token) para
não depender de baixar o tokenizador do Qwen; a lógica de corte é a mesma."""
from fabrica_corpus.ingestao import Trecho
from fabrica_corpus.segmentacao import MAXIMO, MINIMO, dividir_frases, segmentar


def contar(texto: str) -> int:
    return len(texto.split())


def frase(n: int, palavras: int = 20) -> str:
    return "Frase " + " ".join(["palavra"] * (palavras - 2)) + f" fim{n}."


def pdf(fonte: str, paginas: dict[int, str]):
    return [Trecho(fonte=fonte, tipo="pdf", pagina=p, texto=t) for p, t in paginas.items()]


def test_tamanho_entre_256_e_512_e_corte_em_fim_de_frase():
    texto = " ".join(frase(i) for i in range(100))          # 2.000 "tokens"
    segs, estat = segmentar(pdf("doc.pdf", {1: texto}), contar)
    assert all(MINIMO <= s.tokens <= MAXIMO for s in segs)
    assert all(s.texto.endswith(".") for s in segs)
    assert estat["segmentos_curtos"] == 0


def test_nada_se_perde_nem_se_repete():
    frases = [frase(i) for i in range(60)]
    segs, _ = segmentar(pdf("doc.pdf", {1: " ".join(frases[:30]), 2: " ".join(frases[30:])}), contar)
    assert " ".join(s.texto for s in segs) == " ".join(frases)


def test_segmento_atravessa_paginas_e_guarda_todas():
    p1 = " ".join(frase(i) for i in range(10))               # 200
    p2 = " ".join(frase(i) for i in range(10, 20))           # 200
    segs, _ = segmentar(pdf("doc.pdf", {2: p2, 1: p1}), contar)   # fora de ordem de propósito
    assert len(segs) == 1 and segs[0].paginas == [1, 2]
    assert segs[0].texto.startswith(frase(0))


def test_documentos_nunca_se_misturam():
    a = pdf("a.pdf", {1: " ".join(frase(i) for i in range(5))})
    b = [Trecho(fonte="b.txt", tipo="txt", pagina=None, texto=" ".join(frase(i) for i in range(5)))]
    segs, estat = segmentar(a + b, contar)
    assert {s.fonte for s in segs} == {"a.pdf", "b.txt"}
    assert estat["segmentos_por_fonte"] == {"a.pdf": 1, "b.txt": 1}
    assert next(s for s in segs if s.fonte == "b.txt").paginas == []


def test_documento_curto_vira_segmento_curto_contado():
    segs, estat = segmentar([Trecho(fonte="dicas.docx", tipo="docx", pagina=None, texto=frase(1))], contar)
    assert len(segs) == 1 and estat["segmentos_curtos"] == 1


def test_sobra_curta_no_fim_junta_ao_anterior_quando_cabe():
    # 400 + 60: a sobra de 60 cabe no anterior (460 <= 512)
    texto = " ".join(frase(i) for i in range(23))            # 460
    segs, _ = segmentar(pdf("doc.pdf", {1: texto}), contar)
    assert len(segs) == 1 and segs[0].tokens == 460


def test_frase_gigante_e_cortada_por_palavras():
    gigante = " ".join(["célula"] * 1200) + "."             # tabela achatada sem pontuação
    segs, _ = segmentar(pdf("tab.pdf", {1: gigante}), contar)
    assert all(s.tokens <= MAXIMO for s in segs)
    assert sum(s.tokens for s in segs) == 1200


def test_ids_unicos_por_documento():
    texto = " ".join(frase(i) for i in range(80))
    segs, _ = segmentar(pdf("mcid_2026_mapeamento_riscos.pdf", {1: texto}), contar)
    ids = [s.id for s in segs]
    assert len(ids) == len(set(ids)) and ids[0] == "mcid_2026_mapeamento_riscos_0001"


def test_divisao_em_frases_respeita_abreviacoes():
    texto = "Conforme o art. 5 da lei, o Sr. Silva saiu. Veja p. 12 e Souza et al. 2020. Fim."
    assert dividir_frases(texto) == [
        "Conforme o art. 5 da lei, o Sr. Silva saiu.", "Veja p. 12 e Souza et al. 2020.", "Fim."]


def test_marcacoes_da_anonimizacao_nao_quebram_frase():
    texto = "A moradora [NOME] ligou para 199. O vizinho [NOME] enviou fotos."
    assert dividir_frases(texto) == ["A moradora [NOME] ligou para 199.", "O vizinho [NOME] enviou fotos."]
