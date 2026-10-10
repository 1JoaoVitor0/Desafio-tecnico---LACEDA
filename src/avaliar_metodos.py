import pandas as pd

from dados import carregar_busca, montar_grupos

POR_RUA = 10

from matching import mais_frequente, mais_proximo, mais_proximo_mesmo_lado

busca = carregar_busca()
grupos = montar_grupos(busca)

partes = []
for g in grupos.values():
    if g["COD_SETOR"].nunique() > 1:
        com_numero = g.dropna(subset=["numero_norm"])
        if len(com_numero):
            partes.append(com_numero.sample(min(POR_RUA, len(com_numero)), random_state=1))
amostra = pd.concat(partes)
print(f"Ruas avaliadas: {len(partes)} | endereços avaliados: {len(amostra)}")

acertos = {}
for idx, linha in amostra.iterrows():
    g = grupos[(linha["COD_MUNICIPIO"], linha["chave"])].drop(index=idx)
    n = int(linha["numero_norm"])
    verdadeiro = linha["COD_SETOR"]

    freq = mais_frequente(g)
    g_cep = g[g["CEP"] == linha["CEP"]]
    base = g_cep if len(g_cep) > 0 else g

    palpites = {
        "mais_frequente": freq,
        "numero_proximo": mais_proximo(g, n) or freq,
        "cep_e_numero": mais_proximo(base, n) or freq,
        "cep_numero_mesmo_lado": mais_proximo_mesmo_lado(base, n) or mais_proximo(base, n) or freq,
        "cep_frequente (consulta sem numero)": mais_frequente(base),
    }
    for nome, palpite in palpites.items():
        acertos[nome] = acertos.get(nome, 0) + (palpite == verdadeiro)

print()
for nome, n_acertos in acertos.items():
    print(f"{nome}: {n_acertos / len(amostra):.1%}")