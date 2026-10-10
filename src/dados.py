import pandas as pd

from normalize import chave_solta, normalizar_numero, normalizar_texto

CAMINHO_BUSCA = "data/base_busca.csv"
CAMINHO_CNEFE = "data/cnefe_bahia_preparada.parquet"


def carregar_busca():
    busca = pd.read_csv(CAMINHO_BUSCA, sep=";", dtype=str)
    busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
    busca["chave"] = busca["logradouro_norm"].apply(chave_solta)
    busca["numero_norm"] = busca["consulta_numero"].apply(normalizar_numero)
    return busca


def montar_grupos(busca):
    """Devolve {(município, chave): linhas do CNEFE daquela rua}, só das ruas pedidas na busca."""
    cnefe = pd.read_parquet(
        CAMINHO_CNEFE,
        columns=["COD_MUNICIPIO", "COD_SETOR", "CEP", "logradouro_norm", "numero_norm"],
    )
    tabela = {v: chave_solta(v) for v in cnefe["logradouro_norm"].dropna().unique()}
    cnefe["chave"] = cnefe["logradouro_norm"].map(tabela)

    chaves = busca[["consulta_municipio", "chave"]].dropna().drop_duplicates()
    chaves.columns = ["COD_MUNICIPIO", "chave"]
    candidatos = cnefe.merge(chaves, on=["COD_MUNICIPIO", "chave"], how="inner")
    return {k: g for k, g in candidatos.groupby(["COD_MUNICIPIO", "chave"])}