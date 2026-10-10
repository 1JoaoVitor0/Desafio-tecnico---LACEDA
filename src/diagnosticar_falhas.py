import pandas as pd
from rapidfuzz import fuzz, process

from normalize import normalizar_texto

cnefe = pd.read_parquet(
    "data/cnefe_bahia_preparada.parquet",
    columns=["COD_MUNICIPIO", "CEP", "DSC_LOCALIDADE", "logradouro_norm"],
)
tabela = {v: normalizar_texto(v) for v in cnefe["DSC_LOCALIDADE"].dropna().unique()}
cnefe["localidade_norm"] = cnefe["DSC_LOCALIDADE"].map(tabela)


def conjuntos_por_municipio(coluna):
    """Devolve {município: conjunto dos valores distintos da coluna}."""
    return (
        cnefe[["COD_MUNICIPIO", coluna]]
        .dropna()
        .drop_duplicates()
        .groupby("COD_MUNICIPIO")[coluna]
        .apply(set)
        .to_dict()
    )


ruas_por_mun = conjuntos_por_municipio("logradouro_norm")
ceps_por_mun = conjuntos_por_municipio("CEP")
locais_por_mun = conjuntos_por_municipio("localidade_norm")
print("Índices por município prontos.")

busca = pd.read_csv("data/base_busca.csv", sep=";", dtype=str)
busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
busca["bairro_norm"] = busca["consulta_bairro"].apply(normalizar_texto)

resultados = []
for _, linha in busca.iterrows():
    mun = linha["consulta_municipio"]
    nome = linha["logradouro_norm"]
    ruas_mun = ruas_por_mun.get(mun, set())

    if nome in ruas_mun:
        continue 

    candidatos = list(ruas_mun)
    melhor = None
    if nome and candidatos:
        melhor = process.extractOne(nome, candidatos, scorer=fuzz.WRatio)
    locais = locais_por_mun.get(mun, set())

    resultados.append({
        "consulta": nome,
        "municipio": mun,
        "n_ruas_municipio": len(candidatos),
        "melhor_candidato": melhor[0] if melhor else None,
        "score": round(melhor[1]) if melhor else None,
        "cep_no_municipio": linha["consulta_cep"] in ceps_por_mun.get(mun, set()),
        "nome_e_localidade": nome in locais or linha["bairro_norm"] in locais,
    })

diag = pd.DataFrame(resultados).sort_values("score", ascending=False)
pd.set_option("display.width", 250)
print(diag.to_string(index=False))

print(f"\nSem match exato: {len(diag)}")
print(f"CEP existe no município: {diag['cep_no_municipio'].sum()}")
print(f"Nome ou bairro aparece como localidade: {diag['nome_e_localidade'].sum()}")
print(
    f"Score >= 90: {(diag['score'] >= 90).sum()} | "
    f"80-89: {((diag['score'] >= 80) & (diag['score'] < 90)).sum()} | "
    f"< 80: {(diag['score'] < 80).sum()}"
)