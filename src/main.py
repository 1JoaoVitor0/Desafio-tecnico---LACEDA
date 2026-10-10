from pathlib import Path

import pandas as pd

from dados import carregar_busca, montar_grupos
from matching import resolver

CAMINHO_SAIDA = "output/resultado.csv"

busca = carregar_busca()
grupos = montar_grupos(busca)
resultado = resolver(busca, grupos)

colunas_originais = [c for c in busca.columns if c.startswith("consulta_")]
final = pd.concat([busca[colunas_originais], resultado], axis=1)
final["setor_censitario_15dig"] = final["setor_censitario_encontrado"].str[:15]

Path(CAMINHO_SAIDA).parent.mkdir(exist_ok=True)
final.to_csv(CAMINHO_SAIDA, sep=";", index=False, encoding="utf-8-sig")

print(f"Salvo em {CAMINHO_SAIDA}: {final.shape}")
print(final["status_vinculacao"].value_counts().to_string())
print(final["metodo_vinculacao"].value_counts().to_string())