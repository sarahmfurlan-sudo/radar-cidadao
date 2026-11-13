# Fábrica de Corpus: Radar Cidadão

Ferramenta da disciplina de NLP da Global Solution 2026.2 (FIAP, tema CitizenTech).

Ela transforma documentos públicos sobre chuvas intensas e alagamentos em três corpus no formato JSONL, prontos para o fine-tuning de um modelo de linguagem pequeno (SLM) voltado a orientar o cidadão.

> **Situação:** em desenvolvimento. Por enquanto, só os documentos de entrada estão no repositório. O código, o notebook e os corpus ainda não existem.

## Como executar no Google Colab

> _**Pendente.** Estas instruções serão escritas e testadas quando o notebook `fabrica_corpus.ipynb` existir._

Passos previstos:

1. Abrir o notebook `fabrica_corpus.ipynb` no Colab.
2. Ativar a GPU gratuita (Ambiente de execução → Alterar o tipo de ambiente de execução → GPU).
3. Executar as células em ordem. O notebook clona este repositório e instala as bibliotecas.
4. Usar a interface Gradio para enviar documentos (PDF, TXT, DOCX, HTML ou texto colado) e gerar os corpus.

## Etapas da ferramenta

1. **Ingestão:** PDF, TXT, DOCX, HTML e texto colado.
2. **Extração:** com registro do arquivo de origem de cada trecho.
3. **Limpeza:** cabeçalhos, rodapés, números de página, URLs soltas, caracteres estranhos, linhas repetidas e palavras quebradas por hífen.
4. **Normalização:** UTF-8, espaços, quebras de linha e aspas, mantendo acentos, pontuação e maiúsculas.
5. **Anonimização:** CPF, e-mail, telefone e nomes de pessoas, antes de gerar qualquer corpus. Os números de emergência (190, 192, 193, 199 e 40199) são preservados.
6. **Segmentação:** trechos de 256 a 512 tokens, respeitando o fim de frase ou parágrafo.
7. **Geração dos corpus:** `corpus_texto.jsonl`, `corpus_qa.jsonl` e `corpus_chat.jsonl`, todos com o campo `fonte`.
8. **Relatório de qualidade:** número de exemplos, média de tokens, duplicatas removidas e 5 exemplos aleatórios.

Não são removidas stop words e não é feito stemming.

As perguntas e os diálogos são gerados por um modelo aberto da família **Qwen** (modelo exato a definir), quantizado e rodando na GPU do Colab, sem API externa. O grupo revisa pelo menos 20% dos exemplos gerados. O modelo usado e o prompt serão informados aqui e no relatório.

## Documentos de entrada

Ficam em [`dados/entrada/`](dados/entrada/).

