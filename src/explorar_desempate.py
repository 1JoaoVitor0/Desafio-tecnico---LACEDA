import pandas as pd

from normalize import chave_solta, normalizar_numero, normalizar_texto

cnefe = pd.read_parquet(
    "data/cnefe_bahia_preparada.parquet",
    columns=["COD_MUNICIPIO", "COD_SETOR", "CEP", "logradouro_norm", "numero_norm"],
)
tabela = {v: chave_solta(v) for v in cnefe["logradouro_norm"].dropna().unique()}
cnefe["chave"] = cnefe["logradouro_norm"].map(tabela)

busca = pd.read_csv("data/base_busca.csv", sep=";", dtype=str)
busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
busca["chave"] = busca["logradouro_norm"].apply(chave_solta)
busca["numero_norm"] = busca["consulta_numero"].apply(normalizar_numero)

chaves = busca[["consulta_municipio", "chave"]].dropna().drop_duplicates()
chaves.columns = ["COD_MUNICIPIO", "chave"]
candidatos = cnefe.merge(chaves, on=["COD_MUNICIPIO", "chave"], how="inner")
print(f"Linhas candidatas: {len(candidatos)}")

grupos = {k: g for k, g in candidatos.groupby(["COD_MUNICIPIO", "chave"])}


def desempatar(linha):
    g = grupos.get((linha["consulta_municipio"], linha["chave"]))
    if g is None:
        return "SEM_MATCH", None

    setores = g["COD_SETOR"].unique()
    if len(setores) == 1:
        return "RUA_SETOR_UNICO", setores[0]

    g_cep = g[g["CEP"] == linha["consulta_cep"]]
    if g_cep["COD_SETOR"].nunique() == 1:
        return "CEP", g_cep["COD_SETOR"].iloc[0]

    base = g_cep if len(g_cep) > 0 else g
    if pd.notna(linha["numero_norm"]):
        g_num = base[base["numero_norm"] == linha["numero_norm"]]
        if g_num["COD_SETOR"].nunique() == 1:
            return "NUMERO_EXATO", g_num["COD_SETOR"].iloc[0]

    return "AMBIGUO", None


busca[["metodo", "setor"]] = busca.apply(desempatar, axis=1, result_type="expand")

print(busca["metodo"].value_counts().to_string())

amb = busca[busca["metodo"] == "AMBIGUO"].copy()


def perfil(linha):
    g = grupos[(linha["consulta_municipio"], linha["chave"])]
    no_cep = g[g["CEP"] == linha["consulta_cep"]]
    return pd.Series({
        "n_setores": g["COD_SETOR"].nunique(),
        "cep_vazio": g["CEP"].isna().mean(),
        "setores_no_cep": no_cep["COD_SETOR"].nunique(),
        "peso_setor_top": g["COD_SETOR"].value_counts(normalize=True).iloc[0],
        "tem_numero": pd.notna(linha["numero_norm"]),
    })


perfis = amb.apply(perfil, axis=1)
print(f"\nAmbíguos: {len(perfis)}")
print("Com número na consulta:", perfis["tem_numero"].sum())
print("CEP da consulta aparece na rua:", (perfis["setores_no_cep"] > 0).sum())
print("Média de CEP vazio nas ruas:", round(perfis["cep_vazio"].astype(float).mean(), 2))
print("\nPeso do setor mais frequente da rua:")
print(perfis["peso_setor_top"].astype(float).describe().round(2).to_string())