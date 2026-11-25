import pandas as pd
import plotly.express as px
import streamlit as st

# Importa a função responsável por buscar os dados eleitorais brutos
from comparativoanos import executar_analises

INK = "#000000"  # Cor principal de texto
MUTED = "#000000"  # Cor de texto secundário
LINE = "#E3E6EC"  # Cor de bordas, divisores e linhas
BG = "#F6F7F9"  # Cor de fundo geral
ABST = "#E4572E"  # Cor de destaque para abstenção
TEAL = "#0F766E"  # Cor secundária de destaque

# Paleta de cores usada nos gráficos do Plotly para diferenciar séries
PALETTE = [ABST, TEAL, "#3B5BA9", "#C9962B", "#7A4E9E", "#4B9CD3", "#8C8C8C"]

st.set_page_config(
    page_title="Análise Eleitoral",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS geral para a página, com as fontes
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* Aplica a fonte */
html, body, [class*="css"], .stMarkdown, button, input {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

/* Fundo e espaçamento interno do container principal */
.stApp {{ background-color: {BG}; }}
.block-container {{ padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1280px; }}

/* Oculta menu padrão do Streamlit e o rodapé */
#MainMenu, footer {{ visibility: hidden; }}

h1 {{ color: {INK}; font-weight: 700; letter-spacing: -0.02em; font-size: 2.3rem !important; }}
h2, h3 {{ color: {INK}; font-weight: 600; letter-spacing: -0.01em; }}
.subtitulo {{ color: {MUTED}; font-size: 1.05rem; max-width: 46rem; margin-top: -0.4rem; }}

[data-testid="stMetric"] {{
    background: white;
    border: 1px solid {LINE};
    border-left: 4px solid {TEAL};
    border-radius: 10px;
    padding: 16px 18px;
}}
[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.9rem; }}
[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 700; }}

div[data-testid="stColumn"]:first-child [data-testid="stMetric"],
div[data-testid="column"]:first-child [data-testid="stMetric"] {{ border-left-color: {ABST}; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ height: 44px; padding: 0 18px; color: {MUTED}; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: {INK}; font-weight: 600; }}

/* Barra lateral, tabelas e gráficos em cartões brancos */
[data-testid="stSidebar"] {{ background: white; border-right: 1px solid {LINE}; }}
[data-testid="stSidebar"] h2 {{ font-size: 1.1rem; }}
[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 10px; }}
.stPlotlyChart {{ background: white; border: 1px solid {LINE}; border-radius: 10px; padding: 8px; }}

/* Garante cor preta legível em textos e rótulos internos do Streamlit */
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp li, .stApp label, .stApp label p,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMetricLabel"] p,
.stApp [data-testid="stMetricValue"],
.stApp [data-baseweb="tab"],
.stApp [data-baseweb="select"] div,
.stApp [data-testid="stSidebar"] span,
.stApp [data-testid="stExpander"] summary p,
.subtitulo {{ color: #000000 !important; }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Carregando dados...")
def carregar(turno: int, excluir_exterior: bool, min_aptos: int):
    # Carrega os dados de acordo com os parâmetros globais da análise.
    resultado = executar_analises(
        turno=turno, excluir_exterior=excluir_exterior, min_aptos=min_aptos
    )
    # A "base" traz todos os turnos e o exterior sem filtro, então não entra na análise
    resultado.pop("base", None)
    return resultado


def achatar(resultado) -> dict[str, pd.DataFrame]:
    # Normaliza o retorno de "obter_dados()" em um dicionário de DataFrames.
    # Aceita um DataFrame, um dict ou uma lista/tupla.
    if isinstance(resultado, pd.DataFrame):
        return {"Dados": resultado}
    if isinstance(resultado, dict):
        itens = resultado.items()
    elif isinstance(resultado, (list, tuple)):
        itens = ((f"Tabela {i + 1}", v) for i, v in enumerate(resultado))
    else:
        return {}

    # Filtra apenas os valores que de fato são DataFrames do pandas
    return {str(k): v for k, v in itens if isinstance(v, pd.DataFrame)}


# Nomes esperados das colunas na base de dados original
C_ANO = "ANO"
C_UF = "SG_UF"
C_MUN = "NM_MUNICIPIO"
C_APTOS = "QT_APTOS"
C_ABST = "QT_ABSTENCOES"
COLUNAS = [C_ANO, C_UF, C_MUN, C_APTOS, C_ABST]


def preparar(tab: pd.DataFrame) -> pd.DataFrame:
    # Reseta o índice do DataFrame e remove colunas duplicadas, se existirem.
    try:
        tab = tab.reset_index()
    except ValueError:
        # Caso algum nome de nível do índice conflite com o nome de uma coluna
        tab = tab.reset_index(drop=True)
    return tab.loc[:, ~tab.columns.duplicated()]


def estilizar(fig, altura=400):
    # Aplica um padrão visual consistente aos gráficos Plotly.
    fig.update_layout(
        height=altura,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="IBM Plex Sans", color=INK, size=13),
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16, color=INK), x=0.01),
        legend=dict(title=None, orientation="h", y=-0.18),  # Legenda horizontal abaixo do gráfico
        colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


