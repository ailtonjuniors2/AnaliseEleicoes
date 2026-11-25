# ============================================================
# 1. IMPORTAÇÕES
# ============================================================

import pandas as pd
import numpy as np

from pathlib import Path


# ============================================================
# 2. CONFIGURAÇÕES
# ============================================================

# Diretório onde está este arquivo.

PASTA_PROJETO = Path(__file__).resolve().parent

# Diretório onde estão os arquivos CSV.

PASTA_DADOS = PASTA_PROJETO / "dados"

# Arquivos utilizados na comparação.

ARQUIVOS = {
    2006: PASTA_DADOS / "detalhe_votacao_munzona_2006_BRASIL.csv",
    2022: PASTA_DADOS / "detalhe_votacao_munzona_2022_BRASIL.csv",
    2026: PASTA_DADOS / "detalhe_votacao_munzona_2026_BRASIL.csv"
}

# Configurações padrão.

TURNO_COMPARACAO = 1
EXCLUIR_EXTERIOR = False
MIN_APTOS = 5000


# ============================================================
# 3. CARREGAMENTO E LIMPEZA DOS DADOS
# ============================================================

def carregar_presidente(ano, caminho):
    """
    Carrega os dados eleitorais de determinado ano.

    Mantém somente registros referentes ao cargo de presidente,
    converte as colunas numéricas e remove registros inválidos.

    Retorna um DataFrame padronizado.
    """

    caminho = Path(caminho)

    # Verifica se o arquivo existe.

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo de {ano} não encontrado: {caminho}"
        )

    # Lê o CSV.
    # Os códigos de identificação são mantidos como texto.

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        low_memory=False,
        dtype={
            "CD_MUNICIPIO": "string",
            "SG_UF": "string"
        }
    )

    # Remove espaços dos nomes das colunas.

    df.columns = df.columns.str.strip()

    # Verifica as colunas necessárias.

    colunas_obrigatorias = [
        "DS_CARGO",
        "QT_APTOS",
        "QT_ABSTENCOES",
        "NR_TURNO",
        "NM_MUNICIPIO",
        "SG_UF",
        "CD_MUNICIPIO"
    ]

    faltantes = [
        coluna for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Colunas ausentes no arquivo de {ano}: {faltantes}"
        )

    # Limpa espaços das colunas textuais.

    for coluna in df.select_dtypes(include="object").columns:
        df[coluna] = df[coluna].str.strip()

    # Remove espaços das colunas do tipo string.

    for coluna in ["CD_MUNICIPIO", "SG_UF"]:
        df[coluna] = df[coluna].str.strip()

    # Remove registros duplicados.

    df = df.drop_duplicates()

    # Mantém somente os registros de presidente.

    df = df[
        df["DS_CARGO"].astype("string").str.strip().str.casefold()
        == "presidente"
    ].copy()

    # Converte as colunas numéricas.

    for coluna in ["QT_APTOS", "QT_ABSTENCOES", "NR_TURNO"]:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    # Remove registros sem informações necessárias.

    df = df.dropna(
        subset=[
            "QT_APTOS",
            "QT_ABSTENCOES",
            "NR_TURNO",
            "NM_MUNICIPIO",
            "SG_UF",
            "CD_MUNICIPIO"
        ]
    )

    # Remove valores inválidos.

    df = df[
        (df["QT_APTOS"] > 0)
        & (df["QT_ABSTENCOES"] >= 0)
    ].copy()

    # Identifica o ano eleitoral.

    df["ANO"] = ano

    # Seleciona as colunas utilizadas na análise.

    colunas_finais = [
        "ANO",
        "NR_TURNO",
        "SG_UF",
        "CD_MUNICIPIO",
        "NM_MUNICIPIO",
        "QT_APTOS",
        "QT_ABSTENCOES"
    ]

    return df[colunas_finais].copy()


# ============================================================
# 4. FUNÇÃO AUXILIAR DE COMPARAÇÃO MUNICIPAL
# ============================================================

