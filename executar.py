"""Executa o pipeline completo, pulando as etapas cujo produto já está atualizado.

Uso:
    python executar.py            # roda só o que estiver desatualizado
    python executar.py --forcar   # refaz tudo
"""
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

CNEFE_CSV = Path("data/cnefe_bahia.csv")
BASE_BUSCA = Path("data/base_busca.csv")
RESULTADO = Path("output/resultado.csv")
LOG = Path("output/log_execucao.txt")

ETAPAS = [
    (
        "1/3 Filtrar o CNEFE pelos municípios da base de busca",
        Path("src/filtrar_cnefe.py"),
        [CNEFE_CSV, BASE_BUSCA],
        Path("data/cnefe_bahia_filtrada.parquet"),
    ),
    (
        "2/3 Normalizar os logradouros do CNEFE",
        Path("src/preparar_cnefe.py"),
        [Path("data/cnefe_bahia_filtrada.parquet"), Path("src/normalize.py")],
        Path("data/cnefe_bahia_preparada.parquet"),
    ),
    (
        "3/3 Vincular os endereços aos setores censitários",
        Path("src/main.py"),
        [],
        None,
    ),
]


def desatualizado(produto, entradas):
    """True se o produto não existe ou é mais antigo que alguma das entradas."""
    if not produto.exists():
        return True
    return any(e.stat().st_mtime > produto.stat().st_mtime for e in entradas if e.exists())


def executar_etapa(descricao, script):
    """Roda um script com o mesmo Python (o do venv) e devolve a duração em segundos."""
    print(f"\n>>> {descricao}")
    inicio = time.time()
    subprocess.run([sys.executable, str(script)], check=True)
    return time.time() - inicio


def main():
    forcar = "--forcar" in sys.argv
    registro = []

    for descricao, script, entradas, produto in ETAPAS:
        entradas = entradas + [script]
        if produto is not None and not forcar and not desatualizado(produto, entradas):
            print(f"\n>>> {descricao}\n    pulada: {produto} já está atualizado (use --forcar para refazer)")
            registro.append(f"{descricao}: pulada")
            continue

        faltando = [e for e in entradas if not e.exists()]
        if faltando:
            sys.exit(f"Arquivo de entrada não encontrado: {faltando[0]}. Veja a seção 'Dados' do README.")
        try:
            duracao = executar_etapa(descricao, script)
        except subprocess.CalledProcessError:
            sys.exit(f"A etapa falhou: {descricao}. Veja a mensagem de erro acima.")
        registro.append(f"{descricao}: {duracao:.0f}s")

    contagem = pd.read_csv(RESULTADO, sep=";", dtype=str)["status_vinculacao"].value_counts()
    registro.append("Resultado por status: " + ", ".join(f"{k}={v}" for k, v in contagem.items()))

    LOG.parent.mkdir(exist_ok=True)
    cabecalho = f"Execução em {time.strftime('%Y-%m-%d %H:%M:%S')}"
    LOG.write_text(cabecalho + "\n" + "\n".join(registro) + "\n", encoding="utf-8")
    print(f"\nPronto. Log em {LOG}")


if __name__ == "__main__":
    main()