# Radar Cidadão — RPA + IA | FIAP Global Solution 2026.2

**Protótipo acadêmico de triagem automatizada de relatos de riscos urbanos.** Este projeto compõe a solução CitizenTech Radar Cidadão, mas **é independente do notebook Qwen de NLP**. Roda localmente, sem GPU, sem chave de API e sem enviar dados para serviços externos.

> **Aviso:** não é um sistema oficial de Defesa Civil, não prevê desastres nem abre chamados. Apenas apresenta orientações gerais e sinaliza casos que requerem atendimento humano. Em risco imediato, a pessoa deve procurar segurança e contatar os serviços oficiais. O protótipo não substitui isso.

## Integrantes

**Mario Antônio de Oliveira — RM 567713**  
**Sarah Marangoni Furlan — RM 566764**  
**Vinicius Augusto Silva — RM 566830**

## Problema, público e ODS

Durante chuvas intensas, moradores de áreas expostas a alagamentos e encostas instáveis precisam encontrar rapidamente orientações compreensíveis. A triagem manual de um grande volume de relatos pode ser repetitiva. O protótipo organiza relatos fictícios, classifica o assunto e sugere encaminhamentos prudentes. **Persona:** morador que relata uma situação relacionada a chuvas, alagamentos ou deslizamentos, com acesso básico à tecnologia. **ODS 11:** Cidades e Comunidades Sustentáveis, com relação adicional ao ODS 13 (Ação Contra a Mudança Global do Clima).

## Instalação no Windows (PowerShell)

