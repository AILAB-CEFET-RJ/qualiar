import streamlit as st
from utils.config import POLUENTES_TRADUCAO, month_names
from utils.data_loader import load_sensor_data, load_sus_data, load_sensor_boxcox_data
import pages.poluentes_doencas.Poluentes_Doencas as poluentes_doencas
import pages.sensores.Analise_Sensores as analise_sensores
import pages.sus.Dados_Saude as dados_saude

# Configuração inicial
st.set_page_config(page_title="Análise Ambiental e de Saúde", layout="wide")

# Sidebar - Navegação
st.sidebar.title("Menu de Navegação")
pagina_selecionada = st.sidebar.radio(
    "Selecione a página:",
    ["🏭 Análise de Sensores", "🩺 Dados de Saúde", "📈 Poluentes x Doenças"]
)

# Carregar os dados 
df_sensor, poluentes = load_sensor_data()
df_sus, df_sus_aggregated = load_sus_data()
df_sensor_boxcox = load_sensor_boxcox_data()

# Adicionar colunas de latitude e longitude ao df_sensor
estacoes_coords = {
  "ESTAÇÃO BANGU": (-22.887910, -43.471074),
  "ESTAÇÃO CAMPO GRANDE": (-22.886255, -43.556522),
  "ESTAÇÃO CENTRO": (-22.908344, -43.178152),
  "ESTAÇÃO COPACABANA": (-22.965004, -43.180482),
  "ESTAÇÃO IRAJÁ": (-22.831621, -43.326845),
  "ESTAÇÃO PEDRA DE GUARATIBA": (-23.004379, -43.629010),
  "ESTAÇÃO SÃO CRISTÓVÃO": (-22.897771, -43.221745),
  "ESTAÇÃO TIJUCA": (-22.924915, -43.232657),
}

df_sensor["latitude"] = df_sensor["nome_estacao"].map(lambda x: estacoes_coords.get(x, (None, None))[0])
df_sensor["longitude"] = df_sensor["nome_estacao"].map(lambda x: estacoes_coords.get(x, (None, None))[1])

# Roteamento para páginas
if pagina_selecionada == "🏭 Análise de Sensores":
  analise_sensores.show(df_sensor, POLUENTES_TRADUCAO, month_names)
elif pagina_selecionada == "🩺 Dados de Saúde":
  dados_saude.show(df_sus, df_sus_aggregated, month_names)
  # dados_saude.show(df_sus, df_sus_aggregated)
elif pagina_selecionada == "📈 Poluentes x Doenças":
  poluentes_doencas.show(df_sensor_boxcox, df_sus_aggregated)