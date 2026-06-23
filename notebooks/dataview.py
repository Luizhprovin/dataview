# %% [markdown]
# # DataView - Exploracao e Analise de Dados de Vendas
#
# Mini-projeto avaliativo do Modulo 1. O objetivo e criar um fluxo completo de
# analise de vendas: gerar dados brutos, inspecionar, limpar, tratar outliers,
# criar metricas, segmentar clientes, visualizar resultados e exportar arquivos
# finais.
#
# Diferencial aplicado: alem das RFs do enunciado, o notebook usa logging simples
# para monitorar as etapas do pipeline e facilitar a explicacao no video.

# %%
# RF00 - Importacoes, caminhos e logging
import json
import logging
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ajuste de caminhos para funcionar no VS Code tanto a partir da pasta dataview
# quanto a partir da pasta notebooks.
PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_V1 = PROJECT_ROOT / "data" / "processed" / "v1_com_outliers"
DATA_PROCESSED_V2 = PROJECT_ROOT / "data" / "processed" / "v2_outliers_tratado"
DATA_FINAL = PROJECT_ROOT / "data" / "final"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
GRAFICOS_DIR = OUTPUTS_DIR / "graficos"


def garantir_estrutura():
    """Cria as pastas esperadas do projeto, caso ainda nao existam."""
    for pasta in [
        DATA_RAW,
        DATA_PROCESSED_V1,
        DATA_PROCESSED_V2,
        DATA_FINAL,
        OUTPUTS_DIR,
        GRAFICOS_DIR,
    ]:
        pasta.mkdir(parents=True, exist_ok=True)


