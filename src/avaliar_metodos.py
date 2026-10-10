import pandas as pd

from dados import carregar_busca, montar_grupos


def mais_frequente(g):
    """Setor com mais endereços na rua."""
    return g["COD_SETOR"].value_counts().index[0]


def mais_proximo(g, n):
    """Setor cuja casa numerada está mais perto de n (None se ninguém tem número)."""
    num = pd.to_numeric(g["numero_norm"], errors="coerce")
    distancia = (num - n).abs()
    por_setor = distancia.groupby(g["COD_SETOR"]).min().dropna().sort_values()
    return por_setor.index[0] if len(por_setor) else None


busca = carregar_busca()
grupos = montar_grupos(busca)

casos = pd.concat(
    [g.dropna(subset=["numero_norm"]) for g in grupos.values() if g["COD_SETOR"].nunique() > 1]
)
amostra = casos.sample(min(3000, len(casos)), random_state=1)
print(f"Endereços avaliados: {len(amostra)}")

acertos = {"mais_frequente": 0, "numero_proximo": 0, "cep_e_numero": 0}
for idx, linha in amostra.iterrows():
    g = grupos[(linha["COD_MUNICIPIO"], linha["chave"])].drop(index=idx)
    n = int(linha["numero_norm"])
    verdadeiro = linha["COD_SETOR"]

    palpite_freq = mais_frequente(g)
    palpite_num = mais_proximo(g, n) or palpite_freq

    g_cep = g[g["CEP"] == linha["CEP"]]
    palpite_cep = mais_proximo(g_cep if len(g_cep) > 0 else g, n) or palpite_freq

    acertos["mais_frequente"] += palpite_freq == verdadeiro
    acertos["numero_proximo"] += palpite_num == verdadeiro
    acertos["cep_e_numero"] += palpite_cep == verdadeiro

print()
for nome, n_acertos in acertos.items():
    print(f"{nome}: {n_acertos / len(amostra):.1%}")