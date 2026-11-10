"""Gera o DOCX de teste a partir do TXT de teste.

Uso:
    python gerar_docx.py teste_dados_ficticios.txt teste_dados_ficticios.docx

O DOCX tem o mesmo texto do TXT (um parágrafo por linha não vazia) e, no fim,
uma tabela de contatos para testar a extração de tabelas.
Todos os dados pessoais são fictícios.
Requer: python-docx
"""

import sys

from docx import Document

txt, saida = sys.argv[1], sys.argv[2]
with open(txt, encoding="utf-8") as f:
    linhas = f.read().splitlines()

doc = Document()
for i, linha in enumerate(linhas):
    if not linha.strip():
        continue  # linha em branco no TXT = separação de parágrafo
    p = doc.add_paragraph()
    run = p.add_run(linha)
    if i == 0 or linha == "Equipe responsável pelo registro":
        run.bold = True  # aviso inicial e título dos créditos em negrito

doc.add_paragraph().add_run("Tabela de contatos").bold = True
dados = [
    ("Nome", "CPF", "E-mail", "Telefone"),
    ("Mariana Toledo Vasconcelos", "123.456.789-10", "mariana.toledo@example.com", "(20) 99999-0001"),
    ("Joaquim Pereira Lins", "987.654.321-99", "joaquim.lins@example.com", "+55 20 98888-0002"),
]
tabela = doc.add_table(rows=len(dados), cols=4)
tabela.style = "Table Grid"
for r, linha in enumerate(dados):
    for c, valor in enumerate(linha):
        tabela.cell(r, c).text = valor

doc.save(saida)
print("DOCX salvo:", saida)
