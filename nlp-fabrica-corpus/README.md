# Fábrica de Corpus: Radar Cidadão

Ferramenta da disciplina de NLP da Global Solution 2026.2 (FIAP, tema CitizenTech).

Ela transforma documentos públicos sobre chuvas intensas e alagamentos em três corpus no formato JSONL, prontos para o fine-tuning de um modelo de linguagem pequeno (SLM) voltado a orientar o cidadão.

> **Situação:** em desenvolvimento. Já existem, com testes, os módulos de ingestão, limpeza, anonimização, segmentação e geração. Ainda faltam a exportação dos corpus JSONL, o relatório de qualidade, o notebook do Colab e a interface Gradio.

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
5. **Anonimização:** CPF, e-mail, telefone e nomes de pessoas, antes de gerar qualquer corpus.
   - **Marcações:** `[CPF]`, `[EMAIL]`, `[TELEFONE]` e `[NOME]`.
   - **Nomes, em três camadas:** (1) entidades de pessoa encontradas pelo spaCy (`pt_core_news_md`); (2) o que vem depois do rótulo "Nome:"; (3) repetições de um nome já encontrado, em maiúsculas ou só pelo primeiro nome.
   - **Filtro contra falsos positivos:** usa o vocabulário do corpus. Uma palavra que aparece escrita em minúscula em algum lugar do corpus é tratada como palavra comum, e não como nome de pessoa.
   - **Preservados**, por decisão do grupo em 13/11/2026, porque são serviços de que o cidadão precisa: os números de emergência (190, 192, 193, 199 e 40199), o 156, os e-mails `.gov.br` e os telefones de órgãos públicos da lista `CONTATOS_PUBLICOS`.
   - **Limites conhecidos:** um nome de uma palavra só não é mascarado; um nome de cidade com cara de nome de pessoa (por exemplo, "Afonso Cláudio") é mascarado; um sobrenome que também é palavra comum pode ficar solto no texto.
6. **Segmentação:** trechos de 256 a 512 tokens.
   - **Contagem de tokens:** com o tokenizador do Qwen 2.5 (`Qwen/Qwen2.5-7B-Instruct`), que tem o mesmo vocabulário do Qwen 3.
   - **Corte:** sempre em fim de frase.
   - **Rastreabilidade:** cada segmento guarda todas as páginas de origem e um `id` (nome do arquivo + número sequencial).
