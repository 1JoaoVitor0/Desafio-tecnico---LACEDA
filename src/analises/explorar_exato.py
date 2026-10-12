import sys
from pathlib import Path

# Permite importar os módulos de src/ (normalize, dados, matching) a partir desta subpasta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from normalize import normalizar_texto

cnefe = pd.read_parquet(
    "data/cnefe_bahia_preparada.parquet",
    columns=["COD_MUNICIPIO", "COD_SETOR", "CEP", "logradouro_norm"]
)

busca = pd.read_csv(
    "data/base_busca.csv",
    sep=";",
    dtype=str)
busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)

ruas = (
    cnefe.groupby(["COD_MUNICIPIO", "logradouro_norm"])["COD_SETOR"]
    .nunique()
    .rename("n_setores_rua")
    .reset_index()
)

busca = busca.merge(
    ruas,
    how="left",
    left_on=["consulta_municipio", "logradouro_norm"],
    right_on=["COD_MUNICIPIO", "logradouro_norm"]
)

print(f"Linhas após o merge: {len(busca)} (devem ser 107)")

print("\nSetores por rua (NaN = rua não encontrada):")
print(busca["n_setores_rua"].value_counts(dropna=False).sort_index().to_string())

print("\nEndereços sem match exato:")
nao_achou = busca["n_setores_rua"].isna()
print(busca.loc[nao_achou, ["consulta_logradouro", "logradouro_norm", "consulta_municipio"]].to_string())