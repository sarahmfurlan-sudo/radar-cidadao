"""CLI para execução ponta a ponta do Radar Cidadão RPA."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .core import classificar, criar_modelo, identificador, proteger_dados

COLUNAS = ["id", "relato"]
SAIDA = ["id", "relato_anonimizado", "categoria", "confianca", "status", "orientacao"]


def preparar_log(pasta: Path) -> logging.Logger:
    pasta.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("radar_rpa")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(pasta / "execucao.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    return logger


def preparar_banco(caminho: Path) -> sqlite3.Connection:
    db = sqlite3.connect(caminho, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS execucoes (
        hash TEXT PRIMARY KEY, id_externo TEXT NOT NULL, categoria TEXT,
        status TEXT NOT NULL, data_utc TEXT NOT NULL
    )""")
    db.commit()
    return db


def seguro_csv(texto: str) -> str:
    """Mitiga interpretacao de valores como formulas ao abrir CSV em planilhas."""
    if texto and texto.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + texto
    return texto


def processar(entrada: Path, pasta: Path) -> dict:
    inicio = time.perf_counter()
    logger = preparar_log(pasta)
    relatorio = {"total_linhas": 0, "processados": 0, "invalidos": 0,
                 "duplicados": 0, "por_status": {}, "tempo_segundos": 0.0,
                 "saida": str(pasta / "resultados.csv"), "erros": []}
    contagens: Counter[str] = Counter()
    registros: list[dict] = []
    if not entrada.is_file():
        msg = "Arquivo de entrada ausente"
        logger.error("entrada_ausente caminho=%s", entrada)
        relatorio["erros"].append(msg)
        salvar_relatorio(pasta, relatorio)
        return relatorio

    try:
        with entrada.open("r", encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";")
            if not leitor.fieldnames or any(x not in leitor.fieldnames for x in COLUNAS):
                raise ValueError("CSV precisa conter colunas 'id' e 'relato' separadas por ponto e virgula")
            linhas = list(leitor)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        logger.error("entrada_invalida tipo=%s", type(exc).__name__)
        relatorio["erros"].append(str(exc))
        salvar_relatorio(pasta, relatorio)
        return relatorio

    modelo = criar_modelo()
    db = preparar_banco(pasta / "auditoria.sqlite3")
    try:
        for numero, linha in enumerate(linhas, 2):
            relatorio["total_linhas"] += 1
            try:
                codigo = str(linha.get("id") or "").strip()
                texto = str(linha.get("relato") or "").strip()
                if not codigo or not texto or len(texto) > 2000 or len(codigo) > 80:
                    raise ValueError("id/relato vazio ou tamanho acima do limite")
                # Idempotencia por id + texto bruto; o hash e armazenado, nunca o relato.
                chave = identificador(codigo + "\u241f" + texto)
                if db.execute("SELECT 1 FROM execucoes WHERE hash=?", (chave,)).fetchone():
                    relatorio["duplicados"] += 1
                    logger.info("linha=%s id_hash=%s status=duplicado", numero, identificador(codigo))
                    continue
                resultado = classificar(texto, modelo)
                registros.append({
                    "id": seguro_csv(codigo),
                    "relato_anonimizado": seguro_csv(proteger_dados(texto)),
                    "categoria": resultado.categoria,
                    "confianca": f"{resultado.confianca:.3f}",
                    "status": resultado.status,
                    "orientacao": resultado.orientacao,
                })
                db.execute("INSERT INTO execucoes VALUES (?, ?, ?, ?, ?)",
                           (chave, identificador(codigo), resultado.categoria, resultado.status,
                            datetime.now(timezone.utc).isoformat()))
                db.commit()
                contagens[resultado.status] += 1
                relatorio["processados"] += 1
                logger.info("linha=%s id_hash=%s categoria=%s status=%s", numero, identificador(codigo), resultado.categoria, resultado.status)
            except (ValueError, TypeError, KeyError, sqlite3.Error) as exc:
                relatorio["invalidos"] += 1
                logger.warning("linha=%s status=invalido tipo=%s", numero, type(exc).__name__)
                # nao incluir valores brutos do relato nem IDs pessoais nos logs
    finally:
        db.close()

    destino_csv = pasta / "resultados.csv"
    # Reexecucoes nao apagam resultados anteriores. Somente novos relatos sao anexados.
    primeiro_uso = not destino_csv.is_file()
    with destino_csv.open("a", encoding="utf-8-sig" if primeiro_uso else "utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=SAIDA, delimiter=";")
        if primeiro_uso:
            escritor.writeheader()
        escritor.writerows(registros)
    relatorio["por_status"] = dict(contagens)
    relatorio["tempo_segundos"] = round(time.perf_counter() - inicio, 3)
    salvar_relatorio(pasta, relatorio)
    return relatorio


def salvar_relatorio(pasta: Path, resumo: dict) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")


def avaliar(arquivo: Path, pasta: Path) -> dict:
    """Amostra rotulada separada do treinamento, medida real e reprodutivel."""
    pasta.mkdir(parents=True, exist_ok=True)
    modelo = criar_modelo()
    previstos = []
    with arquivo.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        if not leitor.fieldnames or not {"texto", "classe_esperada"}.issubset(leitor.fieldnames):
            raise ValueError("Rotulos precisam de texto;classe_esperada")
        for linha in leitor:
            resposta = classificar(linha["texto"], modelo, limiar=0.0)
            previstos.append({"esperado": linha["classe_esperada"], "previsto": resposta.categoria,
                              "acertou": linha["classe_esperada"] == resposta.categoria,
                              "texto_mascarado": proteger_dados(linha["texto"])})
    acertos = sum(x["acertou"] for x in previstos)
    resultado = {"amostra": len(previstos), "acertos": acertos,
                 "erros": len(previstos)-acertos,
                 "acuracia": round(acertos / len(previstos), 4) if previstos else None,
                 "observacao": "Conjunto sintetico pequeno. Nao mede desempenho em ocorrencias reais.",
                 "detalhes": previstos}
    (pasta / "validacao.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Radar Cidadao - RPA e IA local")
    comandos = p.add_subparsers(dest="comando", required=True)
    executar = comandos.add_parser("run", help="Processa relatos em CSV")
    executar.add_argument("--input", required=True, type=Path)
    executar.add_argument("--output", default=Path("saida"), type=Path)
    validar = comandos.add_parser("validate", help="Mede acertos em amostra sintetica rotulada")
    validar.add_argument("--input", default=Path("dados/validacao_rotulada.csv"), type=Path)
    validar.add_argument("--output", default=Path("evidencias"), type=Path)
    args = p.parse_args(argv)
    if args.comando == "run":
        resumo = processar(args.input, args.output)
        print(json.dumps(resumo, ensure_ascii=False, indent=2))
        return 0 if not resumo["erros"] else 2
    try:
        resultado = avaliar(args.input, args.output)
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"Falha de validacao: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({k: v for k, v in resultado.items() if k != "detalhes"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