# Cabeçalho
st.title("Análise comparativa da abstenção eleitoral")
st.markdown(
    '<p class="subtitulo">Compare a abstenção entre anos, estados e municípios. '
    "Use a barra lateral para definir o recorte.</p>",
    unsafe_allow_html=True,
)

# Parâmetros que alteram a consulta/extração inicial dos dados
with st.sidebar:
    st.header("Análise")
    turno = st.radio("Turno", [1, 2], horizontal=True)
    excluir_exterior = st.checkbox("Excluir eleitores do exterior")
    min_aptos = st.number_input(
        "Mínimo de eleitores aptos por município", 0, 500_000, 5000, step=1000
    )

# Se der erro ao carregar
try:
    resultado = carregar(turno, excluir_exterior, int(min_aptos))
except Exception as erro:
    st.error("Não foi possível carregar os dados com 'executar_analises()'.")
    st.exception(erro)
    st.stop()

# Prepara todas as tabelas e separa as que contêm as colunas eleitorais obrigatórias
todas = {nome: preparar(tab) for nome, tab in achatar(resultado).items()}
tabelas = {n: t for n, t in todas.items() if all(c in t.columns for c in COLUNAS)}

if not tabelas:
    st.error(
        "Nenhuma tabela devolvida por `executar_analises()` tem as colunas: " + ", ".join(COLUNAS)
    )
    st.stop()

# Se houver mais de uma tabela compatível, permite escolher qual será analisada
with st.sidebar:
    if len(tabelas) > 1:
        nome_tabela = st.selectbox("Tabela de dados", list(tabelas))
    else:
        nome_tabela = next(iter(tabelas))
    bruto = tabelas[nome_tabela]

# Limpeza
df = pd.DataFrame(
    {
        "ANO": pd.to_numeric(bruto[C_ANO], errors="coerce"),
        "UF": bruto[C_UF].astype(str),
        "MUN": bruto[C_MUN].astype(str),
        "ABST": pd.to_numeric(bruto[C_ABST], errors="coerce"),
        "APTOS": pd.to_numeric(bruto[C_APTOS], errors="coerce"),
    },
    index=bruto.index,
)

# Filtra registros válidos (eleitores aptos positivos) e remove linhas sem abstenção ou ano
df = df[df["APTOS"] > 0].dropna(subset=["ABST", "ANO"]).copy()
# Aplica o mínimo de eleitores aptos por município definido na barra lateral
df = df[df["APTOS"] >= min_aptos].copy()
if df.empty:
    st.warning("Os dados ficaram vazios após o tratamento. Reduza o mínimo de eleitores aptos.")
    st.stop()

# Garante ano inteiro e calcula a taxa percentual de abstenção por linha
df["ANO"] = df["ANO"].round().astype(int)
df["TAXA"] = df["ABST"] / df["APTOS"] * 100


def agrupar(d: pd.DataFrame, chaves) -> pd.DataFrame:
    # Agrega abstenções e eleitores aptos pelas chaves informadas e recalcula a taxa
    g = d.groupby(chaves)[["ABST", "APTOS"]].sum()
    g["TAXA"] = g["ABST"] / g["APTOS"] * 100
    return g.reset_index()


def taxa_total(d: pd.DataFrame) -> float:
    # Calcula a taxa geral ponderada de abstenção para o conjunto de dados `d`.
    return d["ABST"].sum() / d["APTOS"].sum() * 100


