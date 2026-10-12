import sys
from pathlib import Path

# Permite importar os módulos de src/ (normalize, dados, matching) a partir desta subpasta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dados import carregar_busca, montar_grupos
from matching import localizar_rua

busca = carregar_busca()
grupos = montar_grupos(busca)

for _, linha in busca.iterrows():
    rua, tipo = localizar_rua(linha, grupos)
    if tipo == "RUA_SOLTA":
        nomes = rua["logradouro_norm"].value_counts().head(3)
        achados = " | ".join(f"{nome} ({n})" for nome, n in nomes.items())
        print(f"{linha['logradouro_norm']}  ->  {achados}")