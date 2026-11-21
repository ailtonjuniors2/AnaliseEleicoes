import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from processamento import obter_dados

INK = "#000000"
MUTED = "#000000"
LINE = "#E3E6EC"
BG = "#F6F7F9"
ABST = "#E4572E"  # abstenção
TEAL = "#0F766E"  # comparecimento / menor abstenção
PALETTE = [ABST, TEAL, "#3B5BA9", "#C9962B", "#7A4E9E", "#4B9CD3", "#8C8C8C"]

st.set_page_config(
    page_title="Análise Eleitoral",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, button, input {{
    font-family: 'IBM Plex Sans', sans-serif;
}}
.stApp {{ background-color: {BG}; }}
.block-container {{ padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1280px; }}
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

[data-testid="stSidebar"] {{ background: white; border-right: 1px solid {LINE}; }}
[data-testid="stSidebar"] h2 {{ font-size: 1.1rem; }}

[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 10px; }}
.stPlotlyChart {{ background: white; border: 1px solid {LINE}; border-radius: 10px; padding: 8px; }}

/* Texto preto em toda a interface */
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
    return obter_dados(
        turno=turno, excluir_exterior=excluir_exterior, min_aptos=min_aptos
    )


def achatar(resultado) -> dict[str, pd.DataFrame]:
    """Transforma o retorno (DataFrame, dict ou tupla) em {nome: DataFrame}."""
    if isinstance(resultado, pd.DataFrame):
        return {"Dados": resultado}
    if isinstance(resultado, dict):
        itens = resultado.items()
    elif isinstance(resultado, (list, tuple)):
        itens = ((f"Tabela {i + 1}", v) for i, v in enumerate(resultado))
    else:
        return {}
    return {str(k): v for k, v in itens if isinstance(v, pd.DataFrame)}


def norm(txt: str) -> str:
    s = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return s.upper().replace(" ", "_")


def adivinhar(colunas, candidatos, trechos):
    """Procura primeiro nome exato e depois por trecho. Retorna None se não achar."""
    mapa = {norm(c): c for c in colunas}
    for c in candidatos:
        if c in mapa:
            return mapa[c]
    for n, original in mapa.items():
        if any(t in n for t in trechos):
            return original
    return None


# Tabelas que NÃO aparecem no seletor (comparação por trecho do nome, sem acento/maiúscula)
TABELAS_OCULTAS = ["COMPARATIVO_UFS", "FAIXAS_QUANTIDADE", "FAIXAS_PERCENTUAL"]

NENHUMA = "(nenhuma)"
ESCOLHA = "(escolha)"


def escolher(rotulo, colunas, padrao, obrigatoria=False):
    opcoes = [ESCOLHA if obrigatoria else NENHUMA] + list(colunas)
    idx = opcoes.index(padrao) if padrao in opcoes else 0
    valor = st.selectbox(rotulo, opcoes, index=idx)
    return None if valor in (NENHUMA, ESCOLHA) else valor


def estilizar(fig, altura=400):
    fig.update_layout(
        height=altura,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="IBM Plex Sans", color=INK, size=13),
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16, color=INK), x=0.01),
        legend=dict(title=None, orientation="h", y=-0.18),
        colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


st.title("Análise comparativa da abstenção eleitoral")
st.markdown(
    '<p class="subtitulo">Compare a abstenção entre anos, estados e municípios. '
    "Use a barra lateral para definir o recorte.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Análise")
    turno = st.radio("Turno", [1, 2], horizontal=True)
    excluir_exterior = st.checkbox("Excluir eleitores do exterior")
    min_aptos = st.number_input(
        "Mínimo de eleitores aptos por município", 0, 500_000, 5000, step=1000
    )

try:
    resultado = carregar(turno, excluir_exterior, int(min_aptos))
except Exception as erro:
    st.error("Não foi possível carregar os dados com `obter_dados()`.")
    st.exception(erro)
    st.stop()

