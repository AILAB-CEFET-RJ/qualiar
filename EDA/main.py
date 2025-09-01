import streamlit as st
import pandas as pd
from utils.config import POLUENTES_TRADUCAO, month_names  
from utils.data_loader import load_sus_data, prepare_sus_df, load_estacoes_data, load_rio_de_janeiro_qualiar_data, load_rio_de_janeiro_qualiar_treated_data
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
#     df_prepared = prepare_sus_df(df_raw)
#     return df_prepared

@st.cache_data(show_spinner=True)
def _get_estacoes_data():
    df = load_estacoes_data()
    return df

df_estacoes = _get_estacoes_data()

@st.cache_data(show_spinner=True)
def _get_rio_prepared():
    df = load_rio_de_janeiro_qualiar_data()

    if "data_dia" in df.columns:
        df["data_dia"] = pd.to_datetime(df["data_dia"], format="%Y-%m-%d", errors="coerce")

    if "ano" not in df.columns and "data_dia" in df.columns:
        df["ano"] = df["data_dia"].dt.year
    if "mes" not in df.columns and "data_dia" in df.columns:
        df["mes"] = df["data_dia"].dt.month

    num_cols = ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "data_dia" in df.columns:
        df["ano_mes"] = df["data_dia"].dt.to_period("M").astype(str)

    return df

df_rio = _get_rio_prepared()

@st.cache_data(show_spinner=True)
def _get_rio_prepared_treated():
    df = load_rio_de_janeiro_qualiar_treated_data()

    if "data_dia" in df.columns:
        df["data_dia"] = pd.to_datetime(df["data_dia"], format="%Y-%m-%d", errors="coerce")

    if "ano" not in df.columns and "data_dia" in df.columns:
        df["ano"] = df["data_dia"].dt.year
    if "mes" not in df.columns and "data_dia" in df.columns:
        df["mes"] = df["data_dia"].dt.month

    num_cols = ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "data_dia" in df.columns:
        df["ano_mes"] = df["data_dia"].dt.to_period("M").astype(str)

    return df

df_rio_treated = _get_rio_prepared_treated()

if pagina_selecionada == "🌆 Qualidade do ar Rio":
    analise_rio.show(df_rio)

elif pagina_selecionada == "🩺 Dados de Saúde":
    # Carrega ON-DEMAND
    with st.spinner("Carregando dados do SUS..."):
        df_2012 = load_sus_data(2012)
        df_2013 = load_sus_data(2013)
        df_2014 = load_sus_data(2014)
        df_2015 = load_sus_data(2015)
        df_2016 = load_sus_data(2016)
        df_2017 = load_sus_data(2017)
        df_2018 = load_sus_data(2018)
        df_2019 = load_sus_data(2019)
        df_2020 = load_sus_data(2020)
        df_2021 = load_sus_data(2021)
        df_2022 = load_sus_data(2022)
        df_2023 = load_sus_data(2023)
        df_2024 = load_sus_data(2024)
        df_sus = pd.concat([
            df_2012, df_2013, df_2014, df_2015, df_2016, df_2017,
            df_2018, df_2019, df_2020, df_2021, df_2022, df_2023,
            df_2024
        ], ignore_index=True)
        df_sus = prepare_sus_df(df_sus)
        # df_sus = _get_sus_prepared()
    dados_saude.show(df_sus)

elif pagina_selecionada == "🗺️ Estações (EDA)":
    analise_estacoes.show(df_estacoes)

elif pagina_selecionada == "📈 Poluentes x Doenças":
    pass
    # Se essa página também usa SUS, carregue aqui on-demand:
    # with st.spinner("Carregando dados (SUS + Rio)..."):
        # df_sus = _get_sus_prepared()
    # poluentes_doencas.show(df_sus, df_rio_treated)