def comparar_municipios(mun, ano_anterior, ano_atual, min_aptos):
    """
    Compara a taxa de abstenção dos municípios entre dois anos.

    Utiliza:
        SG_UF + CD_MUNICIPIO como chave de identificação.

    Calcula:
        - Taxa no ano anterior;
        - Taxa no ano atual;
        - Variação em pontos percentuais;
        - Maiores aumentos;
        - Maiores quedas.

    Considera o mínimo de eleitores aptos no ano atual.
    """

    chave = ["SG_UF", "CD_MUNICIPIO"]

    # Seleciona os municípios do ano anterior.

    dados_ant = mun[
        mun["ANO"] == ano_anterior
    ][
        chave + [
            "NM_MUNICIPIO",
            "QT_APTOS",
            "TAXA"
        ]
    ].copy()

    # Seleciona os municípios do ano atual.

    dados_atual = mun[
        mun["ANO"] == ano_atual
    ][
        chave + [
            "NM_MUNICIPIO",
            "QT_APTOS",
            "TAXA"
        ]
    ].copy()

    # Junta os municípios presentes nos dois anos.

    comparacao = dados_ant.merge(
        dados_atual,
        on=chave,
        how="inner",
        suffixes=(
            f"_{ano_anterior}",
            f"_{ano_atual}"
        )
    )

    # Calcula a variação da taxa de abstenção.

    comparacao["VAR_pp"] = (
        comparacao[f"TAXA_{ano_atual}"]
        - comparacao[f"TAXA_{ano_anterior}"]
    )

    # Filtra municípios com quantidade mínima de eleitores.

    grandes = comparacao[
        comparacao[f"QT_APTOS_{ano_atual}"] >= min_aptos
    ].copy()

    # Ordena os maiores aumentos.

    aumentos = grandes.sort_values(
        "VAR_pp",
        ascending=False
    ).head(15).copy()

    # Ordena as maiores quedas.

    quedas = grandes.sort_values(
        "VAR_pp",
        ascending=True
    ).head(15).copy()

    return comparacao, grandes, aumentos, quedas


# ============================================================
# 5. FUNÇÃO PRINCIPAL DE ANÁLISE
# ============================================================

