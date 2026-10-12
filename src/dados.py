import pandas as pd

from normalize import chave_solta, normalizar_numero, normalizar_texto, tipo_logradouro

CAMINHO_BUSCA = "data/base_busca.csv"
CAMINHO_CNEFE = "data/cnefe_bahia_preparada.parquet"


def carregar_busca():
    busca = pd.read_csv(CAMINHO_BUSCA, sep=";", dtype=str)
    busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
    busca["chave"] = busca["logradouro_norm"].apply(chave_solta)
    busca["tipo"] = busca["logradouro_norm"].apply(tipo_logradouro)
    busca["numero_norm"] = busca["consulta_numero"].apply(normalizar_numero)
    busca["bairro_chave"] = busca["consulta_bairro"].apply(normalizar_texto).apply(chave_solta)
    busca["chave_cnefe"] = busca["chave"]
    return busca


def carregar_cnefe():
    """CNEFE já preparado, com a chave solta e o tipo de cada logradouro e a chave da localidade."""
    cnefe = pd.read_parquet(
        CAMINHO_CNEFE,
        columns=[
            "COD_MUNICIPIO", "COD_SETOR", "CEP", "logradouro_norm", "numero_norm", "DSC_LOCALIDADE",
        ],
    )
    nomes = cnefe["logradouro_norm"].dropna().unique()
    cnefe["chave"] = cnefe["logradouro_norm"].map({v: chave_solta(v) for v in nomes})
    cnefe["tipo"] = cnefe["logradouro_norm"].map({v: tipo_logradouro(v) for v in nomes})
    locais = cnefe["DSC_LOCALIDADE"].dropna().unique()
    cnefe["local_chave"] = cnefe["DSC_LOCALIDADE"].map(
        {v: chave_solta(normalizar_texto(v)) for v in locais}
    )
    return cnefe.drop(columns="DSC_LOCALIDADE")


def montar_grupos(busca, cnefe=None):
    """Devolve {(município, chave): linhas do CNEFE daquela rua}, só das ruas pedidas na busca."""
    if cnefe is None:
        cnefe = carregar_cnefe()
    chaves = busca[["consulta_municipio", "chave_cnefe"]].dropna().drop_duplicates()
    chaves.columns = ["COD_MUNICIPIO", "chave"]
    candidatos = cnefe.merge(chaves, on=["COD_MUNICIPIO", "chave"], how="inner")
    return {k: g for k, g in candidatos.groupby(["COD_MUNICIPIO", "chave"])}