Requer Python 3.10 ou superior. Execute dentro desta pasta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m radar_rpa run --input dados\ocorrencias_demo.csv --output saida\demo
.\.venv\Scripts\python.exe -m radar_rpa validate --input dados\validacao_rotulada.csv --output saida\validacao
.\.venv\Scripts\python.exe -m pytest -q
```

Linux/macOS, depois de criar e ativar um `venv`: `python -m pip install -e '.[test]'` e execute os comandos com `python`.

**Ponto de entrada:** `python -m radar_rpa run --input <arquivo.csv> --output <diretorio>`.

O CSV deve ser UTF-8 com colunas `id;relato`. Não é necessário internet após a instalação da dependência scikit-learn. Não é necessário cadastrar chave de API: o sistema não usa nenhuma.

## Execução ponta a ponta

1. Lê as solicitações de `dados/ocorrencias_demo.csv`.
2. Valida o cabeçalho, os campos e o tamanho de cada relato.
3. Evita reprocessamento usando hash SHA-256 e banco local SQLite.
4. Analisa sinais explícitos de urgência com regras conservadoras e classifica relatos com um **modelo local TF-IDF + Regressão Logística**, treinado em 48 frases sintéticas.
5. Para relatos inconclusivos, solicita revisão humana; para possíveis urgências, orienta acionamento direto de serviços oficiais **sem fazer o acionamento**.
6. Mascara padrões de CPF, e-mail e telefone na saída e evita incluir relatos nos logs.
7. Exporta `resultados.csv`, `resumo.json`, `execucao.log` e `auditoria.sqlite3` na pasta de saída.

Se uma linha estiver inválida, o robô registra a ocorrência e continua nas demais. Se o arquivo estiver ausente ou o cabeçalho errado, encerra com erro documentado e código 2, sem gerar respostas enganosas. Ao executar novamente no mesmo diretório, **preserva as linhas antigas** e registra duplicações sem reprocessar.

## Quadro dos temas efetivamente usados

| Tema estudado | Onde aparece na implementação | Função real |
| --- | --- | --- |
| Automação de arquivos com Python | `cli.py`, leitura `csv.DictReader` e exportação CSV/JSON/logs | Processamento em lote e geração de evidências |
| Integração de IA/ML na automação | `core.py`, `TfidfVectorizer` e `LogisticRegression` | Classifica o tema de cada relato sem API ou GPU |
| RPA com Python e tratamento de erros | `cli.py`, orquestração e tratamento por linha | Executa ponta a ponta, trata falhas e registra logs |
| BPM, processos e tarefas | `docs/FLUXO_BPMN.md`, modelo do workflow | Define tarefas, decisões, exceções e saídas do processo |
| Automação com banco de dados | `cli.py`, `sqlite3` | Auditoria técnica e idempotência, sem armazenar o relato bruto |

Conteúdo alinhado aos materiais da disciplina: *Hyperautomation*, *Leitura de arquivos*, *Process, Tasks and BPM/BPMN* e *Exercícios Cron*. Não utilizamos agendamento Cron porque não é necessário para a execução demonstrada.

## Métricas e evidências reproduzíveis

Execute:

```powershell
.\.venv\Scripts\python.exe -m radar_rpa validate --input dados\validacao_rotulada.csv --output saida\validacao
```

A pasta `evidencias/` inclui resultados da execução inicial, mas **rode os comandos para obter os seus próprios números**. O conjunto rotulado é sintético, tem 16 exemplos e é independente das 48 frases usadas no treinamento. Sua acurácia NÃO deve ser interpretada como desempenho real da triagem. Confira `evidencias/validacao.json` para acertos/erros medidos.

**Demonstração de falha:** `dados/ocorrencias_demo.csv` contém uma linha com relato vazio: o robô a rejeita e continua. O arquivo `evidencias/falha_arquivo_ausente/resumo.json` registra também o comportamento seguro quando a entrada não existe.

Testes de software: `python -m pytest -q`. Testam entrada ausente, cabeçalho inválido, anonimização básica, idempotência, suspeita de urgência, fórmula em CSV e processamento parcial.

## Segurança, LGPD e ética

Somente dados inventados são utilizados nos exemplos. Não há chamadas a APIs e não existem chaves no código. O robô não armazena o texto bruto no SQLite, mas **o CSV de saída contém o relato parcialmente mascarado**: o filtro cobre padrões de CPF, e-mail e telefone, **não garante a remoção de nomes, endereços ou outras informações identificáveis**. Por isso, **nunca use dados pessoais reais sem tratamento adicional, revisão humana e autorização**. Nunca exponha a pasta `saida/` em um repositório público com relatos reais. A triagem não substitui avaliação técnica da Defesa Civil, nem oferece diagnóstico médico ou previsão oficial.

## Limitações e próximos passos

- Modelo pequeno, treinado com frases sintéticas. Não calibrado nem validado em eventos reais; probabilidade do classificador não é probabilidade de desastre.
- Regras de palavras-chave podem deixar passar urgências descritas de outras formas. A revisão humana permanece necessária.
- Não integra dados meteorológicos reais nem sistemas da Defesa Civil.
- A proteção de dados não detecta nomes, endereços e todos os tipos de identificadores.
- O projeto pode integrar futuramente um canal público oficial, mas isso não é parte deste protótipo.

## Estrutura

```text
rpa-radar-cidadao/
├─ radar_rpa/           # classificador, regras e orquestrador CLI
├─ dados/                # ocorrencias e amostra rotulada sintéticas
├─ docs/                 # fluxo BPMN simplificado e instruções de demonstração
├─ evidencias/           # execução e validação já realizadas
├─ tests/                # testes automatizados
├─ pyproject.toml        # configuração e dependências
└─ README.md
```

## Fontes pedagógicas

Materiais fornecidos na disciplina: `01_hyperautomation`, `rpa_ia_arquivos`, `02_Process_tasks_bpm_bpmn`, `cron_exercises` e o enunciado `GS2026_2_Enunciado_Final_RPA_IA`.

Fonte pública complementar para orientações preventivas: [Defesa Civil Nacional — gov.br/mdr](https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil). O protótipo não consulta esse endereço nem afirma reproduzir recomendações oficiais completas.

## Notebook executado no Google Colab

O arquivo `RADAR_CIDADAO_RPA_COLAB_EXECUTADO.ipynb` acompanha esta entrega com saídas e evidências já gravadas. Ele permite conferir o fluxo sem precisar refazer o notebook NLP.
