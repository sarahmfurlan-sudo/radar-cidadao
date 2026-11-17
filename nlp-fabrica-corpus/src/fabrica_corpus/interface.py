"""Interface Gradio da Fábrica de Corpus (usada no notebook do Colab).

Duas abas:
 1. "Processar documento": envio de PDF, TXT, DOCX ou HTML (vários arquivos) ou texto
    colado; mostra o resultado de cada etapa (extração com a fonte, limpeza,
    anonimização e segmentação) e devolve o corpus_texto daquele envio em JSONL.
 2. "Corpus finais": estatísticas, 5 exemplos aleatórios de cada corpus e download
    dos 3 JSONL da entrega-final.

A lógica fica em funções comuns (processar, resumo_corpus, exemplos_corpus), testadas
sem o Gradio; criar_app só monta a tela.
"""
from __future__ import annotations

import json
import random
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from .anonimizacao import anonimizar_corpus
from .exportacao import gravar_jsonl, linha_texto
from .finalizacao import ENTREGA, ler_jsonl, recusa_valida
from .ingestao import EXTENSOES_ACEITAS, extrair_arquivo, extrair_texto_colado
from .limpeza import limpar_corpus
from .segmentacao import segmentar

AVISO_CORPUS = ("As perguntas e os diálogos vêm da versão revisada (geração com o Qwen2.5-14B-Instruct no Colab, "
                "revisão humana e finalização). A geração com o Qwen é opcional e precisa de GPU; "
                "o notebook não gera de novo.")


def _celula(texto, limite: int = 160) -> str:
    """Texto curto e seguro para uma célula de tabela em Markdown."""
    t = " ".join(str(texto).split())
    t = t if len(t) <= limite else t[:limite] + "…"
    return t.replace("|", "/")


