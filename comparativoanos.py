import pandas as pd
import numpy as np

from pathlib import Path


# ============================================================
# 2. CONFIGURAÇÕES
# ============================================================

# Localiza a pasta do projeto automaticamente.

PASTA_PROJETO = Path(__file__).parent

# Caminhos dos arquivos CSV.

ARQUIVOS = {
    2006: PASTA_PROJETO / "dados" / "detalhe_votacao_munzona_2006_BRASIL.csv",
    2022: PASTA_PROJETO / "dados" / "detalhe_votacao_munzona_2022_BRASIL.csv",
    2026: PASTA_PROJETO / "dados" / "detalhe_votacao_munzona_2026_BRASIL.csv"
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
    Carrega o CSV de um ano e realiza a limpeza dos dados.

    Mantém somente registros referentes ao cargo de presidente.

    Retorna um DataFrame com as colunas necessárias para análise.
    """

    # Verifica se o arquivo existe.

    if not Path(caminho).exists():
        raise FileNotFoundError(
            f"Arquivo de {ano} não encontrado: {caminho}"
        )

    # Lê o CSV.
    # O código do município é lido como texto para evitar
    # problemas de identificação durante as comparações.

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        low_memory=False,
        dtype={"CD_MUNICIPIO": "string"}
    )

    # Remove espaços extras dos nomes das colunas.

    df.columns = df.columns.str.strip()

    # Verifica se as colunas necessárias existem.

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

    # Limpa os espaços das colunas textuais.

    for coluna in df.select_dtypes(include="object").columns:
        df[coluna] = df[coluna].str.strip()

    # Remove registros duplicados.

    df = df.drop_duplicates()

    # Mantém somente os registros de presidente.

    df = df[
        df["DS_CARGO"].astype("string").str.casefold()
        == "presidente"
    ].copy()

    # Converte as colunas numéricas.

    for coluna in ["QT_APTOS", "QT_ABSTENCOES", "NR_TURNO"]:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    # Remove registros sem informações essenciais.

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

    # Identifica o ano dos dados.

    df["ANO"] = ano

    # Seleciona somente as colunas utilizadas no projeto.

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
# 4. FUNÇÃO PRINCIPAL DE ANÁLISE
# ============================================================

def executar_analises(
    arquivos=None,
    turno=TURNO_COMPARACAO,
    excluir_exterior=EXCLUIR_EXTERIOR,
    min_aptos=MIN_APTOS
):
    """
    Executa todas as análises eleitorais.

    Parâmetros:
        arquivos: dicionário com os caminhos dos CSVs.
        turno: turno eleitoral utilizado nas comparações.
        excluir_exterior: remove ou não os dados do exterior.
        min_aptos: mínimo de eleitores aptos para comparar
                   os municípios com maiores variações.

    Retorna:
        Dicionário contendo todos os DataFrames necessários
        para a criação das tabelas e gráficos do Streamlit.
    """

    # --------------------------------------------------------
    # 4.1 CARREGAMENTO DOS ARQUIVOS
    # --------------------------------------------------------

    if arquivos is None:
        arquivos = ARQUIVOS

    # Carrega cada ano individualmente.

    dfs = {
        ano: carregar_presidente(ano, caminho)
        for ano, caminho in arquivos.items()
    }

    # Junta todos os anos em uma única base.

    base = pd.concat(
        dfs.values(),
        ignore_index=True
    )

    # Identifica os anos realmente disponíveis.

    anos = sorted(base["ANO"].unique())

    if not anos:
        raise ValueError("Nenhum dado eleitoral foi encontrado.")

    # --------------------------------------------------------
    # 4.2 RESUMO COMPARATIVO ENTRE ANOS
    # --------------------------------------------------------

    # Agrupa por ano e turno.

    diag = base.groupby(
        ["ANO", "NR_TURNO"]
    ).agg(
        Zonas=("QT_APTOS", "size"),
        Aptos=("QT_APTOS", "sum"),
        Abstencoes=("QT_ABSTENCOES", "sum")
    ).reset_index()

    # Calcula a taxa de abstenção.

    diag["Taxa (%)"] = (
        diag["Abstencoes"] / diag["Aptos"]
    ) * 100

    # --------------------------------------------------------
    # 4.3 FILTRAGEM DO TURNO
    # --------------------------------------------------------

    b = base[
        base["NR_TURNO"] == turno
    ].copy()

    # Remove o exterior caso solicitado.

    if excluir_exterior:
        b = b[b["SG_UF"] != "ZZ"].copy()

    if b.empty:
        raise ValueError(
            f"Não existem dados disponíveis para o turno {turno}."
        )

    # --------------------------------------------------------
    # 4.4 ANÁLISE POR MUNICÍPIO
    # --------------------------------------------------------

    # A identificação utiliza UF e código do município.

    mun = b.groupby(
        ["ANO", "SG_UF", "CD_MUNICIPIO"],
        as_index=False
    ).agg(
        NM_MUNICIPIO=("NM_MUNICIPIO", "first"),
        QT_APTOS=("QT_APTOS", "sum"),
        QT_ABSTENCOES=("QT_ABSTENCOES", "sum")
    )

    # Taxa percentual de abstenção municipal.

    mun["TAXA"] = (
        mun["QT_ABSTENCOES"] / mun["QT_APTOS"]
    ) * 100

    # --------------------------------------------------------
    # 4.5 ANÁLISE POR UF
    # --------------------------------------------------------

    uf = b.groupby(
        ["ANO", "SG_UF"],
        as_index=False
    ).agg(
        QT_APTOS=("QT_APTOS", "sum"),
        QT_ABSTENCOES=("QT_ABSTENCOES", "sum")
    )

    # Calcula a taxa de cada estado.

    uf["TAXA"] = (
        uf["QT_ABSTENCOES"] / uf["QT_APTOS"]
    ) * 100

    # --------------------------------------------------------
    # 4.6 ANÁLISE NACIONAL
    # --------------------------------------------------------

    nacional = b.groupby("ANO").agg(
        Municipios=("CD_MUNICIPIO", "nunique"),
        Aptos=("QT_APTOS", "sum"),
        Abstencoes=("QT_ABSTENCOES", "sum")
    )

    # Taxa nacional de abstenção.

    nacional["Taxa (%)"] = (
        nacional["Abstencoes"] / nacional["Aptos"]
    ) * 100

    # Variação em pontos percentuais entre anos consecutivos.

    nacional["Variação de pontos percentuais"] = (
        nacional["Taxa (%)"].diff()
    )

    # --------------------------------------------------------
    # 4.7 COMPARATIVO ENTRE AS UFs
    # --------------------------------------------------------

    # Transforma os anos em colunas.

    taxa_uf = uf.pivot(
        index="SG_UF",
        columns="ANO",
        values="TAXA"
    )

    # Calcula a variação entre anos consecutivos.

    anos_uf = sorted(uf["ANO"].unique())

    for anterior, atual in zip(anos_uf[:-1], anos_uf[1:]):

        coluna = (
            f"Variação de pontos percentuais "
            f"{anterior} - {atual}"
        )

        taxa_uf[coluna] = (
            taxa_uf[atual] - taxa_uf[anterior]
        )

    # Ordena pela taxa do ano mais recente.

    if anos_uf:
        taxa_uf = taxa_uf.sort_values(
            anos_uf[-1],
            ascending=False
        )

    # --------------------------------------------------------
    # 4.8 DISTRIBUIÇÃO DOS MUNICÍPIOS POR FAIXA
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

    # Classifica cada município conforme a quantidade
    # absoluta de abstenções.

    mun["FAIXA"] = pd.cut(
        mun["QT_ABSTENCOES"],
        bins=limites,
        labels=faixas
    )

    # Conta municípios por faixa e ano.

    cont = mun.groupby(
        ["FAIXA", "ANO"],
        observed=False
    ).size().unstack(
        "ANO",
        fill_value=0
    )

    # Calcula o percentual de municípios por faixa.
    # A divisão é feita por ano, não pelo total geral.

    pct = cont.div(
        cont.sum(axis=0).replace(0, np.nan),
        axis=1
    ) * 100

    # --------------------------------------------------------
    # 4.9 DISTRIBUIÇÃO ESTATÍSTICA MUNICIPAL
    # --------------------------------------------------------

    # Estatísticas descritivas das taxas municipais.

    estatisticas = mun.groupby(
        "ANO"
    )["TAXA"].describe()

    # --------------------------------------------------------
    # 4.10 COMPARAÇÃO ENTRE MUNICÍPIOS
    # --------------------------------------------------------

    comparacao = pd.DataFrame()
    aumentos = pd.DataFrame()
    quedas = pd.DataFrame()

    anos_disponiveis = sorted(mun["ANO"].unique())

    # A comparação exige pelo menos dois anos.

    if len(anos_disponiveis) >= 2:

        # Seleciona os dois anos mais recentes.

        anterior = anos_disponiveis[-2]
        atual = anos_disponiveis[-1]

        # Chave de identificação dos municípios.

        chave = [
            "SG_UF",
            "CD_MUNICIPIO"
        ]

        # Dados do ano anterior.

        dados_ant = mun[
            mun["ANO"] == anterior
        ][
            chave + [
                "NM_MUNICIPIO",
                "QT_APTOS",
                "TAXA"
            ]
        ].copy()

        # Dados do ano atual.

        dados_atual = mun[
            mun["ANO"] == atual
        ][
            chave + [
                "NM_MUNICIPIO",
                "QT_APTOS",
                "TAXA"
            ]
        ].copy()

        # Mantém somente municípios presentes nos dois anos.

        comparacao = dados_ant.merge(
            dados_atual,
            on=chave,
            how="inner",
            suffixes=(
                f"_{anterior}",
                f"_{atual}"
            )
        )

        # Calcula a variação em pontos percentuais.

        comparacao["VAR_pp"] = (
            comparacao[f"TAXA_{atual}"]
            - comparacao[f"TAXA_{anterior}"]
        )

        # Considera o mínimo de eleitores aptos
        # no ano mais recente.

        grandes = comparacao[
            comparacao[f"QT_APTOS_{atual}"] >= min_aptos
        ].copy()

        # Municípios com os maiores aumentos.

        aumentos = grandes.sort_values(
            "VAR_pp",
            ascending=False
        ).head(15)

        # Municípios com as maiores quedas.

        quedas = grandes.sort_values(
            "VAR_pp",
            ascending=True
        ).head(15)

    # --------------------------------------------------------
    # 4.11 RETORNO DOS RESULTADOS
    # --------------------------------------------------------

    # Entrega todos os resultados organizados.
    # Cada chave poderá ser acessada pelo processamento.py.

    resultados = {
        "base": base,
        "resumo": diag.round(2),
        "nacional": nacional.round(2),
        "municipios": mun,
        "estados": uf,
        "comparativo_ufs": taxa_uf.round(2),
        "faixas_quantidade": cont,
        "faixas_percentual": pct.round(2),
        "estatisticas": estatisticas.round(2),
        "comparacao_municipios": comparacao.round(2),
        "maiores_aumentos": aumentos.round(2),
        "maiores_quedas": quedas.round(2)
    }

    return resultados
