# Radar Cidadão - Fábrica de Corpus CitizenTech (FIAP)

Entrega consolidada dos corpus e da revisão humana. Os dados são educacionais e não constituem serviço operacional de emergência.

## Integrantes

- Mario Antônio de Oliveira - RM 567713
- Sarah Marangoni Furlan - RM 566764
- Vinicius Augusto Silva - RM 566830

**Revisão humana da amostra:** Sarah Marangoni Furlan (RM 566764). A correção técnica posterior e a reformulação dos comentários foram assistidas por IA e estão identificadas no histórico.

## Arquivos

- `corpus_texto.jsonl`: 307 segmentos (`text`, `fonte`, `segmento_id`).
- `corpus_qa.jsonl`: 100 pares de perguntas/respostas únicos (`instruction`, `input`, `output`, `fonte`, `segmento_id`).
- `corpus_chat.jsonl`: 31 diálogos com no mínimo duas trocas (`messages`, `fonte`, `tipo`, `segmento_id`); 11 recusas válidas.
- `estatisticas.json`: quantidades, médias de tokens, duplicatas, recusas válidas e dados da revisão humana.
- `revisao_humana_20_porcento.csv` e `.xlsx`: avaliação humana original (marcação e comentário da revisora) em colunas separadas do parecer técnico.
- `RELATORIO_FINAL_GS_Radar_Cidadao.pdf`: relatório acadêmico consolidado.
- `REGISTRO_AJUSTES_EDITORIAIS.csv`: cada alteração feita nos exemplos depois da geração (antes, depois e motivo).
- `revisao_humana_MARCACOES_RECEBIDAS.pdf`: prova da avaliação original enviada.
- `ROTEIRO_VIDEO_5_MIN.md`: roteiro para a demonstração.

## Fontes

As fontes são documentos públicos sobre enchentes, chuvas intensas e mapeamento de riscos, identificados nos campos `fonte` e `segmento_id` dos JSONL. Incluem publicações do Ministério das Cidades (2024, 2026) e do Ministério da Saúde (2017, 2025, 2026).

## Reprodutibilidade

O projeto utiliza Python, extração/limpeza de documentos, segmentação, geração assistida por LLM e regras de filtragem. A geração das perguntas e dos diálogos está nos notebooks da pasta `notebooks/`. Fluxo: geração (Qwen no Colab) -> revisão humana -> finalização. A finalização (`src/fabrica_corpus/finalizacao.py`) refaz o `corpus_texto` pelo pipeline, tira as páginas das citações, valida e grava os corpus revisados, sem chamar o modelo de novo.

## Limitações

A revisão humana da amostra foi realizada. Os pareceres técnicos da IA fundamentam-se nos **segmentos armazenados no corpus**; não substituem conferência independente da paginação física dos PDFs originais. Não coloque tokens, dados pessoais ou credenciais no repositório.
