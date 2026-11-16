# Radar Cidadão — GS 2027: Fábrica de Corpus CitizenTech

Este pacote **não contém corpus inventado**. Ele fecha o processo com dados realmente gerados pelo projeto e valida exigências formais do enunciado.

## Como usar no Colab, sem refazer as gerações já executadas

1. No notebook em que estão carregados `segs`, `gerar`, `CACHE` e `geracao`, execute `FECHAMENTO_GS_19_NOV.ipynb` no mesmo runtime (ou copie as células para o notebook aberto). Se a sessão tiver reiniciado, execute as células de preparação do notebook original antes de prosseguir.
2. A primeira célula usa o código local do GitHub, commit 2907161, e não modifica o repositório.
3. A geração final só é executada se `qa` e `chat` existentes não tiverem as quantidades necessárias. Ela usa o mesmo cache (`CACHE`) e os mesmos segmentos, evitando retrabalho de consultas anteriores. A **geração pode ser lenta** se o cache ainda não contiver os resultados da escala completa.
4. Os JSONL, estatísticas, cinco amostras por corpus, planilha para revisão humana e relatório preliminar ficam em uma **nova pasta** do Drive `radar-cidadao/entrega_GS_19nov`, sem sobrescrever as v8.2/v8.3.
5. Preencha a planilha de revisão humana, confronte cada exemplo com o documento citado e inclua uma evidência antes/depois de anonimização no PDF.
6. Acrescente ao README final nomes completos dos integrantes, fontes exatas (documentos/URLs), bibliotecas, instruções para rodar e vídeo de até cinco minutos. Não declare o pacote final antes de passar em todos os critérios.

## Quantidades e formatos

- `corpus_texto.jsonl`: mínimo de 50 trechos, `text`, `fonte`.
- `corpus_qa.jsonl`: mínimo de 100 pares, `instruction`, `input`, `output`, `fonte`.
- `corpus_chat.jsonl`: mínimo de 30 diálogos, `messages` com `role`/`content`, pelo menos duas trocas e 10 recusas.
- `estatisticas.json`: quantidades, duplicatas, estimativas de tokens, erros. **Não equivale a validação semântica.**
- `revisao_humana_20_porcento.csv`: marcar S/N após conferir a fonte. A revisão não é preenchida automaticamente.

## Aviso de qualidade

O módulo exporta o que o modelo gerou, mas não inventa respostas para alcançar a meta. A validação automática detecta problemas estruturais e repetição da mesma pergunta; **não garante 90% de qualidade nem comprova que a resposta esteja no PDF**.

## Bibliotecas

Python, pacote original `nlp-fabrica-corpus` (spaCy, bibliotecas de extração, transformers, PyTorch), `reportlab` para o relatório PDF, bibliotecas-padrão `csv`, `json`, `hashlib`, `pathlib`.

## Integrantes

**PENDENTE: preencher nomes completos de todos os integrantes antes da entrega.**
