from pathlib import Path

import pandas as pd

from dados import carregar_busca, carregar_cnefe, montar_grupos
from matching import aplicar_fallback, aplicar_fuzzy, resolver
from relatorio import resumir, salvar_excel

CAMINHO_CSV = "output/resultado.csv"
CAMINHO_XLSX = "output/resultado.xlsx"

busca = carregar_busca()
cnefe = carregar_cnefe()
busca = aplicar_fuzzy(busca, cnefe)
grupos = montar_grupos(busca, cnefe)
resultado = resolver(busca, grupos)
resultado = aplicar_fallback(busca, resultado, cnefe)

colunas_originais = [c for c in busca.columns if c.startswith("consulta_")]
final = pd.concat([busca[colunas_originais], resultado], axis=1)
final["setor_censitario_15dig"] = final["setor_censitario_encontrado"].str[:15]

final = final[colunas_originais + [
    "setor_censitario_encontrado",
    "setor_censitario_15dig",
    "status_vinculacao",
    "metodo_vinculacao",
    "n_setores_candidatos",
    "setores_candidatos",
]]

Path(CAMINHO_CSV).parent.mkdir(exist_ok=True)
final.to_csv(CAMINHO_CSV, sep=";", index=False, encoding="utf-8-sig")
salvar_excel(final, CAMINHO_XLSX)

por_status, _ = resumir(final)
print(f"Salvo em {CAMINHO_CSV} e {CAMINHO_XLSX}: {final.shape}")
print(por_status.to_string(index=False, formatters={"percentual": "{:.1%}".format}))