# Barra lateral
with st.sidebar:
    st.header("Filtros")
    anos_disp = sorted(df["ANO"].unique())
    anos = st.multiselect("Anos", anos_disp, default=anos_disp)

    ufs_disp = sorted(df["UF"].unique())
    ufs = st.multiselect("Estados", ufs_disp, default=ufs_disp)

    # Lista de municípios depende dos estados selecionados
    muns_disp = sorted(df[df["UF"].isin(ufs)]["MUN"].unique())
    muns = st.multiselect("Municípios (opcional)", muns_disp, placeholder="Todos")

# Aplica os filtros escolhidos
dff = df[df["ANO"].isin(anos) & df["UF"].isin(ufs)]
if muns:
    dff = dff[dff["MUN"].isin(muns)]

if dff.empty:
    st.warning("Nenhum dado para esse recorte. Amplie os filtros na barra lateral.")
    st.stop()

ano_ref = dff["ANO"].max()
atual = dff[dff["ANO"] == ano_ref]

# Busca o ano anterior disponível no recorte para calcular a variação em pontos percentuais
anteriores = [a for a in dff["ANO"].unique() if a < ano_ref]
delta = None
if anteriores:
    delta = taxa_total(atual) - taxa_total(dff[dff["ANO"] == max(anteriores)])

# Ordena os estados pela taxa de abstenção no ano de referência
por_uf = agrupar(atual, "UF").sort_values("TAXA")

c1, c2, c3, c4 = st.columns(4)

# Taxa geral de abstenção no ano de referência + variação vs. eleição anterior
c1.metric(
    f"Abstenção em {ano_ref}",
    f"{taxa_total(atual):.1f}%",
    None if delta is None else f"{delta:+.1f} p.p. vs. eleição anterior",
    delta_color="inverse",  # Aumento de abstenção aparece como negativo (vermelho) e queda como positivo
)

# Total de eleitores aptos no ano de referência (formatação numérica com ponto de milhar)
c2.metric("Eleitores aptos", f"{int(atual['APTOS'].sum()):,}".replace(",", "."))

# Estado com menor e maior taxa de abstenção no recorte atual
if por_uf.empty:
    c3.metric("Menor abstenção", "-")
    c4.metric("Maior abstenção", "-")
else:
    c3.metric("Menor abstenção", por_uf["UF"].iloc[0], f"{por_uf['TAXA'].iloc[0]:.1f}%", delta_color="off")
    c4.metric("Maior abstenção", por_uf["UF"].iloc[-1], f"{por_uf['TAXA'].iloc[-1]:.1f}%", delta_color="off")

st.write("")

# Abas
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    ["Evolução", "Estados", "Municípios", "Dados", "Outras tabelas", "Regiões"]
)

