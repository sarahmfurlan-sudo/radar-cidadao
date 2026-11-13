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
   - **Critérios de qualidade**, definidos antes de gerar (13/11/2026), com meta de **90% de aprovação** na amostra revisada pelo grupo. Um exemplo é aprovado quando cumpre os 4:
     1. **Apoiada:** tudo o que a resposta afirma está no trecho.
     2. **Responde:** a resposta responde exatamente a pergunta.
     3. **Mesmo agente:** quem age é o mesmo na pergunta e na resposta (morador, poder público ou conceito).
     4. **Fala com o morador:** sem "o trecho", "este documento", "isso aqui" etc., como se o leitor estivesse vendo o documento.
   - **Histórico das versões do prompt:**

     | Versão | Mudança | Motivo |
     |---|---|---|
     | v1 a v3 | Geração direta a partir do trecho, com o `Qwen2.5-7B-Instruct`; citação da fonte passa a ser colocada pelo código (v3) | — |
     | v5 | Modelo trocado para o 14B; juiz de coerência (responde e mesmo agente); trava contra "o trecho" | Revisão do 7B: muitos exemplos incoerentes (veja "Revisão do 7B" abaixo) |
     | v6 | Juiz ganha o critério "apoiada"; a trava de palavras vira um filtro grosseiro de 25% | Quem decide se a resposta acrescenta algo é o juiz, que lê o sentido; a contagem de palavras só barra o que está muito longe do trecho |
     | v7 | O cidadão só pergunta o que o trecho explica, sem a lista fixa de assuntos (antes, durante, depois, limpeza, doenças) | Com a lista, o modelo fazia o cidadão perguntar de assuntos que o trecho não trata e respondia com conhecimento próprio |
     | v8 | Geração em etapas, a partir dos fatos do trecho (veja abaixo) | A revisão do 7B ficou em 71% de aprovação, abaixo da meta de 90% |

   - **Geração em etapas (v8):**
     1. **Extração de fatos:** o modelo lista os fatos do trecho que interessam ao morador, cada um numa frase curta e com **quem age**: `morador` (o que a pessoa pode fazer), `poder_publico` (com o órgão: prefeitura, Defesa Civil, saúde etc.) ou `conceito` (definição, causa, explicação). Cada fato passa pelas travas 2 a 4; um fato inventado não chega à etapa seguinte. Se o trecho não tem nada útil ao morador (siglas, referências, créditos), o segmento é pulado.
     2. **Perguntas e diálogos a partir dos fatos:** cada pergunta é respondida por um fato e segue quem age nele ("O que eu faço...", "O que a Defesa Civil faz...", "O que é..."). Assim a pergunta já nasce com o agente certo e o diálogo não precisa inventar para continuar.
     - A etapa em fatos pode ser desligada pela constante `USAR_FATOS`, voltando à geração direta a partir do trecho.
   - **Persona** (aprovada em 13/11/2026): o cidadão é morador de área de risco. O assistente do Radar Cidadão é acolhedor, só responde com base no trecho, cita a fonte e, em risco imediato, orienta a ligar para o 199 (Defesa Civil) ou o 193 (Bombeiros). Na geração, o cidadão usa a `PERSONA_CIDADAO_GERACAO`, que não traz a lista de assuntos (v7).
   - **Citação da fonte:** é acrescentada automaticamente pelo código, e não pedida ao modelo (no teste de 13/11/2026 o modelo ignorou o pedido). A função `citacao` de [`geracao.py`](src/fabrica_corpus/geracao.py) (linhas 63 a 74) coloca a citação no fim de cada resposta e na última fala do assistente em cada diálogo, sempre no mesmo formato, com o título legível e as páginas: "Fonte: Periferia Sem Risco, do Ministério das Cidades (2024), p. 7-9." Os títulos ficam na constante `TITULOS` (linhas 46 a 56). O prompt de geração usa a persona sem o "citando a fonte" (`PERSONA_GERACAO`) e pede para o modelo não escrever a fonte, para a citação não sair duplicada.
   - **Quantidades:** 100 perguntas e respostas (até 2 por segmento, sem passar do número de fatos) e 30 diálogos, cada um a partir de um segmento diferente. Cada diálogo tem tantas trocas quantos fatos o segmento tiver, de 2 a 3; um segmento com menos de 2 fatos não vira diálogo.
   - **Divisão planejada dos segmentos:** antes de gerar, a função `planejar_divisao` reparte os segmentos entre perguntas e diálogos, na proporção do que cada um precisa. Antes (v1 a v7), as perguntas rodavam primeiro e ficavam com os documentos voltados ao morador (Periferia, Cartilha, Enchentes), e os diálogos só com as sobras técnicas. Agora todo documento contribui para os dois.
   - **Leitura do JSON:** o modelo às vezes escreve vários blocos JSON seguidos em vez de um só (um bloco por troca do diálogo, uma fala por bloco, ou o bloco repetido). O código lê todos e junta os que têm a chave pedida (`fatos`, `perguntas`, `mensagens` ou `avaliacoes`), sem repetir perguntas; falas soltas viram a lista de mensagens.
   - **Travas:** cada exemplo precisa passar pelas 6. Se falhar, o exemplo é refeito, com até 3 tentativas; depois disso o segmento é pulado e contado no relatório. O motivo de cada descarte fica registrado.
     1. A saída é um JSON válido no formato pedido.
     2. Nenhum número novo (telefone, prazo, quantidade), além dos de emergência.
     3. **Filtro grosseiro de palavras:** pelo menos 25% das palavras importantes da resposta estão no trecho, comparadas pelo radical (as 5 primeiras letras), para "alagamentos" e "alagamento" contarem como a mesma palavra. Esse corte é só interno à trava: o texto do corpus não é alterado. Só barra a resposta muito longe do trecho; quem confere se a resposta acrescenta algo é o juiz (trava 6).
     4. Nenhuma marcação da anonimização (`[NOME]` etc.).
     5. Nada de falar "o trecho", "este documento", "isso aqui" etc., como se o leitor estivesse vendo o documento.
     6. **Juiz:** o próprio modelo relê cada par de pergunta e resposta junto com o trecho e confere os critérios 1 a 3: se a resposta está **apoiada** no trecho, se **responde** exatamente o que foi perguntado e se **quem age** é o mesmo na pergunta e na resposta. Quando reprova, registra quais critérios falharam e o motivo numa frase. O juiz está no prompt `PROMPT_JUIZ` (linhas 362 a 381) e pode ser desligado pela constante `USAR_JUIZ` ou pelo parâmetro `juiz=False`.
   - **Teto de segmentos tentados:** no máximo 3 segmentos tentados para cada segmento necessário nas perguntas, e 3 para cada diálogo pedido (no mínimo 6), para a geração não ficar em laço sem fim quando muitos segmentos são pulados.
   - **Cache:** só o que deu certo fica salvo em [`dados/cache_geracao/`](dados/cache_geracao/) e é reaproveitado nas execuções seguintes. Recusas não são guardadas: depois de um ajuste no código ou no prompt, o segmento é tentado de novo. O nome do arquivo inclui a versão do prompt, o modelo e se o juiz e a etapa em fatos estavam ligados.
   - **Conjunto fixo de avaliação:** a função `conjunto_avaliacao` sorteia, com semente fixa (2026), os mesmos 12 segmentos toda vez. Eles servem para comparar uma versão do prompt com outra sobre o mesmo material.
   - **Revisão do grupo:** a amostra de 20% que o grupo revisa à mão é sorteada com semente fixa, então sai sempre igual.
     - **Forma de registro:** um CSV por revisão na pasta [`revisao/`](revisao/), em UTF-8 com separador `;`, com as colunas `id`, `motivo_da_selecao` (amostra de 20% ou item suspeito escolhido a dedo), `fonte`, `paginas`, `pergunta / diálogo`, `resposta` (vazia nos diálogos), `rotulo (S/N)` e `motivo do N`. Os rótulos S/N são decididos pela Sarah; os motivos dos N são redigidos com apoio de IA.
     - **Revisão do 7B** ([`revisao/rotulos_revisao_7b.csv`](revisao/rotulos_revisao_7b.csv)): 28 itens gerados pelo `Qwen2.5-7B-Instruct` (20 perguntas e 6 diálogos da amostra de 20%, mais 2 perguntas escolhidas por suspeita de erro de quem age). Resultado: **20 S e 8 N**, ou seja, 71% aprovados e 29% reprovados, abaixo da meta de 90%. Os 8 N: 3 em que a resposta não responde a pergunta, 2 com quem age trocado, 2 que falam "do trecho" ou "isso aqui" e 1 fora do foco do morador. Essa revisão motivou a troca para o 14B e o juiz (v5) e a geração em etapas (v8).
     - **Medição do juiz:** a função `medir_juiz` roda as travas e o juiz sobre cada item de um CSV de revisão e compara com o rótulo humano. Devolve a matriz de confusão (humano S/N contra sistema aprova/reprova), a concordância e a lista de divergências, para o relatório.
   - **Prompt completo:** em [`src/fabrica_corpus/geracao.py`](src/fabrica_corpus/geracao.py). Versão atual do prompt: `v8`.
     - Personas: `PERSONA_ASSISTENTE`, `PERSONA_GERACAO`, `PERSONA_CIDADAO_GERACAO` e `PERSONA_CIDADAO` (linhas 77 a 100).
     - Geração em etapas (v8): `PROMPT_FATOS`, `PROMPT_QA_FATOS` e `PROMPT_CHAT_FATOS` (linhas 158 a 206). Os critérios de qualidade ficam num comentário logo antes (linhas 146 a 151).
     - Juiz: `PROMPT_JUIZ` (linhas 362 a 381).
     - Geração direta, usada só com `USAR_FATOS = False`: `PROMPT_QA` e `PROMPT_CHAT` (linhas 102 a 143).
8. **Relatório de qualidade:** número de exemplos, média de tokens, duplicatas removidas e 5 exemplos aleatórios.

O corpus não passa por remoção de stop words nem por stemming: os textos dos 3 JSONL ficam com as palavras inteiras. A comparação pelas 5 primeiras letras existe só dentro da trava 3 da etapa 7, para conferir a resposta contra o trecho, e não muda nenhum texto.

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
