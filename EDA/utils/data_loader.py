import pandas as pd
import streamlit as st
from sklearn.preprocessing import StandardScaler
from utils.config import POLUENTES_TRADUCAO, POLUENTES_SCALED

# Carregamento dos dados
@st.cache_data
def load_sensor_data():
    url_bangu = 'data/Sensors/por_estacao/df_sensor_bangu_preenchido.csv'
    url_campo_grande = 'data/Sensors/por_estacao/df_sensor_campo_grande_preenchido.csv'
    url_pedra_guaratiba = 'data/Sensors/por_estacao/df_sensor_pedra_guaratiba_preenchido.csv'
    url_iraja = 'data/Sensors/por_estacao/df_sensor_iraja_preenchido.csv'
    url_sao_cristovao = 'data/Sensors/por_estacao/df_sensor_sao_cristovao_preenchido.csv'
    url_tijuca = 'data/Sensors/por_estacao/df_sensor_tijuca_preenchido.csv'
    url_centro = 'data/Sensors/por_estacao/df_sensor_centro_preenchido.csv'
    url_copacabana = 'data/Sensors/por_estacao/df_sensor_copacabana_preenchido.csv'
    
    df_sensor_bangu = pd.read_csv(url_bangu, sep=',')
    df_sensor_campo_grande = pd.read_csv(url_campo_grande, sep=',')
    df_sensor_pedra_guaratiba = pd.read_csv(url_pedra_guaratiba, sep=',')
    df_sensor_iraja = pd.read_csv(url_iraja, sep=',')
    df_sensor_sao_cristovao = pd.read_csv(url_sao_cristovao, sep=',')
    df_sensor_tijuca = pd.read_csv(url_tijuca, sep=',')
    df_sensor_centro = pd.read_csv(url_centro, sep=',')
    df_sensor_copacabana = pd.read_csv(url_copacabana, sep=',')
    
    df_sensor = pd.concat([
        df_sensor_bangu,
        df_sensor_campo_grande,
        df_sensor_pedra_guaratiba,
        df_sensor_iraja,
        df_sensor_sao_cristovao,
        df_sensor_tijuca,
        df_sensor_centro,
        df_sensor_copacabana
    ], ignore_index=True)
    
    # Processamento dos dados
    poluentes = [col for col in df_sensor.columns if col not in ['data_formatada', 'ano', 'mes', 'data', 'nome_estacao']]
    df_sensor_aggregated = df_sensor.groupby(by=['nome_estacao', 'data_formatada'])[list(POLUENTES_TRADUCAO.keys()) + ['ano', 'mes']].mean().reset_index()
    
    return df_sensor_aggregated, poluentes

# Carregamento dos dados
@st.cache_data
def load_sensor_boxcox_data():
  url_sensor_boxcox = 'data/Sensors/medicoes-sensores-boxcox.csv'

  df_sensor = pd.read_csv(url_sensor_boxcox, sep=',')
  
  cols_to_scale = ['pm2_5', 'pm10', 'nox', 'temp', 'o3']

  scaler = StandardScaler()

  df_sensor[['pm2_5_scaled', 'pm10_scaled', 'nox_scaled', 'temp_scaled', 'o3_scaled']] = scaler.fit_transform(df_sensor[cols_to_scale])
  
  df_sensor_aggregated = df_sensor.groupby(by=['ano', 'mes'])[list(POLUENTES_SCALED.keys())].mean().reset_index()
  
  return df_sensor_aggregated

@st.cache_data
def load_sus_data():
  urls = {
    'sus_2012': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2012.csv',
    'sus_2013': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2013.csv',
    'sus_2014': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2014.csv',
    'sus_2015': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2015.csv',
    'sus_2016': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2016.csv',
    'sus_2017': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2017.csv',
    'sus_2018': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2018.csv',
    'sus_2019': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2019.csv'
  }
  
  url_sus_2012 = 'data/datasus/dados_filtrados_2012.csv'
  url_sus_2013 = 'data/datasus/dados_filtrados_2013.csv'
  url_sus_2014 = 'data/datasus/dados_filtrados_2014.csv'
  url_sus_2015 = 'data/datasus/dados_filtrados_2015.csv'
  url_sus_2016 = 'data/datasus/dados_filtrados_2016.csv'
  url_sus_2017 = 'data/datasus/dados_filtrados_2017.csv'
  url_sus_2018 = 'data/datasus/dados_filtrados_2018.csv'
  url_sus_2019 = 'data/datasus/dados_filtrados_2019.csv'
  
  df_sus_2012 = pd.read_csv(url_sus_2012, sep=',')
  df_sus_2013 = pd.read_csv(url_sus_2013, sep=',')
  df_sus_2014 = pd.read_csv(url_sus_2014, sep=',')
  df_sus_2015 = pd.read_csv(url_sus_2015, sep=',')
  df_sus_2016 = pd.read_csv(url_sus_2016, sep=',')
  df_sus_2017 = pd.read_csv(url_sus_2017, sep=',')
  df_sus_2018 = pd.read_csv(url_sus_2018, sep=',')
  df_sus_2019 = pd.read_csv(url_sus_2019, sep=',')
    
  df_sus = pd.concat([
    df_sus_2012,
    df_sus_2013,
    df_sus_2014,
    df_sus_2015,
    df_sus_2016,
    df_sus_2017,
    df_sus_2018,
    df_sus_2019
  ], ignore_index=True)
  
  interest_columns = ['UF_ZI', 'ANO_CMPT', 'MES_CMPT', 'MUNIC_RES', 'NASC', 'SEXO', 'DT_INTER', 'DT_SAIDA', 'DIAG_PRINC', 'DIAG_SECUN', 'IDADE', 'DIAS_PERM', 'MORTE']

  df_sus = df_sus[interest_columns]
  
  municipios_rio_de_janeiro = 330455
  
  df_sus = df_sus[df_sus['UF_ZI'] == municipios_rio_de_janeiro]

  df_sus['data_formatada'] = pd.to_datetime(df_sus['DT_INTER'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

  df_sus.sort_values(by='data_formatada', inplace=True)

  df_sus = df_sus[(df_sus['data_formatada'] >= '2012-01-01')]

  df_sus['data_formatada_dt'] = pd.to_datetime(df_sus['data_formatada'])

  df_sus['ano'] = df_sus['data_formatada_dt'].dt.year
  df_sus['mes'] = df_sus['data_formatada_dt'].dt.month

  df_sus_aggregated = df_sus.groupby(['ano', 'mes']).agg(
      num_internacoes=('DT_INTER', 'count')
  ).reset_index()
  
  df_sus_aggregated['mes_ano'] = df_sus_aggregated['ano'].astype(str) + '-' + df_sus_aggregated['mes'].astype(str)
  
  return df_sus, df_sus_aggregated