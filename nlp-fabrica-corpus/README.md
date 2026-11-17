# Fábrica de Corpus: Radar Cidadão

Disciplina de Processamento de Linguagem Natural, Global Solution 2026.2 da FIAP (tema CitizenTech).

A ferramenta transforma documentos públicos sobre chuvas intensas, alagamentos e deslizamentos em três corpus no formato JSONL, prontos para o fine-tuning de um modelo de linguagem pequeno (SLM) que orienta o cidadão. O trabalho cobre a preparação dos dados: coleta, extração, limpeza, normalização, anonimização, segmentação, geração dos corpus e relatório de qualidade.

## Integrantes

| Nome completo | RM |
|---|---|
| Mario Antônio de Oliveira | 567713 |
| Sarah Marangoni Furlan | 566764 |
| Vinicius Augusto Silva | 566830 |

## Como executar no Google Colab

1. Abra o notebook no Colab:
   https://colab.research.google.com/github/sarahmfurlan-sudo/radar-cidadao/blob/main/nlp-fabrica-corpus/fabrica_corpus.ipynb
2. Execute as células em ordem (Ambiente de execução > Executar tudo). Não é preciso GPU nem conta em nenhum serviço.
3. O notebook clona este repositório, instala as dependências do `requirements.txt` e o modelo `pt_core_news_md` do spaCy, e roda o pipeline com os 5 documentos de `dados/entrada`.
4. Na interface Gradio, envie arquivos PDF, TXT, DOCX ou HTML, ou cole um texto, para ver o resultado de cada etapa e baixar o corpus de texto do envio. Os arquivos de `dados/teste` servem para testar a anonimização.

A geração das perguntas e dos diálogos usa o modelo Qwen/Qwen2.5-14B-Instruct e precisa de GPU. Ela já foi feita e revisada, então vem desligada (`RODAR_GERACAO = False`) e o notebook usa os corpus revisados de `entrega-final`. Para gerar de novo, ative a GPU no Colab e mude a opção para `True`.

Para rodar os testes localmente: `python -m pytest -q` dentro de `nlp-fabrica-corpus`.

## Bibliotecas principais

A lista completa, com versões, está em `requirements.txt`.

| Biblioteca | Uso |
|---|---|
| pypdf | Extração de texto de PDF |
| python-docx | Extração de DOCX, incluindo tabelas |
| beautifulsoup4 | Extração de HTML |
| spaCy (`pt_core_news_md`) | Detecção de nomes de pessoas na anonimização |
| transformers | Tokenizador do Qwen 2.5 (contagem de tokens) e geração |
| bitsandbytes, accelerate, torch | Execução do Qwen quantizado em 4 bits na GPU (o torch já vem instalado no Colab; não está no `requirements.txt`) |
| gradio | Interface |
| pytest | Testes automatizados |

## Documentos de entrada

Ficam em `dados/entrada`. São as versões dos links oficiais, conferidas por hash e ISBN.