# Aba 1: taxa de abstenção por ano e estado
with aba1:
    evo = agrupar(dff, ["ANO", "UF"]).rename(columns={"TAXA": "Abstenção (%)"})
    fig = px.line(
        evo,
        x="ANO",
        y="Abstenção (%)",
        color="UF",
        markers=True,
        title="Abstenção por ano e estado",
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_xaxes(type="category")  # Trata o ano como categoria discreta (evita decimais no eixo X)
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

# Aba 2: gráfico de barras agrupadas comparando estados entre os anos selecionados
with aba2:
    comp = agrupar(dff, ["UF", "ANO"]).rename(columns={"TAXA": "Abstenção (%)"})
    comp["ANO"] = comp["ANO"].astype(str)  # Garante legenda discreta por ano
    fig = px.bar(
        comp,
        x="UF",
        y="Abstenção (%)",
        color="ANO",
        barmode="group",
        title="Comparação entre estados",
    )
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

# Aba 3: ranking dos municípios com maior e menor abstenção no ano de referência
with aba3:
    n = st.slider("Quantidade de municípios no ranking", 5, 30, 10)
    rank = agrupar(atual, ["UF", "MUN"]).sort_values("TAXA", ascending=False)
    rank["Local"] = rank["MUN"] + " (" + rank["UF"] + ")"

    ca, cb = st.columns(2)
    for col, dados, titulo, cor in (
            (ca, rank.head(n).iloc[::-1], f"Maior abstenção em {ano_ref}", ABST),
            (cb, rank.tail(n), f"Menor abstenção em {ano_ref}", TEAL),
    ):
        fig = px.bar(dados, x="TAXA", y="Local", orientation="h", title=titulo)
        fig.update_traces(marker_color=cor, hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_xaxes(ticksuffix="%", title=None)
        fig.update_yaxes(title=None)
        # Altura dinâmica proporcional à quantidade de municípios exibidos
        col.plotly_chart(estilizar(fig, 90 + n * 30))

# Aba 4: tabela detalhada dos dados filtrados e exportação em CSV
with aba4:
    tabela = dff.rename(columns={"TAXA": "Abstenção (%)"}).round(2)
    st.dataframe(tabela, hide_index=True)
    st.download_button(
        "Baixar dados filtrados (CSV)",
        tabela.to_csv(index=False).encode("utf-8"),
        file_name="abstencao_filtrada.csv",
        mime="text/csv",
    )

# Aba 5: tabelas adicionais retornadas por 'obter_dados()' que não seguem o schema principal
with aba5:
    outras = {n: t for n, t in todas.items() if n not in tabelas}
    if not outras:
        st.info("Não há outras tabelas.")
    else:
        nome_outra = st.selectbox("Tabela", list(outras))
        st.dataframe(outras[nome_outra], hide_index=True)
        st.download_button(
            "Baixar tabela (CSV)",
            outras[nome_outra].to_csv(index=False).encode("utf-8"),
            file_name=f"{nome_outra}.csv",
            mime="text/csv",
        )

# Aba 6: comparação da taxa de abstenção por região, com variação em p.p. entre os anos
with aba6:
    taxa_reg = todas.get("comparativo_regioes")
    if taxa_reg is None:
        st.info("A comparação por região não está disponível.")
    else:
        # Gráfico de barras agrupadas: taxa de abstenção por região, uma barra por ano
        ordem_reg = list(taxa_reg["REGIAO"])  # Já vem ordenada pela taxa do ano mais recente
        graf_reg = todas["regioes"].rename(columns={"TAXA": "Abstenção (%)"}).copy()
        graf_reg["ANO"] = graf_reg["ANO"].astype(str)  # Garante legenda discreta por ano
        fig = px.bar(
            graf_reg,
            x="REGIAO",
            y="Abstenção (%)",
            color="ANO",
            barmode="group",
            category_orders={"REGIAO": ordem_reg},
            title=f"Taxa de abstenção por região — turno {turno}",
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(estilizar(fig, 420))

        taxa_reg = taxa_reg.rename(columns={"REGIAO": "Região"})
        taxa_reg.columns = [str(c).strip() for c in taxa_reg.columns]  # Anos viram texto
        st.dataframe(taxa_reg, hide_index=True)
        st.download_button(
            "Baixar comparação por região (CSV)",
            taxa_reg.to_csv(index=False).encode("utf-8"),
            file_name="abstencao_regioes.csv",
            mime="text/csv",
        )
import pandas as pd
import plotly.express as px
import streamlit as st

# Importa a função responsável por buscar os dados eleitorais brutos
from processamento import obter_dados

INK = "#000000"      # Cor principal de texto
MUTED = "#000000"    # Cor de texto secundário
LINE = "#E3E6EC"     # Cor de bordas, divisores e linhas
BG = "#F6F7F9"       # Cor de fundo geral
ABST = "#E4572E"     # Cor de destaque para abstenção
TEAL = "#0F766E"     # Cor secundária de destaque

# Paleta de cores usada nos gráficos do Plotly para diferenciar séries 
PALETTE = [ABST, TEAL, "#3B5BA9", "#C9962B", "#7A4E9E", "#4B9CD3", "#8C8C8C"]

st.set_page_config(
    page_title="Análise Eleitoral",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS geral para a página, com as fontes
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* Aplica a fonte */
html, body, [class*="css"], .stMarkdown, button, input {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

/* Fundo e espaçamento interno do container principal */
.stApp {{ background-color: {BG}; }}
.block-container {{ padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1280px; }}

/* Oculta menu padrão do Streamlit e o rodapé */
#MainMenu, footer {{ visibility: hidden; }}

h1 {{ color: {INK}; font-weight: 700; letter-spacing: -0.02em; font-size: 2.3rem !important; }}
h2, h3 {{ color: {INK}; font-weight: 600; letter-spacing: -0.01em; }}
.subtitulo {{ color: {MUTED}; font-size: 1.05rem; max-width: 46rem; margin-top: -0.4rem; }}

[data-testid="stMetric"] {{
    background: white;
    border: 1px solid {LINE};
    border-left: 4px solid {TEAL};
    border-radius: 10px;
    padding: 16px 18px;
}}
[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.9rem; }}
[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 700; }}

div[data-testid="stColumn"]:first-child [data-testid="stMetric"],
div[data-testid="column"]:first-child [data-testid="stMetric"] {{ border-left-color: {ABST}; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ height: 44px; padding: 0 18px; color: {MUTED}; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: {INK}; font-weight: 600; }}

/* Barra lateral, tabelas e gráficos em cartões brancos */
[data-testid="stSidebar"] {{ background: white; border-right: 1px solid {LINE}; }}
[data-testid="stSidebar"] h2 {{ font-size: 1.1rem; }}
[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 10px; }}
.stPlotlyChart {{ background: white; border: 1px solid {LINE}; border-radius: 10px; padding: 8px; }}

/* Garante cor preta legível em textos e rótulos internos do Streamlit */
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp li, .stApp label, .stApp label p,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMetricLabel"] p,
.stApp [data-testid="stMetricValue"],
.stApp [data-baseweb="tab"],
.stApp [data-baseweb="select"] div,
.stApp [data-testid="stSidebar"] span,
.stApp [data-testid="stExpander"] summary p,
.subtitulo {{ color: #000000 !important; }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Carregando dados...")
def carregar(turno: int, excluir_exterior: bool, min_aptos: int):
    # Carrega os dados de acordo com os parâmetros globais da análise.
    return obter_dados(
        turno=turno, excluir_exterior=excluir_exterior, min_aptos=min_aptos
    )


def achatar(resultado) -> dict[str, pd.DataFrame]:
    # Normaliza o retorno de "obter_dados()" em um dicionário de DataFrames.
    # Aceita um DataFrame, um dict ou uma lista/tupla.
    if isinstance(resultado, pd.DataFrame):
        return {"Dados": resultado}
    if isinstance(resultado, dict):
        itens = resultado.items()
    elif isinstance(resultado, (list, tuple)):
        itens = ((f"Tabela {i + 1}", v) for i, v in enumerate(resultado))
    else:
        return {}

    # Filtra apenas os valores que de fato são DataFrames do pandas
    return {str(k): v for k, v in itens if isinstance(v, pd.DataFrame)}


# Nomes esperados das colunas na base de dados original
C_ANO = "ANO"
C_UF = "SG_UF"
C_MUN = "NM_MUNICIPIO"
C_APTOS = "QT_APTOS"
C_ABST = "QT_ABSTENCOES"
COLUNAS = [C_ANO, C_UF, C_MUN, C_APTOS, C_ABST]


def preparar(tab: pd.DataFrame) -> pd.DataFrame:
    # Reseta o índice do DataFrame e remove colunas duplicadas, se existirem.
    try:
        tab = tab.reset_index()
    except ValueError:
        # Caso algum nome de nível do índice conflite com o nome de uma coluna
        tab = tab.reset_index(drop=True)
    return tab.loc[:, ~tab.columns.duplicated()]


def estilizar(fig, altura=400):
    # Aplica um padrão visual consistente aos gráficos Plotly.
    fig.update_layout(
        height=altura,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="IBM Plex Sans", color=INK, size=13),
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16, color=INK), x=0.01),
        legend=dict(title=None, orientation="h", y=-0.18),  # Legenda horizontal abaixo do gráfico
        colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


# Cabeçalho
st.title("Análise comparativa da abstenção eleitoral")
st.markdown(
    '<p class="subtitulo">Compare a abstenção entre anos, estados e municípios. '
    "Use a barra lateral para definir o recorte.</p>",
    unsafe_allow_html=True,
)

# Parâmetros que alteram a consulta/extração inicial dos dados
with st.sidebar:
    st.header("Análise")
    turno = st.radio("Turno", [1, 2], horizontal=True)
    excluir_exterior = st.checkbox("Excluir eleitores do exterior")
    min_aptos = st.number_input(
        "Mínimo de eleitores aptos por município", 0, 500_000, 5000, step=1000
    )

# Se der erro ao carregar
try:
    resultado = carregar(turno, excluir_exterior, int(min_aptos))
except Exception as erro:
    st.error("Não foi possível carregar os dados com 'obter_dados()'.")
    st.exception(erro)
    st.stop()

# Prepara todas as tabelas e separa as que contêm as colunas eleitorais obrigatórias
todas = {nome: preparar(tab) for nome, tab in achatar(resultado).items()}
tabelas = {n: t for n, t in todas.items() if all(c in t.columns for c in COLUNAS)}

if not tabelas:
    st.error(
        "Nenhuma tabela devolvida por `obter_dados()` tem as colunas: " + ", ".join(COLUNAS)
    )
    st.stop()

# Se houver mais de uma tabela compatível, permite escolher qual será analisada
with st.sidebar:
    if len(tabelas) > 1:
        nome_tabela = st.selectbox("Tabela de dados", list(tabelas))
    else:
        nome_tabela = next(iter(tabelas))
    bruto = tabelas[nome_tabela]

# Limpeza
df = pd.DataFrame(
    {
        "ANO": pd.to_numeric(bruto[C_ANO], errors="coerce"),
        "UF": bruto[C_UF].astype(str),
        "MUN": bruto[C_MUN].astype(str),
        "ABST": pd.to_numeric(bruto[C_ABST], errors="coerce"),
        "APTOS": pd.to_numeric(bruto[C_APTOS], errors="coerce"),
    },
    index=bruto.index,
)

# Filtra registros válidos (eleitores aptos positivos) e remove linhas sem abstenção ou ano
df = df[df["APTOS"] > 0].dropna(subset=["ABST", "ANO"]).copy()
if df.empty:
    st.warning("Os dados ficaram vazios após o tratamento. Reduza o mínimo de eleitores aptos.")
    st.stop()

# Garante ano inteiro e calcula a taxa percentual de abstenção por linha
df["ANO"] = df["ANO"].round().astype(int)
df["TAXA"] = df["ABST"] / df["APTOS"] * 100


def agrupar(d: pd.DataFrame, chaves) -> pd.DataFrame:
    # Agrega abstenções e eleitores aptos pelas chaves informadas e recalcula a taxa
    g = d.groupby(chaves)[["ABST", "APTOS"]].sum()
    g["TAXA"] = g["ABST"] / g["APTOS"] * 100
    return g.reset_index()


def taxa_total(d: pd.DataFrame) -> float:
    # Calcula a taxa geral ponderada de abstenção para o conjunto de dados `d`.
    return d["ABST"].sum() / d["APTOS"].sum() * 100


# Barra lateral
with st.sidebar:
    st.header("Filtros")
    anos_disp = sorted(df["ANO"].unique())
    anos = st.multiselect("Anos", anos_disp, default=anos_disp)

    ufs_disp = sorted(df["UF"].unique())
    ufs = st.multiselect("Estados", ufs_disp, default=ufs_disp)

    # Lista de municípios depende dos estados selecionados
    muns_disp = sorted(df[df["UF"].isin(ufs)]["MUN"].unique())
    muns = st.multiselect("Municípios (opcional)", muns_disp, placeholder="Todos")

# Aplica os filtros escolhidos
dff = df[df["ANO"].isin(anos) & df["UF"].isin(ufs)]
if muns:
    dff = dff[dff["MUN"].isin(muns)]

if dff.empty:
    st.warning("Nenhum dado para esse recorte. Amplie os filtros na barra lateral.")
    st.stop()


ano_ref = dff["ANO"].max()
atual = dff[dff["ANO"] == ano_ref]

# Busca o ano anterior disponível no recorte para calcular a variação em pontos percentuais
anteriores = [a for a in dff["ANO"].unique() if a < ano_ref]
delta = None
if anteriores:
    delta = taxa_total(atual) - taxa_total(dff[dff["ANO"] == max(anteriores)])

# Ordena os estados pela taxa de abstenção no ano de referência
por_uf = agrupar(atual, "UF").sort_values("TAXA")

c1, c2, c3, c4 = st.columns(4)

# Taxa geral de abstenção no ano de referência + variação vs. eleição anterior
c1.metric(
    f"Abstenção em {ano_ref}",
    f"{taxa_total(atual):.1f}%",
    None if delta is None else f"{delta:+.1f} p.p. vs. eleição anterior",
    delta_color="inverse",  # Aumento de abstenção aparece como negativo (vermelho) e queda como positivo
)

# Total de eleitores aptos no ano de referência (formatação numérica com ponto de milhar)
c2.metric("Eleitores aptos", f"{int(atual['APTOS'].sum()):,}".replace(",", "."))

# Estado com menor e maior taxa de abstenção no recorte atual
if por_uf.empty:
    c3.metric("Menor abstenção", "-")
    c4.metric("Maior abstenção", "-")
else:
    c3.metric("Menor abstenção", por_uf["UF"].iloc[0], f"{por_uf['TAXA'].iloc[0]:.1f}%", delta_color="off")
    c4.metric("Maior abstenção", por_uf["UF"].iloc[-1], f"{por_uf['TAXA'].iloc[-1]:.1f}%", delta_color="off")

st.write("")

# Abas
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["Evolução", "Estados", "Municípios", "Dados", "Outras tabelas"]
)

# Aba 1: taxa de abstenção por ano e estado
with aba1:
    evo = agrupar(dff, ["ANO", "UF"]).rename(columns={"TAXA": "Abstenção (%)"})
    fig = px.line(
        evo,
        x="ANO",
        y="Abstenção (%)",
        color="UF",
        markers=True,
        title="Abstenção por ano e estado",
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_xaxes(type="category")  # Trata o ano como categoria discreta (evita decimais no eixo X)
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

# Aba 2: gráfico de barras agrupadas comparando estados entre os anos selecionados
with aba2:
    comp = agrupar(dff, ["UF", "ANO"]).rename(columns={"TAXA": "Abstenção (%)"})
    comp["ANO"] = comp["ANO"].astype(str)  # Garante legenda discreta por ano
    fig = px.bar(
        comp,
        x="UF",
        y="Abstenção (%)",
        color="ANO",
        barmode="group",
        title="Comparação entre estados",
    )
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

# Aba 3: ranking dos municípios com maior e menor abstenção no ano de referência
with aba3:
    n = st.slider("Quantidade de municípios no ranking", 5, 30, 10)
    rank = agrupar(atual, ["UF", "MUN"]).sort_values("TAXA", ascending=False)
    rank["Local"] = rank["MUN"] + " (" + rank["UF"] + ")"

    ca, cb = st.columns(2)
    for col, dados, titulo, cor in (
        (ca, rank.head(n).iloc[::-1], f"Maior abstenção em {ano_ref}", ABST),
        (cb, rank.tail(n), f"Menor abstenção em {ano_ref}", TEAL),
    ):
        fig = px.bar(dados, x="TAXA", y="Local", orientation="h", title=titulo)
        fig.update_traces(marker_color=cor, hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_xaxes(ticksuffix="%", title=None)
        fig.update_yaxes(title=None)
        # Altura dinâmica proporcional à quantidade de municípios exibidos
        col.plotly_chart(estilizar(fig, 90 + n * 30))

# Aba 4: tabela detalhada dos dados filtrados e exportação em CSV
with aba4:
    tabela = dff.rename(columns={"TAXA": "Abstenção (%)"}).round(2)
    st.dataframe(tabela, hide_index=True)
    st.download_button(
        "Baixar dados filtrados (CSV)",
        tabela.to_csv(index=False).encode("utf-8"),
        file_name="abstencao_filtrada.csv",
        mime="text/csv",
    )

# Aba 5: tabelas adicionais retornadas por 'obter_dados()' que não seguem o schema principal
with aba5:
    outras = {n: t for n, t in todas.items() if n not in tabelas}
    if not outras:
        st.info("Não há outras tabelas.")
    else:
        nome_outra = st.selectbox("Tabela", list(outras))
        st.dataframe(outras[nome_outra], hide_index=True)
        st.download_button(
            "Baixar tabela (CSV)",
            outras[nome_outra].to_csv(index=False).encode("utf-8"),
            file_name=f"{nome_outra}.csv",
            mime="text/csv",
        )
