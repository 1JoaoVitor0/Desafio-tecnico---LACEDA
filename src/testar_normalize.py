import pandas as pd

from normalize import normalizar_numero, normalizar_texto

pd.set_option("display.width", 200)

busca = pd.read_csv("data/base_busca.csv", sep=";", dtype=str)

busca["logradouro_norm"] = busca["consulta_logradouro"].apply(normalizar_texto)
busca["numero_norm"] = busca["consulta_numero"].apply(normalizar_numero)

print(busca[["consulta_logradouro", "logradouro_norm", "consulta_numero", "numero_norm"]].head(20))

print("\nCasos com None literal:")
tem_none = busca["consulta_logradouro"].str.contains("None", na=False)
print(busca.loc[tem_none, ["consulta_logradouro", "logradouro_norm"]])