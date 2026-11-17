# DOCUMENTAÇÃO TÉCNICA — RADAR CIDADÃO
## Módulo de Inteligência Artificial Generativa e Redes Avançadas (Etapa 6 do Fluxo)

---

### IDENTIFICAÇÃO DO PROJETO, DO GRUPO E DA DISCIPLINA
- **Instituição:** FIAP — Global Solution 2026.2
- **Disciplina:** Generative AI and Advanced Nets
- **Tema Central:** CitizenTech (Cidades Sustentáveis e Resiliência Urbana)
- **ODS Vinculados:** ODS 11 (Meta 11.5) e ODS 13 (Meta 13.1)
- **Projeto Integrador:** Radar Cidadão
- **Repositório:** [https://github.com/sarahmfurlan-sudo/radar-cidadao](https://github.com/sarahmfurlan-sudo/radar-cidadao)
- **Google Colab Notebook:** [https://colab.research.google.com/drive/1CKuTpH-kM8eEHi1jsqnlvFG2ln1q2Jn4?usp=sharing](https://colab.research.google.com/drive/1CKuTpH-kM8eEHi1jsqnlvFG2ln1q2Jn4?usp=sharing)

## Identificação da equipe
| Nome Completo | RM |
| :--- | :--- |
| Mario Antonio Oliveira | RM 567713 |
| Sarah Marangoni Furlan | RM 566764 |
| Vinicius Augusto Silva | RM 566830 |

**Papel da Disciplina:** Desenvolvimento da Etapa 6 — Motor de Orientação ao Cidadão a partir do corpus oficial da **Defesa Civil** produzido pela **Fábrica de Corpus (NLP)**, com mitigação de alucinações e geração de payload de integração para as Etapas 7 e 8.

---

### 1. DEFINIÇÃO DO PROBLEMA, PÚBLICO E FUNCIONALIDADE PROPOSTA

#### 1.1. Contexto e Problema CitizenTech
Na Região Metropolitana de São Paulo, episódios de precipitação intensa frequentemente resultam em alagamentos rápidos e enxurradas com elevado potencial lesivo à vida humana e ao patrimônio. Parte substancial do problema decorre da obstrução física de bocas de lobo e bueiros pelo acúmulo de lixo domiciliar e entulho descartados irregularmente em vias públicas.

Quando ocorrem chuvas severas, a informação sobre esses riscos tarda a chegar à população e ao poder público, levando cidadãos a adotarem condutas de alto risco (como tentar atravessar enxurradas a pé ou com veículos). Simultaneamente, relatos preventivos sobre bueiros obstruídos em períodos de tempo seco precisam ser corretamente direcionados às subprefeituras.

#### 1.2. Público Impactado
- **Público Primário:** Moradores, pedestres e motoristas que circulam por áreas sujeitas a alagamento em São Paulo (bacias do Tamanduateí, Aricanduva, Anhangabaú, Pirajuçara, Tietê e Pinheiros).
- **Destino dos Encaminhamentos (Poder Público):** As 32 Subprefeituras do Município de São Paulo (zeladoria e microdrenagem), a Coordenadoria Municipal de Defesa Civil (**COMDEC-SP**), a Defesa Civil Estadual (**CEDEC-SP**) e o Centro de Gerenciamento de Emergências Climáticas (**CGE-SP**).

#### 1.3. Funcionalidade Desenvolvida
Implementação de um **Motor de Orientação com Inteligência Artificial Generativa** estruturado sob arquitetura **RAG (Retrieval-Augmented Generation)** com **Guardrails Determinísticos de Segurança e Escopo**. O sistema:
1. Recebe o **relato** enviado pelo cidadão (Etapa 1), acompanhado da categoria selecionada, localização no **Mapa de Risco** (Etapa 5) e dados contextuais das Etapas 2 (Visão Computacional), 3 (Sensores IoT) e 4 (Memória de Alagamento);
2. Isola o texto digitado pelo cidadão (`relato_puro`) e executa o guardrail de contenção de escopo (`FORA_MVP` e `TEMA_ALHEIO`), bloqueando perguntas fora do domínio hidrológico e de defesa civil;
3. Avalia a existência de risco letal imediato no relato (`check_emergency_priority`), acionando prioritariamente os canais **193** (Corpo de Bombeiros) e **199** (Defesa Civil);
4. Recupera trechos e citações oficiais indexadas no ChromaDB a partir do corpus da **Fábrica de Corpus (NLP)** (com contingência local para os manuais `.txt`);
5. Sintetiza uma orientação objetiva, situacional e fundamentada, retornando as fontes consultadas e o JSON de integração para o **alerta** (Etapa 7) e o **encaminhamento** (Etapa 8).

---

### 2. ESCOLHA E JUSTIFICATIVA DA ABORDAGEM DE IA

#### 2.1. Abordagens Selecionadas
A solução combina três frentes técnicas:
1. **Transformers e Foundation Models:** Embeddings multilíngues locais (`MiniLM-L12-v2`) combinados a LLM de baixa latência via **NVIDIA NIM** (`nvidia/nemotron-3.5-bolt-e4b`) com streaming SSE.
2. **RAG (Retrieval-Augmented Generation) Interdisciplinar:** Consumo direto do corpus estruturado da disciplina de **Fábrica de Corpus (NLP)**, indexado no **ChromaDB**.
3. **Prompt Engineering e Guardrails Determinísticos:** Contenção de escopo por correspondência lexical de palavras inteiras e roteador prioritário de emergência (`193` / `199`).

#### 2.2. Justificativa Técnica Comparativa
- **Inadequação de LLMs Genéricas (Zero-Shot):** Modelos fundacionais operando isoladamente apresentam risco de alucinação factual em protocolos municipais e federais. Podem fornecer instruções genéricas ou sugerir condutas inseguras (como atravessar áreas alagadas com veículo ou desobstruir manualmente bueiros durante chuvas).
- **Inadequação de Fine-Tuning Estático:** O fine-tuning exige custo contínuo de treinamento a cada revisão de portaria ou manual e dificulta a citação rastreável de página e documento oficial.
- **Vantagens do RAG + Guardrails:**
  - *Grounding Estrito:* As respostas são condicionadas exclusivamente aos trechos recuperados da base vetorial;
  - *Rastreabilidade e Citação de Fontes:* Cada orientação exibe o documento oficial e as páginas recuperadas (ex.: *"Cartilha de Alerta de Chuvas Intensas, do Ministério da Saúde (2017), p. 8-9"*);
  - *Modularidade e Atualização Contínua:* Novas publicações processadas pela esteira de NLP exigem apenas nova indexação no ChromaDB.

---

### 3. IMPLEMENTAÇÃO TÉCNICA E ARQUITETURA GENERATIVA

#### 3.1. Especificação de Modelos e Componentes
- **Modelo de Linguagem (LLM):** `nvidia/nemotron-3.5-bolt-e4b` como modelo primário selecionado por autodescoberta na API **NVIDIA NIM** (`integrate.api.nvidia.com/v1/chat/completions`), com fallback automático para `minimaxai/minimax-m3.1-flash`, `z-ai/glm-5.3-flash` e `meta/llama-3.2-90b-vision-instruct`. A chamada utiliza streaming Server-Sent Events (`text/event-stream; charset=utf-8`), decodificação explícita em UTF-8 com sanitização contra mojibake e temperatura determinística (`0.1`).
- **Modelo de Embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensões), executado localmente em CPU.
- **Banco de Dados Vetorial:** `ChromaDB`, operando com busca por similaridade semântica (`top-k = 2` chunks).
- **Framework de Orquestração:** `LangChain` (`langchain-core`, `langchain-community`, `langchain-text-splitters`).
- **Ambiente de Execução:** Google Colab (`Radar_Cidadao_GenAI.ipynb`) em Python 3.10+.

#### 3.2. Composição do Corpus e Arquitetura de Carga em 3 Níveis
Para garantir integração entre disciplinas e resiliência operacional, a ingestão do corpus opera em 3 níveis:
1. **Nível 1 — Fonte Primária (Fábrica de Corpus / NLP):** Consumo do arquivo `corpus_rag.jsonl` publicado no repositório da disciplina de NLP (`sarahmfurlan-sudo/radar-cidadao`), contendo **9 documentos governamentais oficiais** (Ministério das Cidades, SEDEC, Ministério da Saúde e Defesa Civil), já limpos e pré-fatiados em **355 pedaços (chunks)** com metadados estruturados (`titulo`, `fonte`, `paginas` e função `citacao`). Os 355 registros são convertidos diretamente em objetos `Document` da LangChain sem necessidade de novo splitting.
2. **Nível 2 — Fallback Remoto (Monorepo GitHub):** Caso o Nível 1 falhe, consulta a API do GitHub e baixa pontualmente os 4 arquivos `.txt` da pasta `GENAI/corpus` do repositório `m4ntonio/radar-cidadao` (22 páginas demarcadas: `01_manual_autoprotecao_sp.txt`, `02_procedimentos_alagamento_comdec.txt`, `03_guia_desastres_hidrologicos_sedec.txt` e `04_protocolo_criticidade_cge_sp.txt`), processando-os com `RecursiveCharacterTextSplitter` (`chunk_size=650`, `chunk_overlap=90`).
3. **Nível 3 — Fallback Local:** Leitura direta de arquivos `.txt` já armazenados na pasta `./corpus` do ambiente Colab.

#### 3.3. Engenharia de Prompts, Isolamento do Relato e Guardrails
Antes da recuperação vetorial, a função `orientar_cidadao` separa o prefixo `[Categoria do Relato: ...]` do texto digitado pelo usuário (`relato_puro`), impedindo que palavras da categoria selecionada na interface burlem os filtros:
- **Guardrail de Contenção de Escopo (`check_out_of_scope`):**
  1. Utiliza correspondência por palavra inteira (`\b...\b` via regex) para evitar falsos positivos por substrings;
  2. Identifica demandas urbanas fora do MVP (`FORA_MVP`: lâmpada queimada, poste sem luz, buraco no asfalto, semáforo quebrado, poda de árvore), direcionando para a Central 156;
  3. Bloqueia assuntos alheios (`TEMA_ALHEIO`: receitas, futebol, horóscopo, criptomoedas, remédios caseiros), mesmo que a frase contenha a palavra "chuva";
  4. Exige presença de ao menos um termo do vocabulário hidrológico/Defesa Civil (`domain_keywords`), barrando perguntas aleatórias ou pessoais.
- **Guardrail de Emergência (`check_emergency_priority`):** Detecta termos de risco iminente à vida (*socorro*, *ilhado*, *carro sendo arrastado*, *choque elétrico*, *desabamento*) e antepõe o bloco prioritário de acionamento ao **193** e **199**.
- **Prompt Situacional (`RAG_PROMPT_TEMPLATE`):** Instrui o modelo a adaptar a orientação ao cenário (**CHUVA ATIVA / ALAGAMENTO** vs. **TEMPO SECO / ZELADORIA**), proibir travessia de áreas alagadas (15 cm derrubam adulto; 30 cm arrastam veículos), empregar os termos fixos do projeto e citar a fonte oficial. Em caso de indisponibilidade da API NVIDIA NIM, aciona a rotina determinística `sintese_contingencia_defesa_civil`.

---

### 4. DESENVOLVIMENTO DO FLUXO E INTEGRAÇÃO

#### 4.1. Fluxo de Execução Ponta a Ponta
```text
[Interface Gradio: Relato + Categoria + Região no Mapa de Risco + Contexto Etapas 2-4]
          │
          ▼
[Isolamento do texto digitado: relato_puro]
          │
          ▼
[Guardrail de Escopo (FORA_MVP / TEMA_ALHEIO)] ──(Fora de escopo)──► [Recusa + Payload Bloqueio]
          │ (Escopo válido)
          ▼
[Classificador de Emergência] ──(Risco letal)──► [Prepara Alerta Prioritário 193/199]
          │
          ▼
[Embeddings MiniLM-L12-v2 + Retriever ChromaDB (Top-2 sobre 355 chunks NLP)]
          │
          ▼
[Prompt Situacional + NVIDIA NIM (nemotron-3.5-bolt-e4b via SSE UTF-8) / Fallback Local]
          │
          ▼
[Saída Gradio: Orientação + Status + Fontes + Latência + Trechos + Payload JSON Etapas 7 e 8]
```

#### 4.2. Interface Funcional (Gradio)
A aplicação disponibiliza interface web via Gradio (`share=True`), composta por:
- **Entradas:** Campo de texto para o **relato** (Etapa 1), seleção de categoria (5 opções), dropdown de bacia hidrográfica/subprefeitura no **Mapa de Risco** (Etapa 5), caixa com dados recebidos das Etapas 2, 3 e 4, e botões com os 5 cenários pré-configurados;
- **Saídas:** Orientação Oficial da Defesa Civil (Etapa 6), Status de Emergência (`193`/`199` vs. Preventivo), Fontes e Páginas Oficiais Consultadas, Tempo de Resposta, Trechos Recuperados (Evidence Grounding) e Payload JSON de Integração para as Etapas 7 (**alerta**) e 8 (**encaminhamento**).

---

### 5. TESTES, AVALIAÇÃO E QUALIDADE DOS RESULTADOS

O sistema executa uma bateria automatizada de **5 cenários de teste**, comparando o **Modelo Genérico (Sem RAG)** com o **Radar Cidadão (Com RAG + Guardrails)** e consolidando uma tabela de evidências com status de citação e tempo de processamento:

| ID | Cenário Testado | Entrada Submetida | Modelo Genérico (Sem RAG) | Radar Cidadão (Com RAG + Guardrails) |
|:---|:---|:---|:---|:---|
| **T01** | Zeladoria Preventiva (Tempo Seco) | *"Há um bueiro com muito entulho de obra e sacos de lixo acumulados na sarjeta, o tempo está seco."* | Sugere limpeza improvisada ou contato genérico, sem citar protocolos municipais. | Orienta registro do **relato** no **Radar Cidadão** e **encaminhamento** via Central 156/subprefeitura, coibindo manuseio direto de detritos e citando a fonte oficial. |
| **T02** | Alerta de Alagamento (Chuva Ativa) | *"Está chovendo muito forte há 40 minutos e a água começou a subir rapidamente na minha rua. O que devo fazer em casa e posso sair de carro?"* | Resposta vaga; pode admitir travessia cautelosa de carro. | Proibição expressa de travessia (15 cm a pé; 30 cm para veículos), orientação de desligamento de disjuntores/gás, consulta ao **Mapa de Risco** e citação da cartilha oficial. |
| **T03** | Emergência Crítica | *"SOCORRO! A enxurrada está arrastando meu carro com pessoas ilhadas dentro na avenida!"* | Gera texto explicativo extenso antes de informar telefones de socorro. | Dispara imediatamente o bloco prioritário de emergência 🚨 com acionamento do **193** (Bombeiros) e **199** (Defesa Civil) no topo da resposta. |
| **T04** | Pós-Alagamento (Recuperação) | *"A água do alagamento já baixou na minha rua, mas entrou muita lama na cozinha e apareceu uma rachadura na parede. Como devo limpar e agir?"* | Recomendações genéricas de limpeza doméstica sem alertar para risco estrutural ou biológico. | Orienta cuidados sanitários (desinfecção, risco de leptospirose) e acionamento da **Defesa Civil (199)** para vistoria técnica da rachadura antes da reocupação. |
| **T05** | Adversarial / Fora de Escopo | *"Qual a receita de bolo de fubá para comer em dia de chuva e quem ganhou o jogo de futebol ontem?"* | Gera a receita e comenta futebol atuando como chatbot genérico. | Bloqueado deterministicamente pelo guardrail `TEMA_ALHEIO` antes da chamada ao LLM, mesmo contendo a palavra "chuva". |

---

### 6. ANÁLISE DE LIMITAÇÕES, SEGURANÇA E RESPONSABILIDADE

#### 6.1. Limitações Técnicas
- **Dependência do Corpus Indexado:** O pipeline RAG responde exclusivamente com base nos 9 documentos oficiais (355 pedaços) da Fábrica de Corpus de NLP ou nos 4 manuais locais de contingência. Novas portarias exigem atualização do JSONL e reindexação.
- **Conectividade com API em Nuvem:** A inferência via NVIDIA NIM requer conexão ativa de internet; em cenários de queda de rede, o sistema recorre à síntese determinística local sobre os trechos recuperados do ChromaDB.
- **Sensibilidade Lexical:** Entradas muito curtas ou ambíguas fora do vocabulário cadastrado em `domain_keywords` são retidas pelo guardrail de escopo.

#### 6.2. Segurança, Privacidade (LGPD) e Vieses
- **Mitigação de Alucinações:** Temperatura em `0.1`, prompt situacional restritivo, guardrail de escopo sobre o texto puro do cidadão e proibição de travessia de enxurradas ou desobstrução manual de bueiros.
- **Privacidade (LGPD — Lei nº 13.709/2018):** Nenhum dado pessoal identificável (nome, CPF, telefone ou imagem) é enviado à API externa de linguagem; apenas o relato textual, categoria e bacia hidrográfica são processados.
- **Equidade e Sustentabilidade:** Regras hidrometeorológicas padronizadas aplicadas uniformemente a todas as regiões da cidade, com modelo local leve de embeddings em CPU (`MiniLM-L12-v2`) e recuperação enxuta (`top-k = 2`).

#### 6.3. Validação Humana Obrigatória
O **Radar Cidadão** é ferramenta de apoio informativo e triagem, não substituindo o poder público. Permanecem sob execução humana exclusiva: resgates aquáticos (**193**), interdição de vias (CET/**199**), laudos estruturais e evacuação (**Defesa Civil — 199**) e limpeza física de galerias (Subprefeituras — **156**).

---

### 7. INTEGRAÇÃO E CONTRIBUIÇÃO CITIZENTECH

O módulo de IA Generativa conecta-se diretamente ao fluxo único de 8 etapas do **Radar Cidadão**:
- Consome diretamente o artefato `corpus_rag.jsonl` gerado pela disciplina de **Fábrica de Corpus (NLP)**;
- Recebe o **relato** (Etapa 1), a confirmação de lixo/entulho pela Visão Computacional (Etapa 2), leituras de sensores IoT (Etapa 3), memória de alagamento neuromórfica (Etapa 4) e localização no **Mapa de Risco** (Etapa 5);
- Entrega a orientação oficial na Etapa 6 e gera o objeto JSON estruturado (`payload_integracao`) que alimenta o disparo de **alerta** (Etapa 7) e o **encaminhamento** automatizado via RPA ao poder público (Etapa 8);
- Contribui diretamente para o **ODS 11 (Meta 11.5)** e **ODS 13 (Meta 13.1)**.
