import pandas as pd

CAMINHO_BUSCAR = "data/base_busca.csv"
CAMINHO_CNEFE = "data/cnefe_bahia.csv"
CAMINHO_SAIDA = "data/cnefe_bahia_filtrada.parquet"

COLUNAS = [
    "COD_MUNICIPIO",
    "COD_SETOR",
    "CEP",
    "DSC_LOCALIDADE",
    "NOM_TIPO_SEGLOGR",
    "NOM_TITULO_SEGLOGR",
    "NOM_SEGLOGR",
    "NUM_ENDERECO",
    "DSC_MODIFICADOR",
]

busca = pd.read_csv(
    CAMINHO_BUSCAR,
    sep=";",
    dtype=str)

municipios = set(busca["consulta_municipio"].dropna().unique())

print(f"Municípios na base de busca: {len(municipios)}")

leitor = pd.read_csv(
    CAMINHO_CNEFE,
    sep=";",
    dtype=str,
    usecols=COLUNAS,
    chunksize=500_000
    )

pedacos = []
for i, pedaco in enumerate(leitor, start=1):
    pedaco["COD_MUNICIPIO"] = pedaco["COD_MUNICIPIO"].str[:6]
    mantidas = pedaco[pedaco["COD_MUNICIPIO"].isin(municipios)]
    pedacos.append(mantidas)
    print(f"Pedaço {i}: {len(pedaco)} linhas lidas, {len(mantidas)} mantidas")

cnefe = pd.concat(pedacos, ignore_index=True)
print(f"\nCnefe filtrada: {cnefe.shape}")
print("\nÙltima letra do COD_SETOR:")
print(cnefe["COD_SETOR"].str[-1].value_counts())

cnefe.to_parquet(CAMINHO_SAIDA, index=False)
print(f"\nSalvo em {CAMINHO_SAIDA}")