7. **Geração dos corpus:** `corpus_texto.jsonl`, `corpus_qa.jsonl` e `corpus_chat.jsonl`, todos com o campo `fonte`.
   - **Modelo:** `Qwen/Qwen2.5-14B-Instruct`, em 4 bits na GPU do Colab, sem API externa (a confirmar no primeiro teste no Colab).
   - **Por que o 14B e o juiz:** a primeira versão usava o `Qwen2.5-7B-Instruct`. Na revisão da amostra de 20%, feita pelo grupo em 13/11/2026, cerca de 35% dos exemplos estavam incoerentes: a resposta não respondia a pergunta, ou a pergunta era sobre o que o morador faz e a resposta sobre o que o governo faz. Por isso o modelo passou a ser o 14B, que segue melhor as regras, e foi criado o juiz de coerência (trava 6).
   - **Persona** (aprovada em 13/11/2026): o cidadão é morador de área de risco. O assistente do Radar Cidadão é acolhedor, só responde com base no trecho, cita a fonte e, em risco imediato, orienta a ligar para o 199 (Defesa Civil) ou o 193 (Bombeiros).
   - **Citação da fonte:** é acrescentada automaticamente pelo código, e não pedida ao modelo (no teste de 13/11/2026 o modelo ignorou o pedido). A função `citacao` de [`geracao.py`](src/fabrica_corpus/geracao.py) (linhas 60 a 71) coloca a citação no fim de cada resposta e na última fala do assistente em cada diálogo, sempre no mesmo formato, com o título legível e as páginas: "Fonte: Periferia Sem Risco, do Ministério das Cidades (2024), p. 7-9." Os títulos ficam na constante `TITULOS` (linhas 43 a 53). O prompt de geração usa a persona sem o "citando a fonte" (`PERSONA_GERACAO`) e pede para o modelo não escrever a fonte, para a citação não sair duplicada.
   - **Quantidades:** 100 perguntas e respostas (2 por segmento) e 30 diálogos de 3 trocas, cada um a partir de um segmento diferente.
   - **Leitura do JSON:** o modelo às vezes escreve vários blocos JSON seguidos em vez de um só (um bloco por troca do diálogo, uma fala por bloco, ou o bloco repetido). O código lê todos e junta os que têm a chave pedida (`perguntas` ou `mensagens`), sem repetir perguntas; falas soltas viram a lista de mensagens.
   - **Travas:** cada exemplo precisa passar pelas 6. Se falhar, o exemplo é refeito, com até 3 tentativas; depois disso o segmento é pulado e contado no relatório. O motivo de cada descarte fica registrado.
     1. A saída é um JSON válido no formato pedido.
     2. Nenhum número novo (telefone, prazo, quantidade), além dos de emergência.
     3. Pelo menos 40% das palavras importantes da resposta estão no trecho. A comparação é feita pelo radical (as 5 primeiras letras), para "alagamentos" e "alagamento" contarem como a mesma palavra e a resposta poder ser reescrita em linguagem simples.
     4. Nenhuma marcação da anonimização (`[NOME]` etc.).
     5. Nada de falar "o trecho", "este documento", "isso aqui" etc., como se o leitor estivesse vendo o documento.
     6. **Juiz de coerência:** o próprio modelo relê cada par de pergunta e resposta junto com o trecho e confere duas coisas: se a resposta responde exatamente o que foi perguntado e se quem age é o mesmo na pergunta e na resposta. Quando reprova, registra o motivo numa frase. O juiz está no prompt `PROMPT_JUIZ` (linhas 247 a 264) e pode ser desligado pela constante `USAR_JUIZ` ou pelo parâmetro `juiz=False`.
   - **Teto de segmentos tentados:** no máximo 3 segmentos tentados para cada segmento necessário nas perguntas, e 3 para cada diálogo pedido (no mínimo 6), para a geração não ficar em laço sem fim quando muitos segmentos são pulados.
   - **Cache:** só o que deu certo fica salvo em [`dados/cache_geracao/`](dados/cache_geracao/) e é reaproveitado nas execuções seguintes. Recusas não são guardadas: depois de um ajuste no código ou no prompt, o segmento é tentado de novo. O nome do arquivo inclui a versão do prompt, o modelo e se o juiz estava ligado.
   - **Revisão:** a amostra de 20% que o grupo revisa à mão é sorteada com semente fixa, então sai sempre igual.
   - **Prompt completo:** em [`src/fabrica_corpus/geracao.py`](src/fabrica_corpus/geracao.py), nas constantes `PERSONA_ASSISTENTE`, `PERSONA_GERACAO`, `PERSONA_CIDADAO`, `PROMPT_QA` e `PROMPT_CHAT` (linhas 74 a 132), e o do juiz em `PROMPT_JUIZ`. Versão atual do prompt: `v5`, com estas regras: a pergunta diz o assunto e faz sentido sozinha; a resposta responde exatamente o que foi perguntado; a pergunta segue quem age no trecho (o que o morador faz, o que a prefeitura, a Defesa Civil ou a saúde fazem, ou o que significa um conceito), sem nunca pedir ao morador uma ação que no trecho é do governo; e a resposta usa linguagem simples, sem acrescentar nada.
8. **Relatório de qualidade:** número de exemplos, média de tokens, duplicatas removidas e 5 exemplos aleatórios.

Não são removidas stop words e não é feito stemming.

As perguntas e os diálogos são gerados pelo **Qwen2.5-14B-Instruct** (família Qwen), quantizado em 4 bits e rodando na GPU do Colab, sem API externa. O grupo revisa pelo menos 20% dos exemplos gerados. O modelo e o prompt estão descritos na etapa 7 e também serão informados no relatório.

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

As versões fixadas estão em [`requirements.txt`](requirements.txt). `gradio` ainda não é usado pelo código; `accelerate` e `bitsandbytes` só são usados no Colab.

| Biblioteca | Uso |
|---|---|
| `pypdf` | Extração de texto de PDF |
| `python-docx` | Extração de texto de DOCX |
| `beautifulsoup4` | Extração de texto de HTML |
| `gradio` | Interface |
| `transformers`, `accelerate`, `bitsandbytes` | Execução do modelo Qwen quantizado na GPU |
| `spacy` (`pt_core_news_md`) | Detecção de nomes de pessoas |
| `transformers` (tokenizador do Qwen 2.5) | Contagem de tokens |

## Estrutura da pasta

| Caminho | Conteúdo |
|---|---|
| `src/fabrica_corpus/` | Módulos Python de cada etapa (`ingestao`, `limpeza`, `anonimizacao`, `segmentacao` e `geracao`) |
| `dados/entrada/` | Documentos de entrada |
| `dados/cache_geracao/` | Saídas do Qwen salvas para reaproveitar entre execuções |
| `dados/saida/` | Os 3 corpus JSONL e o relatório de qualidade |
| `revisao/` | Amostra revisada pelo grupo (mínimo de 20%) |
| `logs/` | Logs de execução (não versionados) |
| `tests/` | Testes automáticos de cada módulo (`pytest`) |

## Integrantes

| Nome completo | RM |
|---|---|
| Sarah Marangoni Furlan | 566764 |
| _Pendente_ | _Pendente_ |
| _Pendente_ | _Pendente_ |
