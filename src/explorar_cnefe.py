import pandas as pd

CAMINHO_CNEFE = "data/cnefe_bahia.csv"

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

df = pd.read_csv(
    CAMINHO_CNEFE,
    sep=";", 
    dtype = str,
    usecols=COLUNAS,
    nrows = 500_000,
    )

print(df.shape)
print(df.dtypes)
print(df.head())

print("\n--- Tamanho de COD_MUNICIPIO ---")
print(df["COD_MUNICIPIO"].str.len().value_counts())

print("\n--- Tamanho de COD_SETOR ---")
print(df["COD_SETOR"].str.len().value_counts())

print("\n--- Último caractere de COD_SETOR ---")
print(df["COD_SETOR"].str[-1].value_counts())

print("\n--- 20 tipos de logradouro mais frequentes ---")
print(df["NOM_TIPO_SEGLOGR"].value_counts(dropna=False).head(20))

pct_sem_denominacao = (df["NOM_SEGLOGR"] == "SEM DENOMINACAO").mean() * 100
print(f"\n% de SEM DENOMINACAO: {pct_sem_denominacao:.1f}%")

print("\n--- Como aparece o 'sem número' ---")
sem_numero = df[df["NUM_ENDERECO"] == "0"]
print(sem_numero["DSC_MODIFICADOR"].value_counts(dropna=False))