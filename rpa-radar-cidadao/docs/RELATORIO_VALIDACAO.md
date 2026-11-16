# Relatorio de validacao e evidencias — Radar Cidadao RPA + IA

**Disciplina:** AI for Robotic Process Automation — FIAP GS 2026.2
**Projeto:** Radar Cidadao (prototipo academico)
**Fonte:** artefatos do projeto v1 e execucao confirmada no Windows em 16/11/2026.

## Objetivo e fluxo

Receber lote sintetico de relatos de risco urbano (`id;relato`), validar registro, classificar tema com modelo local TF-IDF + regressao logistica, priorizar sinais explicitos de urgencia com regras conservadoras, registrar auditoria no SQLite e emitir orientacao ou encaminhamento seguro em CSV e JSON. Nao abre chamados nem envia alertas oficiais.

## Resultados observados

| Evidencia | Resultado | Origem |
|---|---:|---|
| Casos no lote | 12 | `evidencias/demo/resumo.json` |
| Relatos processados | 11 | Idem |
| Registros invalidos tratados | 1 | Idem |
| Encaminhamentos imediatos | 2 | Idem |
| Orientacoes gerais | 7 | Idem |
| Fora de escopo | 2 | Idem |
| Testes automatizados | 11/11 aprovados | Log do PowerShell fornecido pela equipe, 16/11/2026 |
| Classificacoes corretas | 16/16 | `evidencias/validacao.json` |
| Erros de classificacao na amostra | 0 | Idem |

**Importante:** a acuracia de 100% foi observada somente em **16 frases sinteticas**. A amostra e pequena e nao demonstra desempenho real, capacidade de prever desastres nem eficacia em emergencias. O treinamento usa 48 frases sinteticas.

## Excecoes e caminhos seguros

1. Um relato vazio e marcado invalido; as outras linhas continuam processadas.
2. Arquivo inexistente produz `resumo.json` com erro e log em `execucao.log`, sem gerar orientacao enganosa; erro registrado: **Arquivo de entrada ausente**.
3. Cabecalho CSV incorreto e entrada malformada sao tratados com erro controlado.
4. Hash + SQLite evita reprocessar o mesmo relato na mesma pasta de saida.
5. Em caso de baixa confianca, o sistema pode encaminhar para revisao humana em vez de apresentar resposta especifica.

## Tres temas e mais, efetivamente usados

| Tema da aula | Funcao operacional | Prova no codigo |
|---|---|---|
| Automacao de arquivos Python | Ingestao de CSV e saida CSV/JSON | `radar_rpa/cli.py`, `processar`, `salvar_relatorio` |
| IA/ML + NLP | Classificacao local do assunto textual | `radar_rpa/core.py`, TF-IDF e regressao logistica |
| RPA com Python | Orquestracao de lote, regras, logs, falhas e resultado | `radar_rpa/cli.py`, `main` e `processar` |
| BPM e processos | Modelagem de tarefas, gateways e tratamento de excecoes | `docs/FLUXO_BPMN.md` |
| Banco de dados | Persistencia da auditoria e idempotencia | SQLite em `radar_rpa/cli.py` |

## Protecao de dados, etica e ODS

Os testes trabalham com dados **sinteticos**. Nao ha credenciais nem chamadas a APIs de terceiros. CPF, e-mail e telefone sao mascarados por padroes, mas o metodo **nao anonimiza integralmente** nomes, locais e outras informacoes pessoais. Por isso, o prototipo nao deve ser usado com dados reais ou como ferramenta operacional da Defesa Civil. O foco e ODS 11 (Cidades e Comunidades Sustentaveis), com relacao ao ODS 13.

## Reproducao

No Windows, dentro da pasta do projeto, execute com o ambiente `.venv` instalado:

```powershell
.\.venv\Scripts\python.exe -m radar_rpa run --input dados\ocorrencias_demo.csv --output saida\demo
.\.venv\Scripts\python.exe -m radar_rpa validate --input dados\validacao_rotulada.csv --output saida\validacao
.\.venv\Scripts\python.exe -m pytest -q
```

Para testar a falha (codigo de saida 2, intencional):

```powershell
.\.venv\Scripts\python.exe -m radar_rpa run --input dados\arquivo_inexistente.csv --output saida\falha
```

## Limitacoes

Classificacao baseada em frases sinteticas, sem validacao externa; regras de urgencia podem falhar; nenhuma integracao meteorologica/Defesa Civil; mascara de PII limitada. A decisao de seguranca real exige profissionais e canais oficiais.
