import streamlit as st
import pandas as pd
from utils.data_loader import load_sus_data, load_estacoes_data, load_rio_de_janeiro_qualiar_data, load_rio_de_janeiro_qualiar_treated_data
import pages.poluentes_doencas.Poluentes_Doencas as poluentes_doencas
import pages.sus.Dados_Saude as dados_saude
import pages.estacoes.Analise_Estacoes as analise_estacoes
import pages.rio.Analise_Rio as analise_rio

st.set_page_config(page_title="Análise Ambiental e de Saúde", layout="wide")

st.sidebar.title("Menu de Navegação")
pagina_selecionada = st.sidebar.radio(
    "Selecione a página:",
    ["🌆 Qualidade do ar Rio", "🩺 Dados de Saúde", "🗺️ Estações (EDA)", "📈 Poluentes x Doenças"]
)

# @st.cache_data(show_spinner=True)
# def _get_sus_prepared():
#     df_raw = load_sus_data()
#     # df_prepared = prepare_sus_df(df_raw)
#     return df_raw

# df_sus = _get_sus_prepared()

# @st.cache_data(show_spinner=True)
# def _get_estacoes_data():
#     df = load_estacoes_data()
#     return df

# df_estacoes = _get_estacoes_data()

# @st.cache_data(show_spinner=True)
# def _get_rio_prepared():
#     df = load_rio_de_janeiro_qualiar_data()

#     if "data_dia" in df.columns:
#         df["data_dia"] = pd.to_datetime(df["data_dia"], format="%Y-%m-%d", errors="coerce")

#     if "ano" not in df.columns and "data_dia" in df.columns:
#         df["ano"] = df["data_dia"].dt.year
#     if "mes" not in df.columns and "data_dia" in df.columns:
#         df["mes"] = df["data_dia"].dt.month

#     num_cols = ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"]
#     for c in num_cols:
#         if c in df.columns:
#             df[c] = pd.to_numeric(df[c], errors="coerce")

#     if "data_dia" in df.columns:
#         df["ano_mes"] = df["data_dia"].dt.to_period("M").astype(str)

#     return df

# df_rio = _get_rio_prepared()

# @st.cache_data(show_spinner=True)
# def _get_rio_prepared_treated():
#     df = load_rio_de_janeiro_qualiar_treated_data()

#     if "data_dia" in df.columns:
#         df["data_dia"] = pd.to_datetime(df["data_dia"], format="%Y-%m-%d", errors="coerce")

#     if "ano" not in df.columns and "data_dia" in df.columns:
#         df["ano"] = df["data_dia"].dt.year
#     if "mes" not in df.columns and "data_dia" in df.columns:
#         df["mes"] = df["data_dia"].dt.month

#     num_cols = ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"]
#     for c in num_cols:
#         if c in df.columns:
#             df[c] = pd.to_numeric(df[c], errors="coerce")

#     if "data_dia" in df.columns:
#         df["ano_mes"] = df["data_dia"].dt.to_period("M").astype(str)

#     return df

# df_rio_treated = _get_rio_prepared_treated()

if st.session_state.get("__page") != pagina_selecionada:
    st.cache_data.clear()
    st.session_state["__page"] = pagina_selecionada

# Roteamento para páginas
if pagina_selecionada == "🌆 Qualidade do ar Rio":
    @st.cache_data(show_spinner=True, max_entries=1)
    def _get_rio_data():
        return load_rio_de_janeiro_qualiar_data()
    df_rio = _get_rio_data()    
    analise_rio.show(df_rio)

elif pagina_selecionada == "🩺 Dados de Saúde":
    @st.cache_data(show_spinner=True, max_entries=1)
    def _get_sus_data():
        return load_sus_data()
    df_sus = _get_sus_data()
    dados_saude.show(df_sus)

elif pagina_selecionada == "🗺️ Estações (EDA)":
    @st.cache_data(show_spinner=True, max_entries=1)
    def _get_estacoes_data():
        return load_estacoes_data()
    df_estacoes = _get_estacoes_data()
    analise_estacoes.show(df_estacoes)

elif pagina_selecionada == "📈 Poluentes x Doenças":
    @st.cache_data(show_spinner=True, max_entries=1)
    def _get_rio_treated_data():
        return load_rio_de_janeiro_qualiar_treated_data()
    df_rio_treated = _get_rio_treated_data()
    @st.cache_data(show_spinner=True, max_entries=1)
    def _get_sus_data():
        return load_sus_data()
    df_sus = _get_sus_data()
    poluentes_doencas.show(df_sus, df_rio_treated)