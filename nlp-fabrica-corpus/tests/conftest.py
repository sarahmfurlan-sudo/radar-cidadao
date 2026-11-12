"""Configuração dos testes: torna o pacote em src/ importável."""

import sys
from pathlib import Path

RAIZ_NLP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_NLP / "src"))
