# Radar Cidadão - Fábrica de Corpus CitizenTech (FIAP)

Entrega consolidada dos corpus e da revisão humana. Os dados são educacionais e não constituem serviço operacional de emergência.

## Integrantes

- Mario Antônio de Oliveira - RM 567713
- Sarah Marangoni Furlan - RM 566764
- Vinicius Augusto Silva - RM 566830

**Revisão humana da amostra:** Sarah Marangoni Furlan (RM 566764). A correção técnica posterior e a reformulação dos comentários foram assistidas por IA e estão identificadas no histórico.

## Arquivos

- `corpus_texto.jsonl`: 306 segmentos com identificadores e fontes.
- `corpus_qa.jsonl`: 100 pares de perguntas/respostas únicos.
- `corpus_chat.jsonl`: 31 diálogos com no mínimo duas respostas do assistente; 11 recusas marcadas.
- `estatisticas.json`: métricas, quantidades e limitações metodológicas.
- `revisao_humana_20_porcento.csv` e `.xlsx`: avaliação humana original preservada em coluna separada do parecer técnico atualizado.
- `RELATORIO_REVISAO_HUMANA.pdf`: resultado da auditoria com comentários editados tecnicamente.
- `RELATORIO_FINAL_GS_Radar_Cidadao.pdf`: relatório acadêmico consolidado.
- `REGISTRO_DA_REVISAO.md` e `REGISTRO_AJUSTES_EDITORIAIS.csv`: rastreabilidade das alterações.
- `revisao_humana_MARCACOES_RECEBIDAS.pdf`: prova da avaliação original enviada.
- `ROTEIRO_VIDEO_5_MIN.md`: roteiro para a demonstração.

## Fontes

As fontes são documentos públicos sobre enchentes, chuvas intensas e mapeamento de riscos, identificados nos campos `fonte` e `segmento_id` dos JSONL. Incluem publicações do Ministério das Cidades (2024, 2026) e do Ministério da Saúde (2017, 2025, 2026).

## Reprodutibilidade

O projeto utiliza Python, extração/limpeza de documentos, segmentação, geração assistida por LLM e regras de filtragem. Para reproduzir a execução, consulte os notebooks na pasta `notebooks/`. Os corpora aqui entregues são as versões revisadas e consolidadas, não arquivos recém-gerados durante este empacotamento.

## Limitações

A revisão humana da amostra foi realizada. Os pareceres técnicos da IA fundamentam-se nos **segmentos armazenados no corpus**; não substituem conferência independente da paginação física dos PDFs originais. O vídeo de demonstração precisa ser gravado/anexado pelo grupo. Não coloque tokens, dados pessoais ou credenciais no repositório.
