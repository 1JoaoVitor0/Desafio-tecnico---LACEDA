import pandas as pd
from rapidfuzz import fuzz, process

ENCONTRADO = "ENCONTRADO"
AMBIGUO = "AMBIGUO"
NAO_ENCONTRADO = "NAO_ENCONTRADO"

PREENCHER_AMBIGUOS = True
MAX_CANDIDATOS = 5

NOTA_MINIMA = 90
MARGEM_MINIMA = 10
PESO_MINIMO_FALLBACK = 0.40


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


def aplicar_fuzzy(busca, cnefe):
    """Para consultas cuja rua não existe no município, tenta corrigir erros de grafia."""
    chaves_por_mun = (
        cnefe[["COD_MUNICIPIO", "chave"]]
        .dropna()
        .drop_duplicates()
        .groupby("COD_MUNICIPIO")["chave"]
        .apply(list)
        .to_dict()
    )
    saida = busca.copy()
    for i, linha in busca.iterrows():
        chave = linha["chave"]
        candidatos = chaves_por_mun.get(linha["consulta_municipio"], [])
        if pd.isna(chave) or not candidatos or chave in candidatos:
            continue 
        achados = process.extract(chave, candidatos, scorer=fuzz.ratio, limit=2)
        melhor, nota = achados[0][0], achados[0][1]
        segunda = achados[1][1] if len(achados) > 1 else 0
        if nota >= NOTA_MINIMA and nota - segunda >= MARGEM_MINIMA:
            saida.at[i, "chave_cnefe"] = melhor
    return saida


def localizar_rua(linha, grupos):
    """Devolve (linhas do CNEFE da rua, tipo de match) ou (None, None)."""
    chave = linha["chave_cnefe"]
    if pd.isna(chave):
        return None, None
    g = grupos.get((linha["consulta_municipio"], chave))
    if g is None:
        return None, None

    exata = g[g["logradouro_norm"] == linha["logradouro_norm"]]
    if len(exata) > 0:
        return exata, "RUA_EXATA"

    tipo = linha["tipo"]
    if pd.isna(tipo):
        return g, "RUA_TIPO_COMPATIVEL"
    compativel = g[g["tipo"].isna() | (g["tipo"] == tipo)]
    if len(compativel) > 0:
        return compativel, "RUA_TIPO_COMPATIVEL"
    return g, "RUA_TIPO_DIFERENTE"


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

        fuzzy = linha["chave_cnefe"] != linha["chave"]
        setor, status, metodo, base = escolher_setor(rua, linha)
        if status == ENCONTRADO and (fuzzy or tipo_rua == "RUA_TIPO_DIFERENTE"):
            status = AMBIGUO 

        candidatos = base["COD_SETOR"].value_counts().index[:MAX_CANDIDATOS]
        if status == AMBIGUO and not PREENCHER_AMBIGUOS:
            setor = None
        resultados.append({
            "setor_censitario_encontrado": setor,
            "status_vinculacao": status,
            "metodo_vinculacao": ("FUZZY_" if fuzzy else "") + f"{tipo_rua}+{metodo}",
            "n_setores_candidatos": base["COD_SETOR"].nunique(),
            "setores_candidatos": "|".join(candidatos) if status == AMBIGUO else None,
        })
    return pd.DataFrame(resultados, index=busca.index)

def _contar(cnefe, coluna):
    """Quantos endereços do CNEFE há em cada (município, valor da coluna, setor)."""
    return cnefe.groupby(["COD_MUNICIPIO", coluna, "COD_SETOR"]).size().rename("n").reset_index()


def _grupo(cont, coluna, municipio, valor):
    """(peso do setor dominante, setores do mais ao menos frequente) de um grupo, ou None."""
    if pd.isna(valor):
        return None
    g = cont[(cont["COD_MUNICIPIO"] == municipio) & (cont[coluna] == valor)]
    if g.empty:
        return None
    g = g.sort_values("n", ascending=False)
    return g["n"].iloc[0] / g["n"].sum(), list(g["COD_SETOR"])


def aplicar_fallback(busca, resultado, cnefe):
    """Para NAO_ENCONTRADO, tenta o CEP, o nome ou o bairro (como localidade) do CNEFE.

    Usa a fonte cujo setor dominante pesa mais e só aceita se o peso passar de
    PESO_MINIMO_FALLBACK. O resultado é sempre AMBIGUO (é uma estimativa)."""
    cont_cep = _contar(cnefe, "CEP")
    cont_loc = _contar(cnefe, "local_chave")
    saida = resultado.copy()
    for i, linha in busca.iterrows():
        if resultado.at[i, "status_vinculacao"] != NAO_ENCONTRADO:
            continue
        mun = linha["consulta_municipio"]
        fontes = {
            "CEP": _grupo(cont_cep, "CEP", mun, linha["consulta_cep"]),
            "LOCALIDADE_NOME": _grupo(cont_loc, "local_chave", mun, linha["chave"]),
            "LOCALIDADE_BAIRRO": _grupo(cont_loc, "local_chave", mun, linha["bairro_chave"]),
        }
        fontes = {nome: g for nome, g in fontes.items() if g is not None}
        if not fontes:
            continue
        nome, (peso, setores) = max(fontes.items(), key=lambda item: item[1][0])
        if peso < PESO_MINIMO_FALLBACK:
            continue
        saida.at[i, "setor_censitario_encontrado"] = setores[0] if PREENCHER_AMBIGUOS else None
        saida.at[i, "status_vinculacao"] = AMBIGUO
        saida.at[i, "metodo_vinculacao"] = f"FALLBACK_{nome}"
        saida.at[i, "n_setores_candidatos"] = len(setores)
        saida.at[i, "setores_candidatos"] = "|".join(setores[:MAX_CANDIDATOS])
    return saida