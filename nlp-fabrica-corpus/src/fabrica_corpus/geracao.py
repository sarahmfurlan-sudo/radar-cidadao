"""Etapa 7 da Fábrica de Corpus: geração das perguntas e dos diálogos.

Um modelo aberto da família Qwen, rodando na GPU do Colab, lê um segmento real
e escreve perguntas e respostas (corpus_qa) e diálogos (corpus_chat) SOMENTE
com o que está no segmento. Cada exemplo guarda a fonte, as páginas e o id do
segmento de origem.

Travas contra invenção (cada exemplo passa por todas, senão é refeito; depois
de 3 tentativas, o segmento é pulado e contado no relatório):
 1. a saída tem que ser um JSON no formato pedido;
 2. todo número citado na resposta (telefone, prazo, quantidade) tem que estar
    no segmento, salvo os números de emergência;
 3. filtro grosseiro: pelo menos 25% das palavras importantes da resposta têm que
    estar no segmento, comparadas pelo radical (as 5 primeiras letras); o corte é
    só interno à trava e não altera o texto do corpus;
 4. nada de marcações da anonimização ([NOME] etc.) nem de nomes inventados;
 5. nada de falar "do trecho" ou "disso aqui", como se o leitor visse o documento;
 6. juiz: o próprio modelo relê cada par com o trecho e confere se a resposta está
    apoiada no trecho (sem acrescentar nada), se responde a pergunta e se quem age
    é o mesmo nos dois.

Cache: cada resposta do modelo é guardada em dados/cache_geracao/, com a versão
do prompt no nome. Rodar de novo (no vídeo ou na correção) reaproveita tudo e
leva segundos; só o que mudou é gerado outra vez.

O modelo é "plugável": gerar_qa e gerar_chat recebem uma função
gerar(mensagens) -> texto. No Colab, ela vem de carregar_qwen(); nos testes,
de um gerador falso. Assim a lógica é testada sem GPU.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Callable, Iterable

MODELO_GERADOR = "Qwen/Qwen2.5-14B-Instruct"  # 14B em 4 bits: segue melhor as regras (o 7B confundia quem age)
VERSAO_PROMPT = "v8_1"   # v8: geração em etapas (extração de fatos com quem age, depois perguntas e diálogos a partir dos fatos)
EMERGENCIA = {"190", "192", "193", "199", "40199", "156"}

# Título legível de cada documento, para o assistente citar a fonte na resposta
# ("Segundo a Cartilha do Ministério da Saúde (2017), ...") em vez do nome do arquivo.
TITULOS = {
    "mcid_2026_mapeamento_riscos.pdf": "Mapeamento de Riscos, do Ministério das Cidades (2026)",
    "ms_2025_plano_contingencia_chuvas.pdf": "Plano de Contingência para Chuvas Intensas, do Ministério da Saúde (2025)",
    "mcid_2024_periferia_sem_risco.pdf": "Periferia Sem Risco, do Ministério das Cidades (2024)",
    "ms_2017_cartilha_alerta_chuvas.pdf": "Cartilha de Alerta de Chuvas Intensas, do Ministério da Saúde (2017)",
    "ms_2026_enchentes.html": "página Enchentes, do Ministério da Saúde",
    "mdr_2021_guia_alertas_desastres.pdf": "Guia Prático de Alertas, do Ministério do Desenvolvimento Regional (2021)",
    "mi_2003_manual_desastres_naturais.pdf": "Manual de Desastres Naturais, do Ministério da Integração Nacional (2003)",
    "pmsp_2024_chuvas_excessivas.pdf": "orientações da Defesa Civil da Prefeitura de São Paulo (2024)",
    "cgesp_2026_dicas_alagamentos.docx": "dicas do CGE da Prefeitura de São Paulo",
}


def titulo(fonte: str) -> str:
    return TITULOS.get(fonte, fonte)


def citacao(fonte: str, paginas: list) -> str:
    """Citação da fonte, acrescentada pelo código no fim das respostas.

    O modelo não cita de forma confiável (no teste de 13/11 ignorou o pedido),
    então a citação é garantida aqui, sempre no mesmo formato:
    "Fonte: Periferia Sem Risco, do Ministério das Cidades (2024), p. 7-9."
    """
    paginas = paginas or []
    if not paginas:
        return f"Fonte: {titulo(fonte)}."
    pags = f"p. {paginas[0]}" if len(paginas) == 1 else f"p. {paginas[0]}-{paginas[-1]}"
    return f"Fonte: {titulo(fonte)}, {pags}."
TENTATIVAS = 3

PERSONA_ASSISTENTE = (
    "Você é o assistente do Radar Cidadão, um app que orienta moradores de áreas sujeitas "
    "a alagamento e deslizamento. Fale de forma acolhedora, direta e com frases curtas. "
    "Responda SOMENTE com base no trecho oficial fornecido, citando a fonte; não acrescente "
    "nada que não esteja nele. Em situação de risco imediato, oriente primeiro a ligar para a Defesa "
    "Civil (199) ou os Bombeiros (193). Se o trecho não traz a resposta, diga que não sabe."
)
# No prompt de geração, a persona vai sem o "citando a fonte": a citação é colocada
# pelo código depois, e pedir ao modelo geraria citação duplicada.
PERSONA_GERACAO = PERSONA_ASSISTENTE.replace(", citando a fonte", "")

# Na geração, o cidadão NÃO recebe a lista de assuntos (antes/durante/depois, limpeza,
# doenças): com ela, o modelo fazia o cidadão perguntar sobre limpeza e doenças em trechos
# que não falam disso, e respondia com conhecimento próprio (o juiz pegou em 13/11).
PERSONA_CIDADAO_GERACAO = (
    "O cidadão mora em bairro de periferia, em área de risco, usa o celular e fala de forma "
    "simples, às vezes com pressa ou medo. Ele SÓ pergunta sobre o que o trecho oficial explica."
)

PERSONA_CIDADAO = (