tabelas = {
    nome: tab
    for nome, tab in achatar(resultado).items()
    if not any(t in norm(nome) for t in TABELAS_OCULTAS)
}
if not tabelas:
    st.error(
        f"`obter_dados()` devolveu `{type(resultado).__name__}`, "
        "e o app espera um DataFrame, ou um dicionário/tupla com DataFrames."
    )
    st.stop()

with st.sidebar:
    if len(tabelas) > 1:
        nome_tabela = st.selectbox("Tabela de dados", list(tabelas))
    else:
        nome_tabela = next(iter(tabelas))
    bruto = tabelas[nome_tabela]
    try:
        # índice padrão (0,1,2...) é descartado; índices com nome viram colunas
        bruto = bruto.reset_index(drop=isinstance(bruto.index, pd.RangeIndex))
    except ValueError:  # índice com o mesmo nome de uma coluna
        bruto = bruto.reset_index(drop=True)
    bruto = bruto.loc[:, ~bruto.columns.duplicated()]
    cols = list(bruto.columns)

    with st.expander("Colunas dos dados"):
        c_ano = escolher("Ano", cols, adivinhar(cols, ["ANO", "ANO_ELEICAO", "NR_ANO"], ["ANO"]))
        c_uf = escolher("Estado (UF)", cols, adivinhar(cols, ["UF", "SG_UF", "ESTADO", "SIGLA_UF"], ["UF", "ESTADO"]))
        c_mun = escolher("Município", cols, adivinhar(cols, ["MUNICIPIO", "NM_MUNICIPIO", "NOME_MUNICIPIO", "CIDADE"],
                                                      ["MUNIC", "CIDADE"]))
        c_aptos = escolher("Eleitores aptos", cols,
                           adivinhar(cols, ["APTOS", "QT_APTOS", "ELEITORES_APTOS", "ELEITORADO", "QT_ELEITORES_APTOS"],
                                     ["APTO", "ELEITORADO"]))
        c_abst = escolher(
            "Abstenções (quantidade ou %)", cols,
            adivinhar(cols, ["ABSTENCOES", "QT_ABSTENCOES", "ABSTENCAO", "QT_ABSTENCAO", "PCT_ABSTENCAO"], ["ABST"]),
            obrigatoria=True,
        )

if c_abst is None:
    st.info("Escolha a coluna de abstenções em **Colunas dos dados**, na barra lateral.")
    st.stop()

tem_aptos = c_aptos is not None
df = pd.DataFrame(index=bruto.index)  # índice fixo: evita colunas vazias/NaN

ano_num = pd.to_numeric(bruto[c_ano], errors="coerce") if c_ano else None
ano_numerico = ano_num is not None and ano_num.notna().any()
if ano_numerico:
    df["ANO"] = ano_num
else:
    df["ANO"] = bruto[c_ano].astype(str) if c_ano else "Único"

df["UF"] = bruto[c_uf].astype(str) if c_uf else "Brasil"
df["MUN"] = bruto[c_mun].astype(str) if c_mun else None
df["ABST"] = pd.to_numeric(bruto[c_abst], errors="coerce")
if tem_aptos:
    df["APTOS"] = pd.to_numeric(bruto[c_aptos], errors="coerce")
    df = df[df["APTOS"] > 0].copy()
    df["TAXA"] = df["ABST"] / df["APTOS"] * 100
else:
    df["TAXA"] = df["ABST"]  # assume que a coluna já está em %
    maximo = df["TAXA"].max()
    if maximo <= 1:  # proporção (0 a 1): converte para %
        df["TAXA"] = df["TAXA"] * 100
    elif maximo > 100:
        st.warning(
            "A coluna de abstenções tem valores acima de 100, então parece ser uma quantidade. "
            "Escolha também a coluna de **Eleitores aptos** em *Colunas dos dados*."
        )

df = df.dropna(subset=["ABST", "ANO"]).copy()
if ano_numerico:
    df["ANO"] = df["ANO"].round().astype(int)
if df.empty:
    st.warning("Os dados ficaram vazios após o tratamento. Confira o mapeamento das colunas "
               "ou reduza o mínimo de eleitores aptos.")
    st.stop()


