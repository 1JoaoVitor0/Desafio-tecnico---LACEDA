import pandas as pd

ENCONTRADO = "ENCONTRADO"
AMBIGUO = "AMBIGUO"
NAO_ENCONTRADO = "NAO_ENCONTRADO"

PREENCHER_AMBIGUOS = True
MAX_CANDIDATOS = 5


def mais_frequente(g):
    """Setor com mais endereços na rua."""
    return g["COD_SETOR"].value_counts().index[0]


def mais_proximo(g, n):
    """Setor cuja casa numerada está mais perto de n (None se ninguém tem número)."""
    num = pd.to_numeric(g["numero_norm"], errors="coerce")
    distancia = (num - n).abs()
    por_setor = distancia.groupby(g["COD_SETOR"]).min().dropna().sort_values()
    return por_setor.index[0] if len(por_setor) else None


def mais_proximo_mesmo_lado(g, n):
    """Igual a mais_proximo, mas só entre casas de mesma paridade (mesmo lado da rua)."""
    num = pd.to_numeric(g["numero_norm"], errors="coerce")
    return mais_proximo(g[num % 2 == n % 2], n)


def localizar_rua(linha, grupos):
    """Devolve (linhas do CNEFE da rua, tipo de match) ou (None, None)."""
    chave = linha["chave"]
    if pd.isna(chave):
        return None, None
    g = grupos.get((linha["consulta_municipio"], chave))
    if g is None:
        return None, None
    exata = g[g["logradouro_norm"] == linha["logradouro_norm"]]
    if len(exata) > 0:
        return exata, "RUA_EXATA"
    return g, "RUA_SOLTA"


def escolher_setor(rua, linha):
    """Devolve (setor, status, método, linhas consideradas) para uma rua já localizada."""
    setores = rua["COD_SETOR"].unique()
    if len(setores) == 1:
        return setores[0], ENCONTRADO, "SETOR_UNICO", rua

    no_cep = rua[rua["CEP"] == linha["consulta_cep"]]
    if no_cep["COD_SETOR"].nunique() == 1:
        return no_cep["COD_SETOR"].iloc[0], ENCONTRADO, "CEP", no_cep

    base = no_cep if len(no_cep) > 0 else rua
    sufixo = "_CEP" if len(no_cep) > 0 else ""

    if pd.notna(linha["numero_norm"]):
        n = int(linha["numero_norm"])
        iguais = base[base["numero_norm"] == linha["numero_norm"]]
        if iguais["COD_SETOR"].nunique() == 1:
            return iguais["COD_SETOR"].iloc[0], ENCONTRADO, "NUMERO_EXATO" + sufixo, base
        palpite = mais_proximo_mesmo_lado(base, n) or mais_proximo(base, n)
        if palpite is not None:
            return palpite, AMBIGUO, "NUMERO_PROXIMO" + sufixo, base

    return mais_frequente(base), AMBIGUO, "SETOR_MAIS_FREQUENTE" + sufixo, base


def resolver(busca, grupos):
    """Aplica a cascata a cada endereço da busca e devolve as colunas de resultado."""
    resultados = []
    for _, linha in busca.iterrows():
        rua, tipo_rua = localizar_rua(linha, grupos)
        if rua is None:
            resultados.append({
                "setor_censitario_encontrado": None,
                "status_vinculacao": NAO_ENCONTRADO,
                "metodo_vinculacao": "SEM_RUA",
                "n_setores_candidatos": 0,
                "setores_candidatos": None,
            })
            continue

        setor, status, metodo, base = escolher_setor(rua, linha)
        candidatos = base["COD_SETOR"].value_counts().index[:MAX_CANDIDATOS]
        if status == AMBIGUO and not PREENCHER_AMBIGUOS:
            setor = None
        resultados.append({
            "setor_censitario_encontrado": setor,
            "status_vinculacao": status,
            "metodo_vinculacao": f"{tipo_rua}+{metodo}",
            "n_setores_candidatos": base["COD_SETOR"].nunique(),
            "setores_candidatos": "|".join(candidatos) if status == AMBIGUO else None,
        })
    return pd.DataFrame(resultados, index=busca.index)