def executar_analises(
    arquivos=None,
    turno=TURNO_COMPARACAO,
    excluir_exterior=EXCLUIR_EXTERIOR,
    min_aptos=MIN_APTOS
):
    """
    Executa todas as análises presentes no notebook.

    Parâmetros:
        arquivos:
            Dicionário contendo os caminhos dos CSVs.

        turno:
            Turno eleitoral utilizado na análise.

        excluir_exterior:
            Se True, remove os registros com SG_UF == "ZZ".

        min_aptos:
            Quantidade mínima de eleitores aptos para as
            tabelas de maiores aumentos e quedas.

    Retorna:
        Dicionário com todos os DataFrames para o Streamlit.
    """

    # --------------------------------------------------------
    # 5.1 CARREGAMENTO DOS ARQUIVOS
    # --------------------------------------------------------

    if arquivos is None:
        arquivos = ARQUIVOS

    # Carrega os dados de cada ano.

    dfs = {
        ano: carregar_presidente(ano, caminho)
        for ano, caminho in arquivos.items()
    }

    # Junta os arquivos em uma única base.

    base = pd.concat(
        dfs.values(),
        ignore_index=True
    )

    # Identifica os anos disponíveis nos arquivos carregados.

    anos = sorted(base["ANO"].unique())

    if len(anos) < 2:
        raise ValueError(
            "São necessários pelo menos dois anos para comparação."
        )

    # --------------------------------------------------------
    # 5.2 RESUMO COMPARATIVO ENTRE ANOS E TURNOS
    # --------------------------------------------------------

    # Agrupa os dados por ano e turno.

    diag = base.groupby(
        ["ANO", "NR_TURNO"]
    ).agg(
        Zonas=("QT_APTOS", "size"),
        Aptos=("QT_APTOS", "sum"),
        Abstencoes=("QT_ABSTENCOES", "sum")
    )

    # Calcula a taxa percentual de abstenção.

    diag["Taxa (%)"] = (
        diag["Abstencoes"] / diag["Aptos"]
    ) * 100

    # --------------------------------------------------------
    # 5.3 FILTRAGEM DO TURNO
    # --------------------------------------------------------

    b = base[
        base["NR_TURNO"] == turno
    ].copy()

    # Remove o exterior se solicitado.

    if excluir_exterior:
        b = b[
            b["SG_UF"] != "ZZ"
        ].copy()

    if b.empty:
        raise ValueError(
            f"Não existem dados para o turno {turno} "
            "com os filtros selecionados."
        )

    # Atualiza os anos efetivamente presentes no turno.

    anos_turno = sorted(b["ANO"].unique())

    if len(anos_turno) < 2:
        raise ValueError(
            "O turno selecionado precisa ter dados "
            "de pelo menos dois anos."
        )

    # --------------------------------------------------------
    # 5.4 AGRUPAMENTO MUNICIPAL
    # --------------------------------------------------------

    # Chave municipal: ano + UF + código do município.

    mun = b.groupby(
        ["ANO", "SG_UF", "CD_MUNICIPIO"],
        as_index=False
    ).agg(
        NM_MUNICIPIO=("NM_MUNICIPIO", "first"),
        QT_APTOS=("QT_APTOS", "sum"),
        QT_ABSTENCOES=("QT_ABSTENCOES", "sum")
    )

    # Calcula a taxa municipal de abstenção.

    mun["TAXA"] = (
        mun["QT_ABSTENCOES"] / mun["QT_APTOS"]
    ) * 100

    # --------------------------------------------------------
    # 5.5 AGRUPAMENTO POR UNIDADE FEDERATIVA
    # --------------------------------------------------------

    uf = b.groupby(
        ["ANO", "SG_UF"],
        as_index=False
    ).agg(
        QT_APTOS=("QT_APTOS", "sum"),
        QT_ABSTENCOES=("QT_ABSTENCOES", "sum")
    )

    # Calcula a taxa de abstenção de cada UF.

    uf["TAXA"] = (
        uf["QT_ABSTENCOES"] / uf["QT_APTOS"]
    ) * 100

    # --------------------------------------------------------
    # 5.6 ANÁLISE NACIONAL
    # --------------------------------------------------------

    nacional = b.groupby("ANO").agg(
        Municipios=("CD_MUNICIPIO", "nunique"),
        Aptos=("QT_APTOS", "sum"),
        Abstencoes=("QT_ABSTENCOES", "sum")
    )

    # Calcula a taxa nacional.

    nacional["Taxa (%)"] = (
        nacional["Abstencoes"] / nacional["Aptos"]
    ) * 100

    # Calcula a variação em pontos percentuais.

    nacional["Variação de pontos percentuais"] = (
        nacional["Taxa (%)"].diff()
    )

    # --------------------------------------------------------
    # 5.7 COMPARATIVO ENTRE UNIDADES FEDERATIVAS
    # --------------------------------------------------------

    # Transforma os anos em colunas.

    taxa_uf = uf.pivot(
        index="SG_UF",
        columns="ANO",
        values="TAXA"
    )

    # Calcula as variações entre todos os anos consecutivos.

    for anterior, atual in zip(
        anos_turno[:-1],
        anos_turno[1:]
    ):

        coluna = (
            f"Variação de pontos percentuais "
            f"{anterior} - {atual} "
        )

        taxa_uf[coluna] = (
            taxa_uf[atual] - taxa_uf[anterior]
        )

    # Ordena pela taxa do ano mais recente.

    taxa_uf = taxa_uf.sort_values(
        anos_turno[-1],
        ascending=False
    )

    # Variação entre os dois últimos anos.

    coluna_variacao_recente = (
        f"Variação de pontos percentuais "
        f"{anos_turno[-2]} - {anos_turno[-1]} "
    )

    variacao_uf = taxa_uf[
        [coluna_variacao_recente]
    ].copy()

    variacao_uf = variacao_uf.sort_values(
        coluna_variacao_recente
    )

    # --------------------------------------------------------
    # 5.8 DISTRIBUIÇÃO DE MUNICÍPIOS POR FAIXA
    # --------------------------------------------------------

    limites = [
        -np.inf,
        100,
        999,
        5000,
        10000,
        np.inf
    ]

    faixas = [
        "Até 100",
        "101 a 999",
        "1.000 a 5.000",
        "5.001 a 10.000",
        "Acima de 10.000"
    ]

    # Classifica os municípios pela quantidade absoluta
    # de abstenções.

    mun["FAIXA"] = pd.cut(
        mun["QT_ABSTENCOES"],
        bins=limites,
        labels=faixas
    )

    # Conta os municípios em cada faixa por ano.

    cont = mun.groupby(
        ["FAIXA", "ANO"],
        observed=False
    ).size().unstack(
        "ANO",
        fill_value=0
    )

    # Calcula o percentual dentro de cada ano.

    pct = cont.div(
        cont.sum(axis=0).replace(0, np.nan),
        axis=1
    ) * 100

    # --------------------------------------------------------
    # 5.9 DISTRIBUIÇÃO DAS TAXAS MUNICIPAIS
    # --------------------------------------------------------

    # Os dados individuais serão utilizados pelo Streamlit
    # para construir o boxplot.

    distribuicao_municipal = mun[
        ["ANO", "SG_UF", "NM_MUNICIPIO", "TAXA"]
    ].copy()

    # Estatísticas descritivas.

    estatisticas = mun.groupby(
        "ANO"
    )["TAXA"].describe().round(2)

    # --------------------------------------------------------
    # 5.10 COMPARAÇÃO DE LONGO PRAZO
    # --------------------------------------------------------

    # O notebook original compara o primeiro e o último
    # ano disponível (2006 e 2026, quando os três estão presentes).

    ano_inicial = anos_turno[0]
    ano_final = anos_turno[-1]

    comp_longo, grandes_longo, aumentos_longo, quedas_longo = (
        comparar_municipios(
            mun,
            ano_inicial,
            ano_final,
            min_aptos
        )
    )

    # --------------------------------------------------------
    # 5.11 COMPARAÇÃO DO PERÍODO MAIS RECENTE
    # --------------------------------------------------------

    # Compara os dois últimos anos disponíveis
    # (2022 e 2026, quando os três estão presentes).

    ano_anterior = anos_turno[-2]
    ano_atual = anos_turno[-1]

    comp_recente, grandes_recente, aumentos_recente, quedas_recente = (
        comparar_municipios(
            mun,
            ano_anterior,
            ano_atual,
            min_aptos
        )
    )

    # --------------------------------------------------------
    # 5.12 RETORNO DOS RESULTADOS
    # --------------------------------------------------------

    # Todos os DataFrames são disponibilizados para o frontend.

    resultados = {

        # Base original após limpeza.
        "base": base,

        # Análises gerais.
        "resumo": diag.round(2),
        "nacional": nacional.round(2),

        # Análises geográficas.
        "municipios": mun,
        "estados": uf,
        "comparativo_ufs": taxa_uf.round(2),
        "variacao_ufs": variacao_uf.round(2),

        # Distribuição municipal.
        "faixas_quantidade": cont,
        "faixas_percentual": pct.round(2),
        "distribuicao_municipal": distribuicao_municipal,
        "estatisticas": estatisticas,

        # Comparação de longo prazo.
        "comparacao_longo_prazo": comp_longo.round(2),
        "maiores_aumentos_longo_prazo": aumentos_longo.round(2),
        "maiores_quedas_longo_prazo": quedas_longo.round(2),

        # Comparação recente.
        "comparacao_recente": comp_recente.round(2),
        "maiores_aumentos": aumentos_recente.round(2),
        "maiores_quedas": quedas_recente.round(2),

        # Informações auxiliares para o frontend.
        "anos_disponiveis": anos_turno,
        "ano_inicial": ano_inicial,
        "ano_final": ano_final,
        "ano_anterior": ano_anterior,
        "ano_atual": ano_atual
    }

    return resultados