def agrupar(d: pd.DataFrame, chaves) -> pd.DataFrame:
    """Taxa agregada: ponderada pelos aptos quando existem, senão média simples."""
    if tem_aptos:
        g = d.groupby(chaves)[["ABST", "APTOS"]].sum()
        g["TAXA"] = g["ABST"] / g["APTOS"] * 100
    else:
        g = d.groupby(chaves)[["TAXA"]].mean()
    return g.reset_index()


def taxa_total(d: pd.DataFrame) -> float:
    if tem_aptos:
        return d["ABST"].sum() / d["APTOS"].sum() * 100
    return d["TAXA"].mean()


with st.sidebar:
    st.header("Filtros")
    anos_disp = sorted(df["ANO"].unique())
    anos = st.multiselect("Anos", anos_disp, default=anos_disp)
    ufs_disp = sorted(df["UF"].unique())
    ufs = st.multiselect("Estados", ufs_disp, default=ufs_disp)
    muns = []
    if c_mun:
        muns_disp = sorted(df[df["UF"].isin(ufs)]["MUN"].unique())
        muns = st.multiselect("Municípios (opcional)", muns_disp, placeholder="Todos")

dff = df[df["ANO"].isin(anos) & df["UF"].isin(ufs)]
if muns:
    dff = dff[dff["MUN"].isin(muns)]
if dff.empty:
    st.warning("Nenhum dado para esse recorte. Amplie os filtros na barra lateral.")
    st.stop()

ano_ref = dff["ANO"].max()
atual = dff[dff["ANO"] == ano_ref]
anteriores = [a for a in dff["ANO"].unique() if a < ano_ref] if not isinstance(ano_ref, str) else []
delta = None
if anteriores:
    delta = taxa_total(atual) - taxa_total(dff[dff["ANO"] == max(anteriores)])

por_uf = agrupar(atual, "UF").sort_values("TAXA")

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    f"Abstenção em {ano_ref}",
    f"{taxa_total(atual):.1f}%",
    None if delta is None else f"{delta:+.1f} p.p. vs. eleição anterior",
    delta_color="inverse",
)
if tem_aptos:
    c2.metric("Eleitores aptos", f"{int(atual['APTOS'].sum()):,}".replace(",", "."))
else:
    c2.metric("Registros", f"{len(atual):,}".replace(",", "."))
if por_uf.empty:
    c3.metric("Menor abstenção", "-")
    c4.metric("Maior abstenção", "-")
else:
    c3.metric("Menor abstenção", por_uf["UF"].iloc[0], f"{por_uf['TAXA'].iloc[0]:.1f}%", delta_color="off")
    c4.metric("Maior abstenção", por_uf["UF"].iloc[-1], f"{por_uf['TAXA'].iloc[-1]:.1f}%", delta_color="off")

st.write("")

aba1, aba2, aba3, aba4 = st.tabs(["Evolução", "Estados", "Municípios", "Dados"])

with aba1:
    evo = agrupar(dff, ["ANO", "UF"]).rename(columns={"TAXA": "Abstenção (%)"})
    fig = px.line(evo, x="ANO", y="Abstenção (%)", color="UF", markers=True,
                  title="Abstenção por ano e estado")
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_xaxes(type="category")
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

with aba2:
    comp = agrupar(dff, ["UF", "ANO"]).rename(columns={"TAXA": "Abstenção (%)"})
    comp["ANO"] = comp["ANO"].astype(str)
    fig = px.bar(comp, x="UF", y="Abstenção (%)", color="ANO", barmode="group",
                 title="Comparação entre estados")
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(estilizar(fig, 420))

with aba3:
    if not c_mun:
        st.info("Selecione a coluna de município em **Colunas dos dados** para ver o ranking.")
    else:
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
            col.plotly_chart(estilizar(fig, 90 + n * 30))

with aba4:
    tabela = dff.rename(columns={"TAXA": "Abstenção (%)"}).round(2)
    st.dataframe(tabela, hide_index=True)
    st.download_button(
        "Baixar dados filtrados (CSV)",
        tabela.to_csv(index=False).encode("utf-8"),
        file_name="abstencao_filtrada.csv",
        mime="text/csv",
    )
