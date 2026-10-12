import sys
from pathlib import Path

# Permite importar os módulos de src/ (normalize, dados, matching) a partir desta subpasta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from dados import CAMINHO_CNEFE
from normalize import chave_solta, normalizar_texto

res = pd.read_csv("output/resultado.csv", sep=";", dtype=str)
falhas = res[res["status_vinculacao"] == "NAO_ENCONTRADO"].copy()
falhas["nome_chave"] = falhas["consulta_logradouro"].apply(normalizar_texto).apply(chave_solta)
falhas["bairro_chave"] = falhas["consulta_bairro"].apply(normalizar_texto).apply(chave_solta)

cnefe = pd.read_parquet(
    CAMINHO_CNEFE, columns=["COD_MUNICIPIO", "COD_SETOR", "CEP", "DSC_LOCALIDADE"]
)
locais = cnefe["DSC_LOCALIDADE"].dropna().unique()
cnefe["local_chave"] = cnefe["DSC_LOCALIDADE"].map(
    {v: chave_solta(normalizar_texto(v)) for v in locais}
)


def anexar(falhas, col_cnefe, col_falhas, sufixo):
    """Anexa a cada falha o nº de setores e o peso do setor dominante do grupo (município, valor)."""
    cont = cnefe.groupby(["COD_MUNICIPIO", col_cnefe, "COD_SETOR"]).size()
    grupo = cont.groupby(level=[0, 1])
    resumo = pd.DataFrame({
        f"n_setores_{sufixo}": grupo.size(),
        f"peso_{sufixo}": grupo.max() / grupo.sum(),
    }).reset_index()
    resumo = resumo.rename(columns={"COD_MUNICIPIO": "consulta_municipio", col_cnefe: col_falhas})
    return falhas.merge(resumo, on=["consulta_municipio", col_falhas], how="left")


falhas = anexar(falhas, "CEP", "consulta_cep", "cep")
falhas = anexar(falhas, "local_chave", "nome_chave", "nome")
falhas = anexar(falhas, "local_chave", "bairro_chave", "bairro")

colunas = [
    "consulta_logradouro", "consulta_municipio", "consulta_cep",
    "n_setores_cep", "peso_cep", "n_setores_nome", "peso_nome",
    "n_setores_bairro", "peso_bairro",
]
pd.set_option("display.width", 250)
print(falhas[colunas].round(2).to_string(index=False))

print(f"\nFalhas analisadas: {len(falhas)}")
for rotulo, col in [
    ("CEP", "peso_cep"),
    ("nome como localidade", "peso_nome"),
    ("bairro como localidade", "peso_bairro"),
]:
    existe = falhas[col].notna().sum()
    forte = (falhas[col] >= 0.5).sum()
    print(f"{rotulo}: existe em {existe} | setor dominante com peso >= 0,5 em {forte}")