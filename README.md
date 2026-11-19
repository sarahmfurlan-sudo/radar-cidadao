# Radar Cidadão

> Radar Cidadão: cidadãos registram problemas da cidade, sensores confirmam os riscos e a população recebe alertas para se proteger de alagamentos.

O Radar Cidadão é um app de zeladoria urbana colaborativa. O MVP é focado em **chuva e alagamento** em São Paulo. Projeto da Global Solution 2026.2 da FIAP, tema **CitizenTech**.

## Integrantes

| Nome completo | RM |
|---|---|
| Mario Antônio de Oliveira | 567713 |
| Sarah Marangoni Furlan | 566764 |
| Vinicius Augusto Silva | 566830 |

## Objetivos de Desenvolvimento Sustentável (ODS)

- **ODS 11 – Cidades e Comunidades Sustentáveis** (principal), meta 11.5
- **ODS 13 – Ação Contra a Mudança Global do Clima** (secundário), meta 13.1

## Fluxo do Radar Cidadão

1. **Relato:** o cidadão registra o problema no app, com foto e localização (Front End).
2. **Análise de imagem:** um detector identifica lixo e entulho na foto (Visão Computacional).
3. **Confirmação por sensores:** sensores de nível de água e de chuva confirmam o risco (IoT).
4. **Memória de alagamento:** o memristor guarda o registro do alagamento depois que a água baixa (Computação Neuromórfica).
5. **Mapa de risco:** o relato atualiza o mapa (Front End).
6. **Orientação:** a IA responde ao cidadão com base nos documentos oficiais (NLP e IA Generativa).
7. **Alerta:** a população da região recebe o alerta (IoT e Front End).
8. **Encaminhamento:** o robô consolida os relatos e gera o encaminhamento ao poder público (RPA).

## Disciplinas

| Disciplina | Pasta | Vídeo |
|---|---|---|
| Front End & Mobile Development | [`front-end-mobile/`](front-end-mobile/) | https://youtu.be/UldCOb6rLMQ |
| Visão Computacional | [`visao-computacional/`](visao-computacional/) | arquivo na pasta |
| IoT | [`iot/`](iot/) | https://youtu.be/PKmweoWx3LY |
| Cluster Computing, Computação Neuromórfica e Supercomputadores | [`neuromorfica-memristor/`](neuromorfica-memristor/) | não se aplica |
| Processamento de Linguagem Natural: Fábrica de Corpus | [`nlp-fabrica-corpus/`](nlp-fabrica-corpus/) | https://youtu.be/0dX_j7xm8_Q |
| IA Generativa | [`ia-generativa/`](ia-generativa/) | https://youtu.be/yCeERxSGitM |
| AI for Robotic Process Automation (RPA + IA) | [`rpa-radar-cidadao/`](rpa-radar-cidadao/) | não se aplica |
| Computação Quântica | [`computacao-quantica/`](computacao-quantica/) | não se aplica |
| Governança em IA e Business Analytics | [`governanca/`](governanca/) | https://youtu.be/bSoN1tuT9XI |

Cada pasta tem o seu README com o que foi feito e como executar.

## Integração entre os módulos

- **NLP → IA Generativa:** a IA Generativa lê o corpus produzido pela Fábrica de Corpus (`nlp-fabrica-corpus/dados/saida_rag/corpus_rag.jsonl`) para responder ao cidadão com base nos documentos oficiais.
- **IoT → Front End:** o Front End consulta `GET /api/radar/status` do Node-RED e mostra o estado dos sensores no mapa de risco. Sem o Node-RED rodando, usa dados simulados.
- O que não foi integrado, e por quê, está no documento da Governança.

## Proteção de dados

O repositório não contém chaves de API nem senhas. Os relatos e os dados pessoais usados nos testes são sintéticos ou fictícios, e os corpus da NLP passam por anonimização.
