import streamlit as st
from utils.config import POLUENTES_TRADUCAO, month_names
from utils.data_loader import load_sensor_data, load_sus_data, load_sensor_boxcox_data
import pages.Poluentes_Doencas as poluentes_doencas
import pages.Analise_Sensores as analise_sensores

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

# Roteamento para páginas
if pagina_selecionada == "🏭 Análise de Sensores":
  analise_sensores.show(df_sensor, POLUENTES_TRADUCAO, month_names)
  st.title("🏭 Análise de Sensores")
  pass
elif pagina_selecionada == "🩺 Dados de Saúde":
  st.title("🩺 Dados de Saúde")
  pass
  # dados_saude.show(df_sus, df_sus_aggregated)
elif pagina_selecionada == "📈 Poluentes x Doenças":
  poluentes_doencas.show(df_sensor_boxcox, df_sus_aggregated)