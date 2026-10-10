import pandas as pd

from normalize import chave_solta, normalizar_texto

cnefe = pd.read_parquet(
    "data/cnefe_bahia_preparada.parquet",
    columns=["COD_MUNICIPIO", "COD_SETOR", "logradouro_norm"],
)

tabela = {v: chave_solta(v) for v in cnefe["logradouro_norm"].dropna().unique()}
cnefe["chave"] = cnefe["logradouro_norm"].map(tabela)

ruas = (
    cnefe.groupby(["COD_MUNICIPIO", "chave"])["COD_SETOR"]
    .nunique()
    .rename("n_setores_chave")
    .reset_index()
)

busca = pd.read_csv("data/base_busca.csv", sep=";", dtype=str)
busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
busca["chave"] = busca["logradouro_norm"].apply(chave_solta)

busca = busca.merge(
    ruas,
    left_on=["consulta_municipio", "chave"],
    right_on=["COD_MUNICIPIO", "chave"],
    how="left",
)

print(f"Linhas após o merge: {len(busca)} (devem ser 107)")
print("\nSetores por chave (NaN = sem match):")
print(busca["n_setores_chave"].value_counts(dropna=False).sort_index().to_string())

print("\nAinda sem match:")
print(busca.loc[busca["n_setores_chave"].isna(), ["logradouro_norm", "chave", "consulta_municipio"]].to_string())