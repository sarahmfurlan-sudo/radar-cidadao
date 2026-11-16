# Roteiro curto de demonstração da disciplina de RPA

1. Mostrar o CSV sintético com colunas `id;relato` e uma linha vazia de propósito.
2. Exibir o quadro de cinco temas reais no README e o diagrama em `FLUXO_BPMN.md`.
3. Rodar `python -m radar_rpa run --input dados/ocorrencias_demo.csv --output saida/demo`.
4. Abrir `saida/demo/resultados.csv`: mostrar classificação, encaminhamento conservador de urgência e máscaras `[CPF]`, `[EMAIL]`.
5. Abrir `saida/demo/resumo.json` e `saida/demo/execucao.log`: mostrar 1 linha inválida, sem derrubar o lote.
6. Repetir o mesmo comando para mostrar `duplicados` e preservação dos resultados.
7. Rodar `python -m radar_rpa validate --input dados/validacao_rotulada.csv --output saida/validacao`, abrir `validacao.json` e mostrar acertos e erros na amostra de 16 frases sintéticas (não representativa).
8. Rodar `python -m radar_rpa run --input dados/nao_existe.csv --output saida/falha` e mostrar `resumo.json` e o log de falha controlada. O comando retorna código de erro 2 de propósito.
9. Rodar `python -m pytest -q` e encerrar explicando as limitações e ODS 11.

Nunca afirmar que a classificação identifica emergências reais nem que os 16 exemplos provam precisão em campo.