def configurar_logging():
    """Configura logs no console e em outputs/pipeline.log."""
    garantir_estrutura()
    logger = logging.getLogger("dataview")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter("%(levelname)s | %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formato)

    arquivo = logging.FileHandler(
        OUTPUTS_DIR / "pipeline.log", mode="w", encoding="utf-8"
    )
    arquivo.setFormatter(formato)

    logger.addHandler(console)
    logger.addHandler(arquivo)
    return logger


def caminho_relativo(caminho):
    """Retorna caminho relativo ao projeto para logs e mensagens."""
    caminho = Path(caminho)
    try:
        return str(caminho.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(caminho)


logger = configurar_logging()
logger.info("Estrutura do projeto configurada")


def salvar_csv_seguro(df, caminho_csv, **kwargs):
    """Salva um DataFrame em CSV com logging e tratamento de erro."""
    try:
        caminho_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(caminho_csv, **kwargs)
        logger.info("CSV salvo com sucesso: %s", caminho_relativo(caminho_csv))
    except PermissionError:
        logger.error(
            "Sem permissao para gravar o CSV: %s", caminho_relativo(caminho_csv)
        )
        raise
    except OSError as erro:
        logger.error(
            "Erro ao gravar o CSV %s: %s", caminho_relativo(caminho_csv), erro
        )
        raise


def salvar_json_seguro(dados, caminho_json):
    """Salva um dicionario em JSON com logging e tratamento de erro."""
    try:
        caminho_json.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_json, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)
        logger.info("JSON salvo com sucesso: %s", caminho_relativo(caminho_json))
    except PermissionError:
        logger.error(
            "Sem permissao para gravar o JSON: %s", caminho_relativo(caminho_json)
        )
        raise
    except OSError as erro:
        logger.error(
            "Erro ao gravar o JSON %s: %s", caminho_relativo(caminho_json), erro
        )
        raise


def ler_json_seguro(caminho_json):
    """Le um arquivo JSON com logging e tratamento de erro."""
    try:
        with open(caminho_json, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        logger.info("JSON lido com sucesso: %s", caminho_relativo(caminho_json))
        return dados
    except FileNotFoundError:
        logger.error("JSON nao encontrado: %s", caminho_relativo(caminho_json))
        raise
    except json.JSONDecodeError as erro:
        logger.error("JSON invalido em %s: %s", caminho_relativo(caminho_json), erro)
        raise


def salvar_figura_segura(fig, caminho_png, dpi=140):
    """Salva uma figura PNG com logging e tratamento de erro."""
    try:
        caminho_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(caminho_png, dpi=dpi)
        logger.info("Grafico salvo com sucesso: %s", caminho_relativo(caminho_png))
    except PermissionError:
        logger.error(
            "Sem permissao para gravar o grafico: %s", caminho_relativo(caminho_png)
        )
        raise
    except OSError as erro:
        logger.error(
            "Erro ao gravar o grafico %s: %s", caminho_relativo(caminho_png), erro
        )
        raise

# %% [markdown]
# ## RF01 - Criar ou carregar o dataset de vendas
#
# Usaremos um dataset sintetico, como recomendado no PDF, para garantir
# reprodutibilidade. A base inclui problemas intencionais: valores nulos, datas
# invalidas, espacos extras em strings e alguns outliers.

# %%
# RF01 - Geracao e carregamento do dataset sintetico bruto
def gerar_dataset_vendas(n_registros=220, seed=42):
    """Gera um dataset sintetico de vendas com sujeiras controladas."""
    random.seed(seed)
    np.random.seed(seed)

    produtos = ["Notebook", "Smartphone", "Tablet", "Monitor", "Teclado", "Mouse"]
    precos = {
        "Notebook": 3500,
        "Smartphone": 2200,
        "Tablet": 1800,
        "Monitor": 1200,
        "Teclado": 250,
        "Mouse": 120,
    }
    categorias = {
        "Notebook": "Computadores",
        "Smartphone": "Celulares",
        "Tablet": "Celulares",
        "Monitor": "Computadores",
        "Teclado": "Perifericos",
        "Mouse": "Perifericos",
    }
    regioes = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
    clientes = ["Cliente_{:03d}".format(i) for i in range(1, 36)]
    data_inicio = datetime(2024, 1, 1)
    dados = []

    indices_outlier_quantidade = {18, 74, 121, 188}
    indices_outlier_preco = {44, 153}

    for i in range(n_registros):
        produto_base = random.choice(produtos)
        produto = produto_base
        cliente = random.choice(clientes)
        quantidade = random.randint(1, 10)
        preco = float(precos[produto_base])
        data = data_inicio + timedelta(days=random.randint(0, 364))

        # Pequena variacao para o dado parecer menos artificial.
        preco = round(preco * random.uniform(0.92, 1.08), 2)

        # Outliers intencionais para a RF04.
        if i in indices_outlier_quantidade:
            quantidade = random.choice([42, 55, 70])
        if i in indices_outlier_preco:
            preco = round(preco * random.choice([5, 8]), 2)

        # Sujeiras intencionais.
        if random.random() < 0.06:
            quantidade = None
        if random.random() < 0.05:
            preco = None
        if random.random() < 0.05:
            produto = "  " + produto + "  "
        if random.random() < 0.04:
            cliente = "  " + cliente + "  "

        data_str = data.strftime("%Y-%m-%d")
        if random.random() < 0.035:
            data_str = random.choice(["DATA INVALIDA", "31/02/2024", "sem data"])

        dados.append(
            {
                "id_venda": i + 1,
                "data_venda": data_str,
                "cliente": cliente,
                "produto": produto,
                "categoria": categorias.get(produto_base, "Outros"),
                "regiao": random.choice(regioes),
                "quantidade": quantidade,
                "preco_unitario": preco,
            }
        )

    return pd.DataFrame(dados)


def carregar_dataset(caminho_csv):
    """Le um arquivo CSV de vendas e retorna um DataFrame."""
    try:
        df = pd.read_csv(caminho_csv)
        logger.info("CSV carregado com sucesso: %s linhas", len(df))
        return df
    except FileNotFoundError:
        logger.error("Arquivo nao encontrado: %s", caminho_relativo(caminho_csv))
        raise


df_gerado = gerar_dataset_vendas()
caminho_bruto = DATA_RAW / "vendas.csv"
salvar_csv_seguro(df_gerado, caminho_bruto, index=False, encoding="utf-8-sig")
df_bruto = carregar_dataset(caminho_bruto)
logger.info(
    "RF01 concluida: dataset bruto salvo e recarregado de %s com %s linhas",
    caminho_relativo(caminho_bruto),
    len(df_bruto),
)
print(df_bruto.head())

# %% [markdown]
# ## RF02 - Inspecionar e descrever os dados
#
# Esta etapa mostra tamanho, colunas, tipos, valores nulos, primeiras linhas e
# estatisticas descritivas.

# %%
# RF02 - Inspecao inicial
def inspecionar_dados(df):
    """Exibe informacoes basicas do DataFrame e retorna estatisticas descritivas."""
    print("=== INSPECAO INICIAL DO DATASET ===")
    print("Shape:", df.shape)
    print("\nColunas:", list(df.columns))
    print("\nTipos de dados:\n", df.dtypes)
    print("\nValores nulos por coluna:\n", df.isnull().sum())
    print("\nPrimeiros registros:")
    print(df.head())

    estatisticas = df.describe(include="all")
    logger.info("RF02 concluida: inspecao inicial executada")
    return estatisticas


estatisticas_iniciais = inspecionar_dados(df_bruto)
print(estatisticas_iniciais)

# %% [markdown]
# ## RF03 - Limpar e tratar os dados
#
# A limpeza trata espacos extras com regex, converte datas, remove datas invalidas
# e remove linhas sem quantidade ou preco unitario.

# %%
# RF03 - Limpeza de strings, datas e nulos
def limpar_strings_regex(df, colunas):
    """Normaliza colunas textuais usando regex e strip."""
    df = df.copy()
    for col in colunas:
        df[col] = df[col].apply(
            lambda s: re.sub(r"\s+", " ", str(s)).strip() if pd.notna(s) else s
        )
    return df


def limpar_dados(df):
    """Limpa o DataFrame e retorna a versao v1 com outliers mantidos."""
    df = df.copy()
    relatorio = {"registros_iniciais": int(len(df))}

    colunas_texto = [
        col
        for col in df.columns
        if pd.api.types.is_object_dtype(df[col])
        or pd.api.types.is_string_dtype(df[col])
    ]
    df = limpar_strings_regex(df, colunas_texto)

    df["data_venda"] = pd.to_datetime(df["data_venda"], errors="coerce")
    relatorio["datas_invalidas_removidas"] = int(df["data_venda"].isna().sum())
    df = df.dropna(subset=["data_venda"])

    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")

    n_antes = len(df)
    df = df.dropna(subset=["quantidade", "preco_unitario"])
    relatorio["linhas_nulas_removidas"] = int(n_antes - len(df))

    df["quantidade"] = df["quantidade"].astype(int)
    df["preco_unitario"] = df["preco_unitario"].astype(float)

    relatorio["registros_finais"] = int(len(df))
    relatorio["registros_removidos_total"] = int(
        relatorio["registros_iniciais"] - len(df)
    )

    print("=== RELATORIO DE LIMPEZA ===")
    for etapa, valor in relatorio.items():
        print("{}: {}".format(etapa, valor))

    logger.info(
        "RF03 concluida: %s registros removidos na limpeza geral",
        relatorio["registros_removidos_total"],
    )
    return df, relatorio


df_v1, relatorio_limpeza = limpar_dados(df_bruto)
caminho_v1 = DATA_PROCESSED_V1 / "vendas_v1.csv"
salvar_csv_seguro(df_v1, caminho_v1, index=False, encoding="utf-8-sig")
logger.info("Versao v1 salva em %s", caminho_relativo(caminho_v1))
print(df_v1.head())

# %% [markdown]
# ## RF04 - Detectar e tratar outliers
#
# A versao v1 mantem os outliers. A versao v2 usa IQR para remover valores
# extremos em quantidade e receita total temporaria.

# %%
# RF04 - Outliers via IQR
def tratar_outliers(df, colunas, fator=1.5, metodo="remover"):
    """Detecta e trata outliers numericos usando o intervalo interquartil."""
    df = df.copy()
    relatorio = {}

    for col in colunas:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lim_inf = q1 - fator * iqr
        lim_sup = q3 + fator * iqr
        mascara_outlier = (df[col] < lim_inf) | (df[col] > lim_sup)
        n_outliers = int(mascara_outlier.sum())

        relatorio[col] = {
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "limite_inferior": float(lim_inf),
            "limite_superior": float(lim_sup),
            "outliers_detectados": n_outliers,
        }

        print(
            "{}: {} outliers detectados (lim_inf={:.2f}, lim_sup={:.2f})".format(
                col, n_outliers, lim_inf, lim_sup
            )
        )

        if metodo == "remover":
            df = df[~mascara_outlier]
        elif metodo == "limitar":
            df[col] = df[col].clip(lower=lim_inf, upper=lim_sup)
        else:
            raise ValueError("metodo deve ser 'remover' ou 'limitar'")

    return df, relatorio


df_v1_tmp = df_v1.copy()
df_v1_tmp["receita_total"] = df_v1_tmp["quantidade"] * df_v1_tmp["preco_unitario"]

df_v2, relatorio_outliers = tratar_outliers(
    df_v1_tmp,
    colunas=["quantidade", "receita_total"],
    metodo="remover",
)
df_v2 = df_v2.drop(columns=["receita_total"])

caminho_v2 = DATA_PROCESSED_V2 / "vendas_v2.csv"
salvar_csv_seguro(df_v2, caminho_v2, index=False, encoding="utf-8-sig")

print("\nv1 = {} linhas".format(len(df_v1)))
print("v2 = {} linhas".format(len(df_v2)))
print("Outliers removidos = {} linhas".format(len(df_v1) - len(df_v2)))
logger.info(
    "RF04 concluida: v2 salva em %s com %s linhas",
    caminho_relativo(caminho_v2),
    len(df_v2),
)
print(df_v2.head())

# %% [markdown]
# ## RF05 - Criar colunas derivadas
#
# Criamos receita total, mes, trimestre, ano e uma faixa de valor por item usando
# np.select.

# %%
# RF05 - Colunas derivadas
def criar_colunas_derivadas(df):
    """Cria colunas calculadas para analise."""
    df = df.copy()
    df["receita_total"] = df["quantidade"] * df["preco_unitario"]
    df["mes"] = df["data_venda"].dt.month
    df["trimestre"] = df["data_venda"].dt.quarter.apply(lambda q: "Q{}".format(q))
    df["ano"] = df["data_venda"].dt.year
    df["ano_mes"] = df["data_venda"].dt.to_period("M").astype(str)

    condicoes = [
        df["receita_total"] < 500,
        (df["receita_total"] >= 500) & (df["receita_total"] < 5000),
        df["receita_total"] >= 5000,
    ]
    rotulos = ["Baixo Valor", "Medio Valor", "Alto Valor"]
    df["faixa_receita_item"] = np.select(condicoes, rotulos, default="N/D")

    logger.info("RF05 concluida: colunas derivadas criadas")
    return df


df = criar_colunas_derivadas(df_v2)
print(
    df[
        [
            "data_venda",
            "produto",
            "receita_total",
            "mes",
            "trimestre",
            "ano",
            "faixa_receita_item",
        ]
    ].head()
)

# %% [markdown]
# ## RF06 - Calcular metricas agregadas com groupby
#
# As metricas respondem as perguntas do negocio: vendas no tempo, produtos mais
# fortes, categorias e regioes.

# %%
# RF06 - Metricas agregadas
def calcular_metricas(df):
    """Calcula metricas por mes, produto, categoria, regiao e trimestre."""
    metricas = {}

    metricas["por_mes"] = (
        df.groupby("mes")
        .agg(
            receita_total=("receita_total", "sum"),
            quantidade=("quantidade", "sum"),
            n_vendas=("id_venda", "count"),
        )
        .reset_index()
        .sort_values("mes")
    )

    metricas["por_trimestre"] = (
        df.groupby("trimestre")
        .agg(receita_total=("receita_total", "sum"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("trimestre")
    )

    metricas["top_produtos"] = (
        df.groupby("produto")["receita_total"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    metricas["por_categoria"] = (
        df.groupby("categoria")["receita_total"]
        .sum()
        .reset_index()
        .sort_values("receita_total", ascending=False)
    )

    metricas["por_regiao"] = (
        df.groupby("regiao")
        .agg(
            receita_total=("receita_total", "sum"),
            quantidade=("quantidade", "sum"),
            media_ticket=("receita_total", "mean"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
    )

    for nome, tabela in metricas.items():
        print("\n=== {} ===".format(nome.upper().replace("_", " ")))
        print(tabela.to_string(index=False))

    logger.info("RF06 concluida: metricas agregadas calculadas")
    return metricas


metricas = calcular_metricas(df)

# %% [markdown]
# ## RF07 - Segmentar clientes por nivel de gasto
#
# Classificamos clientes em Bronze, Prata e Ouro usando lambda com condicional.

# %%
# RF07 - Segmentacao de clientes
def segmentar_clientes(df):
    """Agrupa gasto por cliente e classifica em segmentos."""
    clientes_df = (
        df.groupby("cliente")["receita_total"]
        .sum()
        .reset_index()
        .rename(columns={"receita_total": "total_gasto"})
    )

    clientes_df["segmento"] = clientes_df["total_gasto"].apply(
        lambda g: "Ouro" if g > 15000 else ("Prata" if g >= 5000 else "Bronze")
    )

    clientes_df = clientes_df.sort_values("total_gasto", ascending=False)

    print("=== SEGMENTACAO DE CLIENTES (Top 10) ===")
    print(clientes_df.head(10).to_string(index=False))
    print("\nDistribuicao de segmentos:")
    print(clientes_df["segmento"].value_counts().to_string())

    logger.info("RF07 concluida: %s clientes segmentados", len(clientes_df))
    return clientes_df


clientes = segmentar_clientes(df)
print(clientes.head())

# %% [markdown]
# ## RF08 - Calcular estatisticas com NumPy
#
# Esta etapa usa array NumPy, funcoes estatisticas, vetorizacao, broadcasting e
# boolean indexing.

# %%
# RF08 - Estatisticas com NumPy
def calcular_estatisticas_numpy(df):
    """Calcula estatisticas de receita usando NumPy diretamente."""
    receitas = df["receita_total"].to_numpy()

    stats = {
        "media": float(np.mean(receitas)),
        "mediana": float(np.median(receitas)),
        "desvio_padrao": float(np.std(receitas)),
        "total": float(np.sum(receitas)),
        "p25": float(np.percentile(receitas, 25)),
        "p75": float(np.percentile(receitas, 75)),
    }

    receitas_pct = (receitas / receitas.sum()) * 100
    stats["acima_da_media"] = int((receitas > stats["media"]).sum())
    stats["participacao_top5_pct"] = float(np.sort(receitas_pct)[-5:].sum())

    print("=== ESTATISTICAS COM NUMPY ===")
    for chave, valor in stats.items():
        if chave == "acima_da_media":
            print("{}: {} vendas".format(chave, valor))
        else:
            print("{}: {:.2f}".format(chave, valor))

    logger.info("RF08 concluida: estatisticas NumPy calculadas")
    return stats


stats = calcular_estatisticas_numpy(df)

# %% [markdown]
# ## RF09 - Criar visualizacoes com Matplotlib e Seaborn
#
# Geramos cinco graficos PNG: receita por mes, top produtos, distribuicao por
# regiao, clientes por segmento e um pairplot de relacoes numericas.

# %%
# RF09 - Visualizacoes
def gerar_visualizacoes(df, metricas, clientes, output_dir=GRAFICOS_DIR):
    """Gera e salva graficos do projeto."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="muted")

    meses_abrev = [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    pm = metricas["por_mes"]
    ax.plot(pm["mes"], pm["receita_total"], marker="o", linewidth=2)
    ax.set_title("Receita Total por Mes")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Receita (R$)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(meses_abrev, rotation=45)
    fig.tight_layout()
    salvar_figura_segura(fig, output_dir / "receita_por_mes.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=metricas["top_produtos"],
        y="produto",
        x="receita_total",
        hue="produto",
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 5 Produtos por Receita Total")
    ax.set_xlabel("Receita Total (R$)")
    ax.set_ylabel("Produto")
    fig.tight_layout()
    salvar_figura_segura(fig, output_dir / "top_produtos.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="regiao", y="receita_total", ax=ax)
    ax.set_title("Distribuicao de Receita por Regiao")
    ax.set_xlabel("Regiao")
    ax.set_ylabel("Receita por Venda (R$)")
    plt.xticks(rotation=30)
    fig.tight_layout()
    salvar_figura_segura(fig, output_dir / "distribuicao_receita_regiao.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ordem = ["Bronze", "Prata", "Ouro"]
    contagem = clientes["segmento"].value_counts().reindex(ordem, fill_value=0)
    contagem = contagem.reset_index()
    contagem.columns = ["segmento", "quantidade_clientes"]
    sns.barplot(
        data=contagem,
        x="segmento",
        y="quantidade_clientes",
        hue="segmento",
        legend=False,
        ax=ax,
    )
    ax.set_title("Clientes por Segmento")
    ax.set_xlabel("Segmento")
    ax.set_ylabel("Numero de Clientes")
    fig.tight_layout()
    salvar_figura_segura(fig, output_dir / "clientes_por_segmento.png", dpi=140)
    plt.close(fig)

    pairplot_df = df[
        ["quantidade", "preco_unitario", "receita_total", "categoria"]
    ].copy()
    categorias = sorted(pairplot_df["categoria"].dropna().unique())
    cores_pairplot = {
        categoria: cor
        for categoria, cor in zip(
            categorias,
            ["#A3BEFA", "#F0986E", "#A3D576", "#FFE15B", "#F390CA"],
        )
    }

    grade = sns.pairplot(
        data=pairplot_df,
        vars=["quantidade", "preco_unitario", "receita_total"],
        hue="categoria",
        palette=cores_pairplot,
        diag_kind="hist",
        plot_kws={"alpha": 0.78, "s": 34, "edgecolor": "white", "linewidth": 0.35},
        diag_kws={"alpha": 0.72},
    )
    grade.fig.set_size_inches(9, 9)
    grade.fig.subplots_adjust(top=0.9)
    grade.fig.suptitle("Relacao entre Quantidade, Preco e Receita", fontsize=15)
    grade.fig.text(
        0.5,
        0.94,
        "Cada ponto representa uma venda final; as cores indicam a categoria do produto.",
        ha="center",
        fontsize=10,
    )
    salvar_figura_segura(
        grade.fig, output_dir / "pairplot_relacoes_numericas.png", dpi=140
    )
    plt.close(grade.fig)

    logger.info("RF09 concluida: graficos salvos em %s", caminho_relativo(output_dir))


gerar_visualizacoes(df, metricas, clientes)

# %% [markdown]
# ## RF10 - Funcoes reutilizaveis e funcao de ordem superior
#
# O fluxo ja esta organizado em funcoes. Para demonstrar funcao que recebe outra
# funcao como argumento, usamos aplicar_transformacao.

# %%
# RF10 - Funcao de ordem superior
def aplicar_transformacao(df, coluna, funcao):
    """Aplica uma funcao recebida por parametro em uma coluna do DataFrame."""
    df = df.copy()
    df["{}_transformado".format(coluna)] = df[coluna].apply(funcao)
    return df


df_demo = aplicar_transformacao(
    df,
    "receita_total",
    lambda x: "Ticket Alto" if x > 5000 else "Ticket Normal",
)

print(df_demo[["receita_total", "receita_total_transformado"]].head())

df_demo_milhares = aplicar_transformacao(
    df,
    "receita_total",
    lambda x: round(x / 1000, 2),
)

print(df_demo_milhares[["receita_total", "receita_total_transformado"]].head())

# %% [markdown]
# ## RF11 - Ler e escrever arquivos CSV e JSON
#
# Exportamos metricas mensais, segmentacao de clientes e estatisticas gerais.
# Depois lemos o JSON de volta para confirmar a gravacao.

# %%
# RF11 - Exportacao de resultados
def exportar_resultados(metricas, clientes, stats):
    """Exporta resultados em CSV e JSON, depois valida a leitura do JSON."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    caminho_metricas = OUTPUTS_DIR / "metricas_por_mes.csv"
    caminho_clientes = OUTPUTS_DIR / "segmentacao_clientes.csv"
    caminho_json = OUTPUTS_DIR / "estatisticas_gerais.json"

    salvar_csv_seguro(
        metricas["por_mes"], caminho_metricas, index=False, encoding="utf-8-sig"
    )
    salvar_csv_seguro(clientes, caminho_clientes, index=False, encoding="utf-8-sig")

    stats_serializaveis = {}
    for chave, valor in stats.items():
        if isinstance(valor, (int, np.integer)):
            stats_serializaveis[chave] = int(valor)
        else:
            stats_serializaveis[chave] = round(float(valor), 2)
    salvar_json_seguro(stats_serializaveis, caminho_json)
    stats_lidas = ler_json_seguro(caminho_json)

    print("CSV exportado:", caminho_relativo(caminho_metricas))
    print("CSV exportado:", caminho_relativo(caminho_clientes))
    print("JSON exportado e lido de volta:")
    print(json.dumps(stats_lidas, indent=2, ensure_ascii=False))

    logger.info("RF11 concluida: CSVs e JSON exportados")
    return stats_lidas


stats_lidas = exportar_resultados(metricas, clientes, stats)

# %% [markdown]
# ## RF12 - Consolidar a analise e salvar o dataset final
#
# A versao final escolhida e a v2, com limpeza geral e tratamento de outliers. A
# v1 permanece salva para comparacao.

# %%
# RF12 - Consolidacao final
def salvar_dataset_final(df):
    """Salva o dataset final enriquecido e verifica arquivos esperados."""
    caminho_final = DATA_FINAL / "vendas_final.csv"
    salvar_csv_seguro(df, caminho_final, index=False, encoding="utf-8-sig")
    logger.info("Dataset final salvo em %s", caminho_relativo(caminho_final))
    return caminho_final


def validar_entrega():
    """Confere se os principais arquivos da entrega foram gerados."""
    esperados = [
        DATA_RAW / "vendas.csv",
        DATA_PROCESSED_V1 / "vendas_v1.csv",
        DATA_PROCESSED_V2 / "vendas_v2.csv",
        DATA_FINAL / "vendas_final.csv",
        OUTPUTS_DIR / "metricas_por_mes.csv",
        OUTPUTS_DIR / "segmentacao_clientes.csv",
        OUTPUTS_DIR / "estatisticas_gerais.json",
        GRAFICOS_DIR / "receita_por_mes.png",
        GRAFICOS_DIR / "top_produtos.png",
        GRAFICOS_DIR / "distribuicao_receita_regiao.png",
        GRAFICOS_DIR / "clientes_por_segmento.png",
        GRAFICOS_DIR / "pairplot_relacoes_numericas.png",
        OUTPUTS_DIR / "pipeline.log",
    ]

    status = pd.DataFrame(
        {
            "arquivo": [str(caminho.relative_to(PROJECT_ROOT)) for caminho in esperados],
            "existe": [caminho.exists() for caminho in esperados],
        }
    )
    print(status)

    if status["existe"].all():
        logger.info("Validacao final concluida: todos os arquivos esperados existem")
    else:
        logger.warning("Validacao final encontrou arquivos ausentes")

    return status


caminho_final = salvar_dataset_final(df)
status_entrega = validar_entrega()
print("Dataset final salvo em:", caminho_relativo(caminho_final))
print("Shape final:", df.shape)
