import pandas as pd

cnefe = pd.read_parquet("data/cnefe_bahia_filtrada.parquet")
busca = pd.read_csv("data/base_busca.csv", sep=";", dtype=str)

ceps_cnefe = set(cnefe["CEP"].dropna().unique())
busca["cep_existe"] = busca["consulta_cep"].isin(ceps_cnefe)
print(busca["cep_existe"].value_counts())

print("\n CEPs que não existem na base CNEFE:")
print(busca.loc[~busca["cep_existe"], ["consulta_logradouro", "consulta_cep", "consulta_municipio"]])

setores_por_cep = cnefe.groupby("CEP")["COD_SETOR"].nunique()
busca["n_setores_no_cep"] = busca["consulta_cep"].map(setores_por_cep)

print("\nSetores por CEP (para os CEPs da busca):")
print(busca["n_setores_no_cep"].value_counts(dropna=False).sort_index())