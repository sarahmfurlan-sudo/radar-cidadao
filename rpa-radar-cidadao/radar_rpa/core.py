"""Classificacao local e politica de orientacoes conservadoras.

Nao estima probabilidade real de desastre e nao substitui servicos publicos.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

CLASSES = ("alagamento", "deslizamento", "chuva_intensa", "outros")

# Dados de treino deliberadamente sinteticos. Nunca sao tratados como fonte oficial.
TREINO = {
    "alagamento": [
        "A rua esta cheia de agua da enchente", "Alagamento impediu passagem na avenida",
        "A agua do rio entrou no quintal", "A casa esta inundando depois da chuva",
        "O bueiro transbordou e a agua subiu", "A correnteza cobre a ponte do bairro",
        "Tem muita agua entrando no comercio", "O bairro foi atingido por inundacao",
        "A enxurrada invadiu a garagem", "Rua alagada perto da escola",
        "A margem do corrego transbordou", "Preciso de orientacao sobre enchente",
    ],
    "deslizamento": [
        "O barranco atras da casa esta rachando", "Uma encosta cedeu perto da escola",
        "Existe risco de deslizamento no morro", "Terra descendo do talude",
        "O muro esta inclinado e o solo abriu", "A lama desceu pela encosta",
        "A casa apresenta rachaduras apos chuva", "O morro deslizou perto do bairro",
        "Arvores inclinadas no barranco", "Pedras cairam da encosta",
        "O terreno comecou a escorregar", "Risco de queda de barreira na estrada",
    ],
    "chuva_intensa": [
        "Esta chovendo muito forte agora", "Chuva intensa com raios e trovoadas",
        "Recebi aviso de temporal no bairro", "Vento e chuva muito fortes",
        "A tempestade esta chegando", "Chove sem parar desde cedo",
        "Previsao de chuva forte hoje", "Rajadas de vento durante temporal",
        "Forte chuva causa preocupacao na regiao", "Chuva persistente nesta madrugada",
        "Tempestade e muitos relampagos", "Quero dicas antes de uma chuva intensa",
    ],
    "outros": [
        "Como fazer cadastro para biblioteca", "Quero saber o horario de um museu",
        "Preciso renovar documento de identidade", "O onibus atrasou hoje",
        "Como agendar atendimento municipal", "Tenho duvida sobre imposto",
        "Como solicitar segunda via de boleto", "Onde consultar servicos de educacao",
        "Quero receita de bolo", "Como consultar o calendario escolar",
        "Preciso trocar uma senha", "Quais parques estao abertos",
    ],
}

# As orientacoes sao deliberadamente genericas: nao afirmam a existencia de alerta oficial.
ORIENTACOES = {
    "alagamento": "Evite atravessar vias alagadas e contato com agua de enchente. Procure local seguro e acompanhe comunicados da Defesa Civil de sua cidade.",
    "deslizamento": "Afaste-se de encostas, barreiras e estruturas com sinais de instabilidade. Procure um local seguro e acione a Defesa Civil local.",
    "chuva_intensa": "Acompanhe os avisos da Defesa Civil e da meteorologia oficial. Evite areas alagadas, encostas e abrigo sob arvores durante tempestades.",
    "outros": "Este prototipo atende apenas orientacoes gerais sobre chuvas, alagamentos e deslizamentos. Consulte o orgao responsavel pelo assunto.",
}

# Regra conservadora tem precedencia sobre ML. "Urgente" aqui significa ENCAMINHAR,
# nunca classificar oficialmente a ocorrencia como emergencia real.
SINAIS_URGENTES = [
    r"\b(?:socorro|pres[oa]|presa|presos|presas|ferid[oa]s?|desaparecid[oa]s?|vitima|vitimas|soterrad[oa]s?)\b",
    r"\b(?:agua|água)\s+(?:est[aá]\s+)?entrando\s+(?:agora\s+)?(?:na|em)\s+(?:minha\s+)?casa\b",
    r"\b(?:casa|muro|barranco|encosta)\s+(?:est[aá]\s+)?(?:desabando|caindo|cedendo)\b",
    r"\b(?:fio|rede)\s+(?:eletric[oa]|elétric[oa])\s+(?:ca[iu]|caiu)\b",
]

CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?[\s-]*)?9?\d{4}[\s-]?\d{4}(?!\d)")


def proteger_dados(texto: str) -> str:
    """Mascara padroes de CPF, e-mail e telefone; nao detecta nomes/endereco."""
    return PHONE.sub("[TELEFONE]", EMAIL.sub("[EMAIL]", CPF.sub("[CPF]", texto)))


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def criar_modelo() -> Pipeline:
    textos, classes = [], []
    for classe, exemplos in TREINO.items():
        textos.extend(exemplos)
        classes.extend([classe] * len(exemplos))
    modelo = Pipeline([
        ("tfidf", TfidfVectorizer(strip_accents="unicode", analyzer="char_wb", ngram_range=(3, 5), lowercase=True)),
        ("classificador", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    modelo.fit(textos, classes)
    return modelo


@dataclass(frozen=True)
class Resultado:
    categoria: str
    confianca: float
    status: str
    orientacao: str


def classificar(texto: str, modelo: Pipeline, limiar: float = 0.35) -> Resultado:
    if not isinstance(texto, str) or not texto.strip():
        return Resultado("indefinido", 0.0, "revisao", "Relato ausente. Solicite nova descricao sem dados pessoais.")
    texto = texto.strip()
    if any(re.search(p, normalizar(texto)) for p in SINAIS_URGENTES):
        return Resultado(
            "possivel_urgencia", 1.0, "encaminhar_imediatamente",
            "Se houver perigo imediato, afaste-se da area de risco se isso for seguro e acione o servico de emergencia local (Defesa Civil 199 ou Bombeiros 193, no Brasil). Este sistema nao aciona esses servicos.",
        )
    probabilidades = modelo.predict_proba([texto])[0]
    classes = modelo.classes_
    indice = int(probabilidades.argmax())
    categoria = str(classes[indice])
    confianca = float(probabilidades[indice])
    if confianca < limiar:
        return Resultado(categoria, confianca, "revisao", "Relato inconclusivo. Encaminhar para revisao humana; nao emitir alerta automatico.")
    if categoria == "outros":
        return Resultado(categoria, confianca, "fora_escopo", ORIENTACOES[categoria])
    return Resultado(categoria, confianca, "orientacao_geral", ORIENTACOES[categoria])


def identificador(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]
