import sys
from pathlib import Path

# Permite importar os módulos de src/ (normalize, dados, matching) a partir desta subpasta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from rapidfuzz import fuzz, process

from dados import CAMINHO_CNEFE, carregar_busca, montar_grupos
from matching import localizar_rua
from normalize import chave_solta

busca = carregar_busca()
grupos = montar_grupos(busca)

cnefe = pd.read_parquet(CAMINHO_CNEFE, columns=["COD_MUNICIPIO", "logradouro_norm"])
tabela = {v: chave_solta(v) for v in cnefe["logradouro_norm"].dropna().unique()}
cnefe["chave"] = cnefe["logradouro_norm"].map(tabela)
chaves_por_mun = (
    cnefe[["COD_MUNICIPIO", "chave"]]
    .dropna()
    .drop_duplicates()
    .groupby("COD_MUNICIPIO")["chave"]
    .apply(list)
    .to_dict()
)

resultados = []
for _, linha in busca.iterrows():
    rua, _ = localizar_rua(linha, grupos)
    if rua is not None:
        continue  # 

    chave = linha["chave"]
    candidatos = chaves_por_mun.get(linha["consulta_municipio"], [])
    achados = []
    if pd.notna(chave) and candidatos:
        achados = process.extract(chave, candidatos, scorer=fuzz.ratio, limit=2)

    resultados.append({
        "consulta": linha["logradouro_norm"],
        "chave": chave,
        "melhor": achados[0][0] if achados else None,
        "nota": round(achados[0][1]) if achados else 0,
        "segunda_nota": round(achados[1][1]) if len(achados) > 1 else 0,
    })

diag = pd.DataFrame(resultados)
diag["margem"] = diag["nota"] - diag["segunda_nota"]
diag = diag.sort_values("nota", ascending=False)

pd.set_option("display.width", 250)
print(diag.to_string(index=False))
print(f"\nSem rua localizada: {len(diag)}")
print(f"Nota >= 90: {(diag['nota'] >= 90).sum()} | 80-89: {((diag['nota'] >= 80) & (diag['nota'] < 90)).sum()} | < 80: {(diag['nota'] < 80).sum()}")