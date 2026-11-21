import streamlit as st
import pandas as pd
import plotly.express as px

from processamento import obter_dados



#CONFIGURAÇÃO DA PÁGINA

st.set_page_config(
    page_title="Análise Eleitoral",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

#ESTILIZAÇÃO
st.markdown("""
<style>

    .main {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        padding: 18px;
        border-radius: 12px;
    }

    h1, h2, h3 {
        color: #172554;
    }

</style>
""", unsafe_allow_html=True)

st.title("Análise Comparativa Eleitoral")

st.markdown(
    """
    Dashboard interativo para análise e comparação dos índices
    de abstenção eleitoral entre diferentes anos, estados e municípios.
    """
)

st.divider()
