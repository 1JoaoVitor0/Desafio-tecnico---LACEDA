# Vinculação de endereços a setores censitários (CNEFE Bahia)

Solução do teste prático de Engenharia de Dados Jr. Dado um conjunto de endereços de qualidade variável (a base de busca), o pipeline localiza cada um no Cadastro Nacional de Endereços para Fins Estatísticos (CNEFE) da Bahia e devolve o setor censitário correspondente.

A saída é a própria base de busca acrescida do setor, de um **status** (`ENCONTRADO`, `AMBIGUO` ou `NAO_ENCONTRADO`) e do **método** que produziu cada resposta, de modo que cada linha pode ser auditada.

## Resultado

A base de busca tem 107 endereços (o enunciado cita 100), distribuídos em 78 municípios.

| Status | Endereços | % | Como ler |
|---|---|---|---|
| `ENCONTRADO` | 16 | 15,0% | Rua localizada e setor decidido com alta confiança |
| `AMBIGUO` | 65 | 60,7% | Há um palpite informado para o setor, mas ele não é certo. A coluna do setor traz o melhor palpite e `setores_candidatos` lista as alternativas |
| `NAO_ENCONTRADO` | 26 | 24,3% | Nenhum sinal confiável. O setor fica vazio |

A seção [Confiabilidade](#confiabilidade) detalha o que está por trás de cada grupo.

### Arquivos de saída (`output/`)

| Arquivo | Conteúdo |
|---|---|
| `resultado.csv` | **Entrega principal.** Todas as linhas e colunas da base de busca, sem alteração, mais as colunas abaixo. Separador `;`, UTF-8 com BOM |
| `resultado.xlsx` | O mesmo conteúdo, para leitura: cores por status, filtros, aba de resumo e aba de legenda |
| `log_execucao.txt` | Data, tempo de cada etapa e contagem final por status |

| Coluna acrescentada | Descrição |
|---|---|
| `setor_censitario_encontrado` | `COD_SETOR` do CNEFE (16 caracteres: 15 dígitos + letra). Vazio quando `NAO_ENCONTRADO` |
| `setor_censitario_15dig` | O mesmo setor sem a letra final |
| `status_vinculacao` | `ENCONTRADO`, `AMBIGUO` ou `NAO_ENCONTRADO` |
| `metodo_vinculacao` | Como o setor foi decidido, por exemplo `RUA_EXATA+NUMERO_PROXIMO_CEP`. O prefixo `FUZZY_` indica rua achada por correção de grafia, e `FALLBACK_` indica setor estimado pelo CEP ou pela localidade |
| `n_setores_candidatos` | Quantos setores diferentes existem entre os candidatos considerados |
| `setores_candidatos` | Até 5 setores mais frequentes, separados por `\|` (apenas nos `AMBIGUO`) |

## Como executar

### Pré-requisitos

Python 3.11 (desenvolvido em 3.11.9) e cerca de 2 GB livres em disco, por causa do CSV do CNEFE.

### 1. Dados

- **Base de busca:** já está no repositório, em `data/base_busca.csv`.
- **CNEFE Bahia:** o arquivo usado é o `29_BA.zip` disponibilizado pelo **link alternativo do enunciado** (item "https://fiocruzbr-my.sharepoint.com/:u:/g/personal/robespierre_pita_fiocruz_br/IQBffC24BhqdR6YxIj-uwH3cAZQO3HzIQLBZocKpMmR7PkE?e=RAynjl"). Extraia o `29_BA.csv` (1,46 GB) e salve como **`data/cnefe_bahia.csv`**. O arquivo não está no repositório por causa do tamanho. A [página do CNEFE no IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html) traz a documentação e os downloads oficiais, mas o pipeline foi desenvolvido e validado apenas com o arquivo do link alternativo. Arquivos de outra origem podem ter estrutura diferente e não foram testados.

### 2. Ambiente

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Execução

Na raiz do repositório:

```powershell
python executar.py
```

Saída esperada ao final:

```
        status  enderecos percentual
    ENCONTRADO         16      15.0%
       AMBIGUO         65      60.7%
NAO_ENCONTRADO         26      24.3%
```

O `executar.py` roda as três etapas na ordem e grava tudo em `output/`:

1. `src/filtrar_cnefe.py`: lê o CNEFE em pedaços e mantém só os municípios da base de busca. É a etapa mais demorada, por ler o CSV de 1,4 GB.
2. `src/preparar_cnefe.py`: monta e normaliza o logradouro de cada endereço do CNEFE.
3. `src/main.py`: vincula os endereços e grava os resultados.

Cada etapa só é refeita se o produto não existir ou for mais antigo que alguma entrada (compara-se a data de modificação dos arquivos). Por isso, nas execuções seguintes a etapa 1 é pulada. `python executar.py --forcar` refaz tudo. O pipeline é determinístico: a única amostragem do projeto, na validação interna, usa semente fixa.

## Como funciona

### Os dados

**CNEFE Bahia:** 9.047.296 endereços. O logradouro vem dividido em tipo, título e nome (`AVENIDA` + `VEREADOR` + `JOAO SILVA`). O município tem 7 dígitos (com verificador) e o setor, 16 caracteres. 20,2% dos endereços dos municípios da busca não têm número, e esses casos aparecem como `NUM_ENDERECO = 0` com modificador `SN`.

**Base de busca:** o logradouro vem numa coluna só, e a qualidade varia. Há `None` colado no início de alguns logradouros, "sem número" escrito de três formas (vazio, `SN` e `S/N`, em 34% dos endereços), erros de digitação (`EPFANIA`, `DEABRIL`), nomes rurais (`FAZENDA BICO`) e códigos no lugar do nome (`RUA QD S15 RUA 07 N09`).

### Visão geral

```
cnefe_bahia.csv (1,4 GB, 9,05 M linhas)
   │  1. filtrar: 78 municípios da busca
   ▼
cnefe_bahia_filtrada.parquet (3,89 M linhas, 44,7 MB)
   │  2. preparar: logradouro completo e número normalizados
   ▼
cnefe_bahia_preparada.parquet
   │  3. vincular: localizar a rua, escolher o setor, estimar o que sobrar
   ▼
output/resultado.csv  +  resultado.xlsx  +  log_execucao.txt
```

### Normalização

A mesma função trata os dois lados: remove acentos, coloca em maiúsculas, tira pontuação, descarta o `None` que sobrou da exportação (era o tipo do logradouro, nulo), expande abreviações e unifica as formas de "sem número". No CNEFE, o logradouro é montado concatenando tipo, título e nome.

### Localizar a rua

A busca fica restrita ao município da consulta. Os critérios são aplicados em ordem, e os endereços que sobram passam para o seguinte:

| Critério | Regra | Endereços | Resultado máximo |
|---|---|---|---|
| Nome exato | Logradouro normalizado igual ao do CNEFE | 43 | `ENCONTRADO` |
| Chave solta | Compara sem tipo e sem artigos (`DE`, `DA`, `DO`...), com as palavras em ordem alfabética, o que cobre diferenças de artigo, de ordem e de tipo ausente. Prefere o tipo igual ou ausente | +19 | `ENCONTRADO` com tipo compatível (7); `AMBIGUO` com tipo diferente (12) |
| Correção de grafia | Similaridade do texto inteiro (`rapidfuzz`), aceita com nota 90 ou mais **e** segundo colocado a pelo menos 10 pontos | +12 | `AMBIGUO` |

Ao todo, 74 dos 107 endereços têm a rua localizada.

### Escolher o setor

Entre os candidatos da rua, a ordem é:

1. a rua tem um único setor: resolvido (`ENCONTRADO`);
2. o CEP da consulta restringe a rua a um setor: resolvido (`ENCONTRADO`);
3. o número exato aparece em um só setor: resolvido (`ENCONTRADO`);
4. com número: o setor da casa de número mais próximo, na mesma paridade (mesmo lado da rua) e dentro do CEP quando ele aparece na rua (`AMBIGUO`);
5. sem número: o setor mais frequente, dentro do CEP quando possível (`AMBIGUO`).

### Fallback para quem ficou sem rua

Para os endereços sem rua localizada, o pipeline olha três sinais: o CEP, o nome do logradouro e o bairro, estes dois comparados com a localidade do CNEFE (`DSC_LOCALIDADE`). Usa o sinal cujo setor dominante concentra a maior fração dos endereços do grupo, e só aceita se essa fração for pelo menos **0,40**. O resultado é sempre `AMBIGUO`.

## Decisões fundamentadas nos dados

Cada regra acima veio de uma medição, e os scripts estão em `src/analises/`.

- **O CEP não serve de chave.** 97 dos 107 CEPs existem no CNEFE, mas só um endereço tem um CEP que corresponde a um setor único. Os CEPs rurais cobrem o município inteiro, com até 246 setores. O CEP entra como reforço do desempate, nunca como critério de busca.
- **Município é o bloqueio, e o nome da rua é a chave.** Depois do filtro por município ainda restam 3,89 milhões de linhas, o que obriga a comparar por nome.
- **A chave solta tem um custo.** Ao tirar o tipo da comparação, `RUA CATUABINHA` casa com `FAZENDA CATUABINHA`. A auditoria dos 19 casos resgatados mostrou 7 com o mesmo logradouro (diferença de artigo, ordem ou tipo ausente) e 12 com tipo diferente. Por isso o tipo diferente nunca resulta em `ENCONTRADO`.
- **A correção de grafia usa a similaridade do texto inteiro** (`fuzz.ratio`). A medida composta testada primeiro (`WRatio`) dava nota alta a candidatos curtos: `RUA A` recebia 90 contra `RUA ARCO VERDE`. A margem de 10 pontos evita escolher entre dois candidatos parecidos (`ANTONIO CASAES` teve 97 contra 93 e ficou de fora).
- **A correção de grafia nunca resulta em `ENCONTRADO`.** Um nome próprio que difere de uma letra pode ser outra pessoa: `MARIA ANDRADE` foi aceita como `MARIO ANDRADE` (nota 92), e nota nenhuma distingue isso.
- **O número mais próximo, dentro do CEP, foi o desempate que mais acertou** na validação interna (próxima seção).
- **O limite do fallback (0,40) fica numa lacuna dos dados.** Entre os 33 endereços sem rua, 7 têm um sinal com peso de 0,46 a 0,93, e o seguinte vale 0,35. Os demais têm de 2% a 35% de chance, e preencher isso seria ruído com cara de resposta.

## Confiabilidade

### Por origem da resposta

| Origem | Endereços | Leitura |
|---|---|---|
| `ENCONTRADO` | 16 | Rua certa (nome exato ou tipo compatível) e setor decidido |
| `AMBIGUO`, rua certa e setor palpitado | 34 | Acerto validado de 49% a 80%, conforme o método (tabela abaixo) |
| `AMBIGUO`, tipo de logradouro diferente | 12 | A rua pode ser outro lugar. Sem validação |
| `AMBIGUO`, rua achada por correção de grafia | 12 | Sem validação |
| `AMBIGUO`, fallback por CEP ou localidade | 7 | Peso do setor dominante de 0,46 a 0,93. Esperam-se cerca de 4 acertos |
| `NAO_ENCONTRADO` | 26 | Sem resposta |

### Validação interna dos métodos de desempate

Não há padrão ouro disponível, então a taxa de acerto geral não pode ser medida. A validação interna esconde um endereço do próprio CNEFE (cujo setor se conhece), aplica o método e compara com o setor verdadeiro. Foram 538 endereços de 55 ruas que têm mais de um setor, no máximo 10 por rua, para imitar a base de busca, que tem um endereço por rua:

| Método | Acerto |
|---|---|
| Setor mais frequente da rua | 48,7% |
| Número mais próximo | 69,7% |
| CEP + número mais próximo | 77,3% |
| CEP + número mais próximo, mesmo lado da rua | 79,6% |
| CEP + setor mais frequente (consulta sem número) | 57,2% |

Cuidados na leitura: são tetos, e não a taxa da solução. O teste usa o CEP verdadeiro de cada endereço, enquanto na busca 13 dos 53 endereços ambíguos da primeira versão têm CEP que não aparece na rua. Também exclui as ruas não encontradas, e o ganho do "mesmo lado" (2 pontos) está dentro do ruído, já que endereços da mesma rua não são independentes.

## Premissas

- O código de município da consulta está correto e delimita a busca. A comparação usa os 6 primeiros dígitos do `COD_MUNICIPIO` do CNEFE, que tem 7.
- O setor devolvido é o `COD_SETOR` do CNEFE tal como está (15 dígitos + a letra `P`, presente em todos os registros dos municípios da busca; o significado da letra não foi verificado). A coluna `setor_censitario_15dig` traz a versão sem a letra, porque o exemplo do enunciado mostra 15 dígitos.
- Um setor cobre uma faixa contínua de numeração, e números de mesma paridade ficam do mesmo lado da rua. Por isso o número mais próximo indica o setor.
- Nos `AMBIGUO`, o setor é preenchido com o melhor palpite (constante `PREENCHER_AMBIGUOS` em `src/matching.py`). Com `False`, a coluna sai vazia e só a lista de candidatos é gravada.
- Os limites do projeto ficam no topo de `src/matching.py`: nota e margem da correção de grafia (`NOTA_MINIMA`, `MARGEM_MINIMA`) e peso do fallback (`PESO_MINIMO_FALLBACK`).

## Limitações

- **26 endereços (24,3%) ficam sem setor.** Causas: CEP rural genérico, rua ausente do CNEFE com aquele nome (`RUA JULIO VERNE`), código no lugar do nome (`RUA QD S15 RUA 07 N09`) e numeral por extenso (`RUA 21 DE JANEIRO`, que no CNEFE é `RUA VINTE E UM DE JANEIRO`). Um conversor de numerais resolveria o último caso.
- **Os limites foram calibrados na própria base de busca**, olhando seus 107 endereços e sem um conjunto separado de validação. Podem não se transferir bem para outros dados.
- **Nomes curtos são difíceis para a correção de grafia:** uma letra trocada em `TAGUA` (`TABUA`) dá nota 80, abaixo do limite.
- **O tipo do logradouro é a primeira palavra**, se estiver na lista de tipos conhecidos. Tipos de várias palavras (`2A TRAVESSA DA RUA`) não são reconhecidos.
- **A interpolação por número é simples:** não considera a geometria da rua, e empates (setores à mesma distância ou com a mesma frequência) são decididos pela ordem dos dados.
- **O peso do fallback assume** que o endereço procurado se distribui como os do CNEFE, o que pode ser otimista para endereços rurais.

## Estrutura do repositório

```
executar.py               comando único: roda o pipeline completo
data/
  base_busca.csv          base de busca (entrada)
  cnefe_bahia.csv         CNEFE (entrada, não versionado)
src/                      pipeline
  filtrar_cnefe.py          etapa 1: filtra o CNEFE pelos municípios da busca
  preparar_cnefe.py         etapa 2: normaliza os logradouros do CNEFE
  main.py                   etapa 3: vincula e grava os resultados
  normalize.py              normalização, chave solta e tipo de logradouro
  dados.py                  carga e preparação das bases
  matching.py               localização da rua, desempate, correção de grafia e fallback
  relatorio.py              saída em Excel e tabelas-resumo
  analises/                 investigações que fundamentam as decisões
output/                   resultados
```

Os scripts de `src/analises/` não fazem parte da execução. Rodam a partir da raiz, por exemplo `python src/analises/avaliar_metodos.py`.

| Script | O que mostrou |
|---|---|
| `explorar_cnefe.py` | Estrutura do CNEFE: município de 7 dígitos, setor de 16 caracteres, linhas sem número |
| `explorar_matching.py` | O CEP isolado discrimina pouco |
| `explorar_exato.py` | O nome exato resolve 43 de 107 endereços |
| `diagnosticar_falhas.py`, `diagnosticar_fuzzy.py` | Natureza das falhas e calibração da correção de grafia |
| `explorar_chave_solta.py`, `auditar_solta.py` | Ganho e riscos da chave solta |
| `explorar_desempate.py`, `avaliar_metodos.py` | Validação interna dos métodos de desempate |
| `diagnosticar_fallback.py` | Peso do setor dominante por CEP e localidade nos 33 sem rua |
| `testar_normalize.py` | Conferência da normalização na base de busca |

## Dependências

`pandas`, `pyarrow` (leitura e escrita de Parquet), `unidecode` (remoção de acentos), `rapidfuzz` (similaridade de texto) e `openpyxl` (saída em Excel). As versões usadas estão em `requirements.txt`.