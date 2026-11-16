# Fluxo de processo - BPM e BPMN (representacao simplificada)

O desenho usa evento inicial/final, tarefas e gateways de decisao. Nao representa integracao com a Defesa Civil: o sistema gera uma recomendacao, mas nao envia chamados externos.

```mermaid
flowchart TD
  A((Inicio)) --> B[Ler CSV de relatos]
  B --> C{Arquivo valido?}
  C -- Nao --> D[Registrar erro sem expor dados]
  D --> Z((Fim seguro))
  C -- Sim --> E[Validar cada linha]
  E --> F{Linha valida?}
  F -- Nao --> G[Registrar linha invalida]
  G --> K{Mais linhas?}
  F -- Sim --> H[Verificar duplicidade no SQLite]
  H --> I{Ja processada?}
  I -- Sim --> K
  I -- Nao --> J[Classificar texto localmente com NLP]
  J --> L{Sinal de urgencia ou baixa confianca?}
  L -- Sim --> M[Orientar encaminhamento / revisao humana]
  L -- Nao --> N[Orientacao geral segura]
  M --> O[Mascarar dados e registrar resultado]
  N --> O
  O --> K
  K -- Sim --> E
  K -- Nao --> P[Exportar CSV e resumo JSON]
  P --> Q((Fim))
```

**Limites:** prototipo academico; nao realiza diagnostico, previsao, despacho ou alerta oficial. Regras e modelos pequenos nao validam risco geotecnico ou meteorologico real.
