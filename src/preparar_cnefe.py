import pandas as pd

from normalize import normalizar_numero, normalizar_texto

ENTRADA = "data/cnefe_bahia_filtrada.parquet"
SAIDA = "data/cnefe_bahia_preparada.parquet"


def normalizar_coluna(serie, funcao):
    unicos = serie.dropna().unique()
    tabela = {valor: funcao(valor) for valor in unicos}
    return serie.map(tabela)


cnefe = pd.read_parquet(ENTRADA)

partes = cnefe[["NOM_TIPO_SEGLOGR", "NOM_TITULO_SEGLOGR", "NOM_SEGLOGR"]].fillna("")
cnefe["logradouro_completo"] = (
    partes["NOM_TIPO_SEGLOGR"]
    + " "
    + partes["NOM_TITULO_SEGLOGR"]
    + " "
    + partes["NOM_SEGLOGR"]
)

cnefe["logradouro_norm"] = normalizar_coluna(cnefe["logradouro_completo"], normalizar_texto)
cnefe["numero_norm"] = normalizar_coluna(cnefe["NUM_ENDERECO"], normalizar_numero)

print(f"Linhas: {len(cnefe)}")
print(f"Logradouros distintos (texto bruto): {cnefe['logradouro_completo'].nunique()}")
print(f"Logradouros distintos (normalizados): {cnefe['logradouro_norm'].nunique()}")
print(f"Linhas sem número: {cnefe['numero_norm'].isna().mean():.1%}")

print("\nAmostra:")
print(
    cnefe[["NOM_TIPO_SEGLOGR", "NOM_TITULO_SEGLOGR", "NOM_SEGLOGR", "logradouro_norm", "numero_norm"]]
    .sample(10, random_state=1)
    .to_string()
)

cnefe.to_parquet(SAIDA, index=False)
print(f"\nSalvo em {SAIDA}")