| Arquivo | Documento | Órgão | Ano | ISBN | Link oficial |
|---|---|---|---|---|---|
| `mcid_2026_mapeamento_riscos.pdf` | Mapeamento de Riscos: conceitos e métodos aplicados a processos geológicos e hidrológicos | Ministério das Cidades | 2026 | 978-85-7958-108-3 | [PDF](https://www.cidades.gov.br/images/stories/ArquivosPeriferias/ArquivosPDF/Mapeamento_de_riscos_21-10_digital.pdf) |
| `ms_2025_plano_contingencia_chuvas.pdf` | Plano de Contingência para Emergências em Saúde Pública por Chuvas Intensas e Desastres Associados | Ministério da Saúde | 2025 | 978-65-5993-924-4 | [PDF](https://bvsms.saude.gov.br/bvs/publicacoes/plano_contingencia_emergencias_chuvas_desastres.pdf) |
| `mcid_2024_periferia_sem_risco.pdf` | Periferia Sem Risco | Ministério das Cidades | 2024 | 978-85-7958-083-3 | [PDF](https://www.cidades.gov.br/images/stories/ArquivosPeriferias/ArquivosPDF/cartilhaperiferiasemrisco.pdf) |
| `ms_2017_cartilha_alerta_chuvas.pdf` | Cartilha de Orientação à População no Período de Alerta de Chuvas Intensas | Ministério da Saúde | 2017 | — | [PDF](https://bvsms.saude.gov.br/bvs/publicacoes/cartilha_orientacao_populacao_chuvas_intensas.pdf) |
| `ms_2026_enchentes.html` | Enchentes (página no gov.br) | Ministério da Saúde | 2026 (ano de acesso) | — | [Página](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes) |

### Seleção de páginas

Os PDFs ficam inteiros no repositório. A seleção é aplicada na ingestão, a partir de [`selecao_paginas.json`](dados/entrada/selecao_paginas.json). O HTML não tem páginas e entra inteiro.

| Documento | Páginas excluídas | Motivo |
|---|---|---|
| Mapeamento de Riscos (MCid, 2026) | 1–6, 109–111 (usadas 102 de 111) | Capa (p. 1), folha de rosto (p. 2), ficha catalográfica e expediente com nomes (p. 3), listas de figuras e quadros (p. 4–5), sumário (p. 6), minibiografias dos autores (p. 109), página em branco (p. 110) e quarta capa (p. 111). |
| Cartilha Alerta de Chuvas (MS, 2017) | 1–4, 24 (usadas 19 de 24) | Capa, folha de rosto, ficha catalográfica e expediente com nomes, sumário e contracapa. |
| Plano de Contingência (MS, 2025) | 1–6, 68–71, 78 (usadas 67 de 78) | Capa, folha de rosto, ficha catalográfica e expediente com nomes (p. 3), lista de siglas (p. 4–5), sumário (p. 6), referências bibliográficas (p. 68–71) e contracapa (p. 78). |
| Periferia Sem Risco (MCid, 2024) | 1–2, 10–12 (usadas 7 de 12) | Capa e contracapa (só imagem) e expediente com nomes (p. 10). |

## Documentos ampliados (RAG de IA Generativa)

Ficam em [`dados/entrada_ia_generativa/`](dados/entrada_ia_generativa/).
**Não entram no corpus avaliado da NLP**, que usa só os 5 documentos acima. Servem para o corpus ampliado (9 documentos) usado no RAG da disciplina de IA Generativa.

| Arquivo | Documento | Órgão | Ano | Link oficial |
|---|---|---|---|---|
| `mdr_2021_guia_alertas_desastres.pdf` | Guia Prático de Utilização de Alertas do Governo Federal para Ações de Preparação para Desastres (2ª ed.) | Ministério do Desenvolvimento Regional | 2021 | _Pendente_ |
| `mi_2003_manual_desastres_naturais.pdf` | Manual de Desastres, Volume I: Desastres Naturais | Ministério da Integração Nacional | 2003 | _Pendente_ |
| `pmsp_2024_chuvas_excessivas.pdf` | Chuvas excessivas: Saiba como agir (página da Defesa Civil, salva em PDF) | Prefeitura de São Paulo | 2024 | [Página](https://prefeitura.sp.gov.br/web/defesa_civil/w/cuidados_importantes/179951) |
| `cgesp_2026_dicas_alagamentos.docx` | Dicas sobre alagamentos e enchentes (texto transcrito da página) | CGE – Prefeitura de São Paulo | 2026 (ano de acesso) | _Pendente: link da página original no cgesp.org_ |

### Seleção de páginas

Os PDFs ficam inteiros no repositório. A seleção é aplicada na ingestão, a partir de [`selecao_paginas.json`](dados/entrada_ia_generativa/selecao_paginas.json).

| Documento | Páginas usadas | Motivo |
|---|---|---|
| Manual de Desastres (MI, 2003) | 40–41, 48–52, 108–117 (17 de 174) | Só os capítulos sobre inundações, enxurradas, alagamentos e deslizamentos. Excluídas: créditos (p. 3), manejo rural de bacias (p. 42–47), inundações litorâneas (p. 53), introdução de geomorfologia (p. 102–107), rastejos e quedas de rochas (p. 118–121). |
| Guia Prático de Alertas (MDR, 2021) | Todas, exceto a p. 2 (45 de 46) | A p. 2 é a página de créditos, com nomes reais. |

## Arquivo de teste

Os formatos TXT, DOCX e texto colado serão demonstrados com um arquivo de teste com **dados pessoais fictícios**. O mesmo arquivo serve para mostrar o "antes e depois" da anonimização. Ele fica em [`dados/teste/`](dados/teste/), junto com o script `gerar_docx.py`, que gera o DOCX a partir do TXT.

## Bibliotecas

> _**Previstas.** A lista final, com versões, será confirmada quando o código existir._

| Biblioteca | Uso |
|---|---|
| `pypdf` | Extração de texto de PDF |
| `python-docx` | Extração de texto de DOCX |
| `beautifulsoup4` | Extração de texto de HTML |
| `gradio` | Interface |
| `transformers`, `accelerate`, `bitsandbytes` | Execução do modelo Qwen quantizado na GPU |
| _a definir_ | Contagem de tokens e detecção de nomes de pessoas |

## Estrutura da pasta

| Caminho | Conteúdo |
|---|---|
| `src/fabrica_corpus/` | Módulos Python de cada etapa _(a criar)_ |
| `dados/entrada/` | Documentos de entrada |
| `dados/cache_geracao/` | Saídas do Qwen salvas para reaproveitar entre execuções |
| `dados/saida/` | Os 3 corpus JSONL e o relatório de qualidade |
| `revisao/` | Amostra revisada pelo grupo (mínimo de 20%) |
| `logs/` | Logs de execução (não versionados) |
| `tests/` | Testes _(a criar)_ |

## Integrantes

| Nome completo | RM |
|---|---|
| Sarah Marangoni Furlan | 566764 |
| _Pendente_ | _Pendente_ |
| _Pendente_ | _Pendente_ |
