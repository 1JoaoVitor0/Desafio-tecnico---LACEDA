import re

import pandas as pd
from unidecode import unidecode

ABREVIACOES = {
    "R": "RUA",
    "AV": "AVENIDA",
    "AL": "ALAMEDA",
    "TV": "TRAVESSA",
    "PC": "PRACA",
    "ROD": "RODOVIA",
    "EST": "ESTRADA",
    "FAZ": "FAZENDA",
    "POV": "POVOADO",
    "DIST": "DISTRITO",
    "LOT": "LOTEAMENTO",
    "COND": "CONDOMINIO",
    "RES": "RESIDENCIAL",
    "JD": "JARDIM",
    "DR": "DOUTOR",
    "PROF": "PROFESSOR",
    "STA": "SANTA",
    "STO": "SANTO",
    "SR": "SENHOR",
    "CEL": "CORONEL",
    "ENG": "ENGENHEIRO",
}

VALORES_NULOS = {"NONE", "NAN", "NULL"}

STOPWORDS = {"DE", "DA", "DO", "DAS", "DOS", "E"}

TIPOS = {
    "RUA", "AVENIDA", "TRAVESSA", "ESTRADA", "FAZENDA", "RODOVIA", "POVOADO",
    "PRACA", "ALAMEDA", "LOTEAMENTO", "CONDOMINIO", "DISTRITO", "SITIO", "VILA",
    "CAMINHO", "BECO", "CONJUNTO", "COMUNIDADE", "ASSENTAMENTO", "CORREDOR", "VIA",
}

def normalizar_texto(texto):
    if pd.isna(texto):
        return None
    texto = unidecode(str(texto)).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    tokens = [t for t in texto.split() if t not in VALORES_NULOS]
    tokens = [ABREVIACOES.get(t, t) for t in tokens]
    resultado = " ".join(tokens)
    return resultado or None


def normalizar_numero(numero):
    if pd.isna(numero):
        return None
    digitos = re.sub(r"\D", "", str(numero))
    return digitos.lstrip("0") or None

def chave_solta(texto_normalizado):
    if texto_normalizado is None:
        return None
    tokens = [
        t for t in texto_normalizado.split()
        if t not in STOPWORDS and t not in TIPOS
    ]
    if not tokens:
        tokens = texto_normalizado.split()
    return " ".join(sorted(tokens)) or None