| Arquivo | Documento | Órgão | Ano | ISBN | Link oficial |
|---|---|---|---|---|---|
| `mcid_2026_mapeamento_riscos.pdf` | Mapeamento de Riscos: conceitos e métodos aplicados a processos geológicos e hidrológicos | Ministério das Cidades | 2026 | 978-85-7958-108-3 | [PDF](https://www.cidades.gov.br/images/stories/ArquivosPeriferias/ArquivosPDF/Mapeamento_de_riscos_21-10_digital.pdf) |
| `ms_2025_plano_contingencia_chuvas.pdf` | Plano de Contingência para Emergências em Saúde Pública por Chuvas Intensas e Desastres Associados | Ministério da Saúde | 2025 | 978-65-5993-924-4 | [PDF](https://bvsms.saude.gov.br/bvs/publicacoes/plano_contingencia_emergencias_chuvas_desastres.pdf) |
| `mcid_2024_periferia_sem_risco.pdf` | Periferia Sem Risco | Ministério das Cidades | 2024 | 978-85-7958-083-3 | [PDF](https://www.cidades.gov.br/images/stories/ArquivosPeriferias/ArquivosPDF/cartilhaperiferiasemrisco.pdf) |
| `ms_2017_cartilha_alerta_chuvas.pdf` | Cartilha de Orientação à População no Período de Alerta de Chuvas Intensas | Ministério da Saúde | 2017 | não tem | [PDF](https://bvsms.saude.gov.br/bvs/publicacoes/cartilha_orientacao_populacao_chuvas_intensas.pdf) |
| `ms_2026_enchentes.html` | Enchentes (página do gov.br) | Ministério da Saúde | 2026 (ano de acesso) | não tem | [Página](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes) |

## Corpus gerados

Ficam em `entrega-final`.

| Arquivo | Conteúdo | Quantidade |
|---|---|---|
| `corpus_texto.jsonl` | Trechos de 256 a 512 tokens (`text`, `fonte`, `segmento_id`) | 307 trechos |
| `corpus_qa.jsonl` | Perguntas e respostas (`instruction`, `input`, `output`, `fonte`, `segmento_id`) | 100 pares |
| `corpus_chat.jsonl` | Diálogos com papéis system, user e assistant (`messages`, `fonte`, `tipo`, `segmento_id`) | 31 diálogos, 11 recusas |

Também estão em `entrega-final`: `estatisticas.json` (contagens, médias de tokens e duplicatas), `amostras_5_por_corpus.json` (5 exemplos aleatórios de cada corpus), a revisão humana de 20% (`revisao_humana_20_porcento.csv`) e o registro de cada ajuste feito nos exemplos (`REGISTRO_AJUSTES_EDITORIAIS.csv`).

## Corpus ampliado para a IA Generativa

O `corpus_rag.jsonl` fica em `dados/saida_rag/` e é lido pelo RAG da disciplina de IA Generativa pelo link raw do GitHub:

```
https://raw.githubusercontent.com/sarahmfurlan-sudo/radar-cidadao/main/nlp-fabrica-corpus/dados/saida_rag/corpus_rag.jsonl
```

Ele tem 356 trechos de 9 documentos: os 5 de `dados/entrada` e os 4 de `dados/entrada_ia_generativa`, preparados pelo mesmo pipeline (limpeza, anonimização e segmentação). Cada linha tem `id`, `texto`, `fonte`, `titulo`, `paginas` e `tokens`. Esse corpus não faz parte da avaliação da NLP.

## Proteção de dados

Nenhum dado pessoal real aparece nos corpus. CPF, e-mail, telefone e nomes de pessoas, inclusive sobrenomes de autores em citações, são mascarados como `[CPF]`, `[EMAIL]`, `[TELEFONE]` e `[NOME]` antes da geração. Os números de emergência (190, 192, 193, 199 e 40199) e os contatos de órgãos públicos são mantidos. Os arquivos de `dados/teste` contêm só dados fictícios.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `fabrica_corpus.ipynb` | Notebook de entrada, com a interface Gradio |
| `src/fabrica_corpus/` | Módulos de cada etapa: ingestão, limpeza, anonimização, segmentação, geração, exportação, finalização e interface (Gradio) |
| `dados/entrada/` | Os 5 documentos de entrada e a seleção de páginas (`selecao_paginas.json`: as páginas de capa, créditos, sumário e referências que ficam de fora de cada PDF) |
| `dados/entrada_ia_generativa/` | Os 4 documentos extras do corpus ampliado da IA Generativa (com a seleção de páginas deles) |
| `dados/teste/` | Arquivos de teste com dados fictícios (TXT e DOCX) |
| `dados/saida_rag/` | `corpus_rag.jsonl`, o corpus ampliado lido pelo RAG da IA Generativa |
| `dados/cache_geracao/` | Pasta do cache das respostas do Qwen; na geração no Colab o cache ficou no Google Drive |
| `dados/saida/` | Pasta de saída padrão da exportação (vazia: os corpus finais estão em `entrega-final`) |
| `entrega-final/` | Corpus e arquivos de qualidade da entrega |
| `revisao/` | Rótulos da revisão humana da primeira versão, com o Qwen 7B (`rotulos_revisao_7b.csv`) |
| `logs/` | Logs de execução (não versionados) |
| `tests/` | Testes automatizados |
| `Relatorio_NLP_Radar_Cidadao.pdf` | Relatório da disciplina |

## Limitações

- Tabelas de PDF chegam com as colunas misturadas, e palavras compostas quebradas no hífen são unidas sem o hífen.
- Um nome de uma palavra só, que não apareceu completo antes, não é mascarado.
- As perguntas e os diálogos foram gerados por modelo e revisados por amostragem. Não substituem as orientações oficiais da Defesa Civil.

## Links

- Vídeo de demonstração: [inserir o link do vídeo]