def _tabela(cabecalho: list[str], linhas: Iterable[list]) -> str:
    md = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    md += ["| " + " | ".join(_celula(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(md)


def _caminho(arquivo) -> Path:
    """O Gradio entrega caminhos (str) ou objetos com .name, conforme a versão."""
    return Path(getattr(arquivo, "name", arquivo))


# ------------------------------------------------------------ aba 1: processar documento
def processar(arquivos: list | None, texto_colado: str = "", contar: Callable[[str], int] | None = None,
              pasta_saida: str | Path | None = None) -> dict:
    """Roda extração, limpeza, anonimização e segmentação no que foi enviado.

    Devolve {"extracao", "limpeza", "anonimizacao", "segmentacao"} em Markdown e
    "jsonl" com o caminho do corpus_texto deste envio (ou None se não houve texto)."""
    trechos, avisos = [], []
    for arquivo in arquivos or []:
        caminho = _caminho(arquivo)
        if caminho.suffix.lower() not in EXTENSOES_ACEITAS:
            avisos.append(f"`{caminho.name}`: formato não aceito (use PDF, TXT, DOCX ou HTML).")
            continue
        try:
            novos = extrair_arquivo(caminho)
        except Exception as erro:                       # arquivo corrompido não derruba o envio
            avisos.append(f"`{caminho.name}`: não foi possível ler ({erro}).")
            continue
        if not novos:
            avisos.append(f"`{caminho.name}`: nenhum texto extraído (PDF só com imagem?).")
        trechos += novos
    if texto_colado and texto_colado.strip():
        trechos += extrair_texto_colado(texto_colado)

    vazio = {"extracao": "\n\n".join(avisos) or "Envie um arquivo ou cole um texto.",
             "limpeza": "", "anonimizacao": "", "segmentacao": "", "jsonl": None}
    if not trechos:
        return vazio

    extracao = _tabela(["Fonte", "Tipo", "Página", "Caracteres", "Início do texto"],
                       [[t.fonte, t.tipo, t.pagina or "-", len(t.texto), t.texto] for t in trechos])
    extracao = (f"**{len(trechos)} trecho(s) extraído(s)**, cada um com o arquivo de origem.\n\n" + extracao
                + ("\n\n" + "\n\n".join(avisos) if avisos else ""))

    limpos, est_l = limpar_corpus(trechos)
    antes, depois = trechos[0].texto, (limpos[0].texto if limpos else "")
    limpeza = (f"Caracteres: {est_l['caracteres_antes']} -> {est_l['caracteres_depois']} | "
               f"trechos vazios descartados: {est_l['trechos_vazios_descartados']} | "
               f"linhas de referência removidas: {est_l['linhas_de_referencia_removidas']} | "
               f"cabeçalhos/rodapés repetidos: {sum(est_l['repetidas_por_documento'].values())}\n\n"
               f"**Primeiro trecho, antes:**\n\n```\n{antes[:700]}\n```\n\n**Depois:**\n\n```\n{depois[:700]}\n```")
    if not limpos:
        vazio.update(extracao=extracao, limpeza=limpeza)
        return vazio

    anonimos, est_a = anonimizar_corpus(limpos)
    anonimizacao = (_tabela(["Nome", "CPF", "E-mail", "Telefone", "Citação (autor)"],
                            [[est_a["nome"], est_a["cpf"], est_a["email"], est_a["telefone"], est_a["citacao"]]])
                    + "\n\nNúmeros de emergência (190, 192, 193, 199, 40199) e o 156 são preservados.\n\n"
                    f"**Primeiro trecho anonimizado:**\n\n```\n{anonimos[0].texto[:900]}\n```")

    segmentos, est_s = segmentar(anonimos, contar)
    segmentacao = (f"**{est_s['segmentos']} segmento(s)** | média de {est_s['tokens_media']} tokens "
                   f"(mín. {est_s['tokens_min']}, máx. {est_s['tokens_max']}) | "
                   f"segmentos curtos (< 256 tokens): {est_s['segmentos_curtos']}\n\n"
                   + _tabela(["segmento_id", "Fonte", "Páginas", "Tokens", "Início do texto"],
                             [[s.id, s.fonte, ", ".join(map(str, s.paginas)) or "-", s.tokens, s.texto]
                              for s in segmentos]))

    pasta = Path(pasta_saida) if pasta_saida else Path(tempfile.mkdtemp(prefix="fabrica_corpus_"))
    jsonl = pasta / "corpus_texto.jsonl"
    gravar_jsonl((linha_texto(s) for s in segmentos), jsonl)
    return {"extracao": extracao, "limpeza": limpeza, "anonimizacao": anonimizacao,
            "segmentacao": segmentacao, "jsonl": str(jsonl)}


# ------------------------------------------------------------ aba 2: corpus finais
def arquivos_corpus(pasta: str | Path = ENTREGA) -> list[str]:
    return [str(Path(pasta) / f"corpus_{t}.jsonl") for t in ("texto", "qa", "chat")]


def resumo_corpus(pasta: str | Path = ENTREGA) -> str:
    pasta = Path(pasta)
    est = json.loads((pasta / "estatisticas.json").read_text(encoding="utf-8"))
    chat = ler_jsonl(pasta / "corpus_chat.jsonl")
    linhas = [[f"corpus_{t}.jsonl", est[t]["quantidade"], est[t]["minimo"], est[t]["media_tokens_aprox"],
               est[t].get("duplicatas_removidas", 0)] for t in ("texto", "qa", "chat")]
    md = [AVISO_CORPUS, "",
          _tabela(["Arquivo", "Exemplos", "Mínimo", "Média de tokens (aprox.)", "Duplicatas removidas"], linhas), "",
          f"**Recusas válidas:** {sum(map(recusa_valida, chat))} (mínimo 10)"]
    if "amostra_humana" in est:
        a = est["amostra_humana"]
        md.append(f"**Revisão humana:** {est.get('revisora_humana', '')}; {a['exemplos']} exemplos "
                  f"({a['percentual_dos_131']}%): {a['marcacoes_s']} S e {a['marcacoes_n']} N.")
    return "\n\n".join(md)


def exemplos_corpus(pasta: str | Path = ENTREGA, semente: int | None = 2026, n: int = 5) -> str:
    pasta, rng = Path(pasta), random.Random(semente)
    md = []
    texto = ler_jsonl(pasta / "corpus_texto.jsonl")
    md.append("### corpus_texto\n\n" + _tabela(["segmento_id", "Fonte", "Texto"],
                                                 [[e["segmento_id"], e["fonte"], e["text"]]
                                                  for e in rng.sample(texto, min(n, len(texto)))]))
    qa = ler_jsonl(pasta / "corpus_qa.jsonl")
    md.append("### corpus_qa\n\n" + _tabela(["Pergunta (instruction)", "Resposta (output)", "Fonte"],
                                              [[e["instruction"], e["output"], e["fonte"]]
                                               for e in rng.sample(qa, min(n, len(qa)))], ))
    chat = ler_jsonl(pasta / "corpus_chat.jsonl")
    blocos = []
    for e in rng.sample(chat, min(n, len(chat))):
        falas = "\n".join(f"- **{m['role']}:** {' '.join(m['content'].split())}"
                          for m in e["messages"] if m["role"] != "system")
        blocos.append(f"**{e['tipo']}** | fonte `{e['fonte']}`\n\n{falas}")
    md.append("### corpus_chat\n\n" + "\n\n---\n\n".join(blocos))
    return "\n\n".join(md)


# ------------------------------------------------------------ tela
def criar_app(pasta: str | Path = ENTREGA, contar: Callable[[str], int] | None = None):
    import gradio as gr

    def _processar(arquivos, texto):
        r = processar(arquivos, texto, contar)
        return r["extracao"], r["limpeza"], r["anonimizacao"], r["segmentacao"], r["jsonl"]

    with gr.Blocks(title="Fábrica de Corpus: Radar Cidadão") as app:
        gr.Markdown("# Fábrica de Corpus: Radar Cidadão\nDocumentos públicos sobre chuvas, alagamentos e "
                    "deslizamentos transformados em corpus JSONL para treinar um modelo que orienta o cidadão.")
        with gr.Tab("Processar documento"):
            arquivos = gr.File(label="Documentos (PDF, TXT, DOCX ou HTML)", file_count="multiple",
                               file_types=[".pdf", ".txt", ".docx", ".html", ".htm"])
            texto = gr.Textbox(label="Ou cole um texto", lines=5)
            botao = gr.Button("Processar", variant="primary")
            with gr.Accordion("1. Extração (com a fonte)", open=True):
                s_extracao = gr.Markdown()
            with gr.Accordion("2. Limpeza e normalização", open=False):
                s_limpeza = gr.Markdown()
            with gr.Accordion("3. Anonimização", open=False):
                s_anon = gr.Markdown()
            with gr.Accordion("4. Segmentação (256 a 512 tokens)", open=False):
                s_seg = gr.Markdown()
            s_jsonl = gr.File(label="corpus_texto.jsonl deste envio")
            botao.click(_processar, [arquivos, texto], [s_extracao, s_limpeza, s_anon, s_seg, s_jsonl])
        with gr.Tab("Corpus finais"):
            gr.Markdown(resumo_corpus(pasta))
            gr.File(value=arquivos_corpus(pasta), label="Corpus da entrega-final", file_count="multiple")
            sortear = gr.Button("Sortear outros 5 exemplos")
            s_exemplos = gr.Markdown(exemplos_corpus(pasta))
            sortear.click(lambda: exemplos_corpus(pasta, semente=None), None, s_exemplos)
    return app
