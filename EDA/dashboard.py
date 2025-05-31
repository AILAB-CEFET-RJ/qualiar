import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração inicial
st.set_page_config(page_title="Análise Ambiental e de Saúde", layout="wide")
sns.set_style("whitegrid")

POLUENTES_TRADUCAO = {
    'pm2_5': 'PM2.5 (µg/m³)',
    'pm10': 'PM10 (µg/m³)',
    'co': 'Monóxido de Carbono (CO)',
    'no': 'Óxido de Nitrogênio (NO)',
    'no2': 'Dióxido de Nitrogênio (NO₂)',
    'nox': 'Óxidos de Nitrogênio (NOx)',
    'so2': 'Dióxido de Enxofre (SO₂)',
    'o3': 'Ozônio (O₃)',
    'chuva': 'Precipitação (mm)',
    'temp': 'Temperatura (°C)',
    'ur': 'Umidade Relativa (%)'
}

# Carregamento dos dados
@st.cache_data
def load_sensor_data():
    urls = {
        'bangu': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_bangu_preenchido.csv',
        'campo_grande': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_campo_grande_preenchido.csv',
        'pedra_guaratiba': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_pedra_guaratiba_preenchido.csv',
        'iraja': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_iraja_preenchido.csv',
        'sao_cristovao': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_sao_cristovao_preenchido.csv',
        'tijuca': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_tijuca_preenchido.csv',
        'centro': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_centro_preenchido.csv',
        'copacabana': 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_copacabana_preenchido.csv'
    }
    
    dfs = []
    for name, url in urls.items():
        df = pd.read_csv(url)
        dfs.append(df)
    
    df_sensor = pd.concat(dfs, ignore_index=True)
    
    # Processamento dos dados
    poluentes = [col for col in df_sensor.columns if col not in ['data_formatada', 'ano', 'mes', 'data', 'nome_estacao']]
    df_sensor_aggregated = df_sensor.groupby(by=['nome_estacao', 'data_formatada'])[list(POLUENTES_TRADUCAO.keys()) + ['ano', 'mes']].mean().reset_index()
    
    return df_sensor_aggregated, poluentes

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

  dfs = []
  for name, url in urls.items():
      df = pd.read_csv(url)
      dfs.append(df)
    
  df_sus = pd.concat(dfs, ignore_index=True)
  
  interest_columns = ['UF_ZI', 'ANO_CMPT', 'MES_CMPT', 'MUNIC_RES', 'NASC', 'SEXO', 'DT_INTER', 'DT_SAIDA', 'DIAG_PRINC', 'DIAG_SECUN', 'IDADE', 'DIAS_PERM', 'MORTE']

  df_sus = df_sus[interest_columns]
  
  municipios_rio_de_janeiro = 330455
  
  df_sus = df_sus[df_sus['UF_ZI'] == municipios_rio_de_janeiro]

  df_sus_aggregated = df_sus.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
      num_internacoes=('DT_INTER', 'count')
  ).reset_index()
  
  df_sus_aggregated = df_sus_aggregated.rename(columns={'ANO_CMPT': 'ano', 'MES_CMPT': 'mes'})
  df_sus_aggregated['mes_ano'] = df_sus_aggregated['ano'].astype(str) + '-' + df_sus_aggregated['mes'].astype(str)
  
  return df_sus, df_sus_aggregated

# Sidebar - Navegação
st.sidebar.title("Menu de Navegação")
pagina_selecionada = st.sidebar.radio(
    "Selecione a página:",
    ["🏭 Análise de Sensores", "🩺 Dados de Saúde", "📈 Poluentes x Doenças"]
)

# Carregar os dados dos sensores e do SUS
df_sensor, poluentes = load_sensor_data()
df_sus, df_sus_aggregated = load_sus_data()

# Página: Análise de Sensores
if pagina_selecionada == "🏭 Análise de Sensores":
    st.title("🏭 Análise de Dados de Sensores Ambientais")
    
    with st.sidebar:
      st.header("⚙️ Configurações")
      
      # Seleção da estação (incluindo opção 'Geral')
      estacoes = list(df_sensor['nome_estacao'].unique())
      estacoes.insert(0, 'Geral')
      selected_estacao = st.selectbox(
          'Selecione a estação:', 
          estacoes,
          key='estacao_select'
      )
      
      # Seleção de poluentes com nomes formatados
      selected_poluentes = st.multiselect(
          'Selecione as variáveis:', 
          options=list(POLUENTES_TRADUCAO.keys()),
          format_func=lambda x: POLUENTES_TRADUCAO[x],
          default=['pm2_5', 'temp'],
          key='poluentes_multiselect'
      )
      
      # Seleção de anos
      available_years = sorted(df_sensor['ano'].unique())
      selected_years = st.multiselect(
          'Selecione os anos:', 
          available_years,
          default=[available_years[-1]],
          key='years_multiselect'
      )
      
      # Seleção de meses com nomes
      month_names = {
          1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
          5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
          9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
      }
      selected_months = st.multiselect(
          'Selecione os meses:', 
          options=month_names.keys(),
          format_func=lambda x: month_names[x],
          default=list(month_names.keys())[:1],
          key='months_multiselect'
      )

    # Filtragem e visualização dos dados
    if not selected_poluentes or not selected_years or not selected_months:
      st.warning("Por favor, selecione pelo menos uma variável, um ano e um mês.")
    else:
        df_filtered = df_sensor[
            (df_sensor['nome_estacao'] == selected_estacao) &
            (df_sensor['ano'].isin(selected_years)) &
            (df_sensor['mes'].isin(selected_months))
        ].sort_values('data_formatada')
        
        if df_filtered.empty:
            st.error("Nenhum dado encontrado com os filtros selecionados.")
        else:
            # Container principal
            main_container = st.container()
            
            with main_container:
                st.subheader(f"📊 Dados para a estação: {selected_estacao}")
                
                # Gráficos para cada variável selecionada
                for poluente in selected_poluentes:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    
                    # Plot para cada combinação de ano e mês
                    for year in selected_years:
                        for month in selected_months:
                            mask = (df_filtered['ano'] == year) & (df_filtered['mes'] == month)
                            temp_df = df_filtered[mask]
                            
                            if not temp_df.empty:
                                label = f"{year} - {month_names[month]}"
                                ax.plot(
                                    temp_df['data_formatada'], 
                                    temp_df[poluente], 
                                    label=label, 
                                    marker='o', 
                                    markersize=5,
                                    linewidth=2
                                )
                    
                    # Configurações do gráfico
                    ax.set_title(f"{POLUENTES_TRADUCAO[poluente]} - Estação {selected_estacao}", pad=20)
                    ax.set_xlabel("Data", labelpad=10)
                    ax.set_ylabel(POLUENTES_TRADUCAO[poluente], labelpad=10)
                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                    
                    # Formatação do eixo x
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    # Exibe o gráfico
                    st.pyplot(fig)
                    
                    # Espaçamento entre gráficos
                    st.markdown("---")
            
            # Seção de dados brutos
            with st.expander("📁 Visualizar Dados Brutos", expanded=False):
                st.dataframe(
                    df_filtered[['data_formatada', 'ano', 'mes'] + selected_poluentes].rename(columns=POLUENTES_TRADUCAO),
                    height=300,
                    use_container_width=True
                )
                
                # Opção para download
                csv = df_filtered[['data_formatada', 'ano', 'mes'] + selected_poluentes].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar dados como CSV",
                    data=csv,
                    file_name=f'dados_{selected_estacao}.csv',
                    mime='text/csv'
                )
            
# elif pagina_selecionada == "🩺 Dados de Saúde":
#     st.title("🩺 Dados de Doenças Respiratórias")
    
#     # st.line_chart(df_doencas.set_index('data'))
    
#     with st.expander("Dados Brutos"):
#         st.dataframe(df_sus)

# Página: Correlação
elif pagina_selecionada == "📈 Poluentes x Doenças":
    st.title("📈 Relação entre Poluentes e Doenças Respiratórias")
    
    # Merge dos dados
    df_merged = pd.merge(df_sensor, df_sus_aggregated, on=['ano', 'mes'], how='inner')
    
    # Seleção e cálculo da correlação
    variaveis = ['pm2_5', 'pm10', 'co', 'o3', 'no', 'no2', 'nox', 'so2', 'chuva', 'temp', 'ur', 'num_internacoes']
    correlation_matrix = df_merged[variaveis].corr()
    
    # Mapeamento de nomes amigáveis
    nome_colunas = {
        'pm2_5': 'PM2.5', 
        'pm10': 'PM10',
        'co': 'CO',
        'o3': 'Ozônio',
        'no': 'NO',
        'no2': 'NO₂',
        'nox': 'NOx',
        'so2': 'SO₂',
        'chuva': 'Chuva',
        'temp': 'Temp.',
        'ur': 'Umidade',
        'num_internacoes': 'Internações'
    }
    
    # Aplica os nomes amigáveis
    correlation_matrix = correlation_matrix.rename(columns=nome_colunas, index=nome_colunas)
    
    # Configurações do gráfico
    plt.figure(figsize=(8, 5))
    
    # Paleta de cores personalizada
    cor_palette = sns.diverging_palette(10, 240, sep=20, as_cmap=True)
    
    # Plot do heatmap com estilo idêntico ao solicitado
    ax = sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap=cor_palette,
        fmt='.2f',
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'shrink': 0.7},
        annot_kws={'size': 10},
        vmin=-1,
        vmax=1
    )
    
    # Ajustes estéticos idênticos
    plt.title('Matriz de Correlação: Poluentes vs Internações\n',
              fontsize=13, pad=20, fontweight='bold')
    ax.set_facecolor('#f8f9fa')  # Fundo cinza claro
    
    # Melhorando os rótulos
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
    
    # Adicionando grade sutil
    for _, spine in ax.spines.items():
        spine.set_visible(True)
        spine.set_color('#dddddd')
    
    # Destacando valores importantes (|correlação| >= 0.45)
    for text in ax.texts:
        t = float(text.get_text())
        if abs(t) >= 0.45:
            text.set_fontweight('bold')
    
    plt.tight_layout()
    st.pyplot(plt)
    
    # Legenda explicativa
    st.markdown("""
    <style>
        .legenda-box {
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            border-left: 4px solid #6c757d;
        }
    </style>
    <div class="legenda-box">
        <strong>Interpretação:</strong><br>
        • Correlação positiva (valores próximos de +1): ambas as variáveis aumentam juntas<br>
        • Correlação negativa (valores próximos de -1): uma variável aumenta enquanto a outra diminui<br>
        • Valores em <strong>negrito</strong> indicam correlações moderadas/fortes (|r| ≥ 0.45)
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Gráficos de correlação e análises estatísticas...")
    
# # # Sidebar com controles
# # with st.sidebar:
# #     st.header("⚙️ Configurações")
    
# #     # Seleção da estação (única)
# #     selected_estacao = st.selectbox(
# #         'Selecione a estação:', 
# #         df_sensor['nome_estacao'].unique(),
# #         key='estacao_select'
# #     )
    
# #     # Seleção múltipla de poluentes
# #     selected_poluentes = st.multiselect(
# #         'Selecione os poluentes/variáveis:', 
# #         poluentes,
# #         default=['pm2_5', 'temp'],
# #         key='poluentes_multiselect'
# #     )
    
# #     # Seleção múltipla de anos
# #     available_years = sorted(df_sensor['ano'].unique())
# #     selected_years = st.multiselect(
# #         'Selecione os anos:', 
# #         available_years,
# #         default=[available_years[-1]],  # Último ano disponível por padrão
# #         key='years_multiselect'
# #     )
    
# #     # Seleção múltipla de meses
# #     month_names = {
# #         1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
# #         5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
# #         9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
# #     }
# #     selected_months = st.multiselect(
# #         'Selecione os meses:', 
# #         options=month_names.keys(),
# #         format_func=lambda x: month_names[x],
# #         default=list(month_names.keys())[:1],  # Primeiro mês por padrão
# #         key='months_multiselect'
# #     )

# # # Filtragem dos dados
# # if not selected_poluentes or not selected_years or not selected_months:
# #     st.warning("Por favor, selecione pelo menos um poluente, um ano e um mês.")
# # else:
# #     df_filtered = df_sensor[
# #         (df_sensor['nome_estacao'] == selected_estacao) &
# #         (df_sensor['ano'].isin(selected_years)) &
# #         (df_sensor['mes'].isin(selected_months))
# #     ]
    
# #     if df_filtered.empty:
# #         st.error("Nenhum dado encontrado com os filtros selecionados.")
# #     else:
# #         # Visualização dos dados
# #         st.subheader(f"📈 Dados para a estação: {selected_estacao}")
        
# #         # Criar uma figura para cada poluente
# #         for poluente in selected_poluentes:
# #             fig, ax = plt.subplots(figsize=(12, 4))
            
# #             # Plot para cada combinação de ano e mês
# #             for year in selected_years:
# #                 for month in selected_months:
# #                     mask = (df_filtered['ano'] == year) & (df_filtered['mes'] == month)
# #                     temp_df = df_filtered[mask]
                    
# #                     if not temp_df.empty:
# #                         label = f"{year} - {month_names[month]}"
# #                         ax.plot(temp_df['data_formatada'], temp_df[poluente], label=label, marker='o', markersize=4)
            
# #             ax.set_title(f"{poluente.upper()} - Estação {selected_estacao}")
# #             ax.set_xlabel("Data")
# #             ax.set_ylabel(poluente)
# #             ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# #             plt.xticks(rotation=45)
# #             plt.tight_layout()
            
# #             st.pyplot(fig)
        
# #         # Mostrar dados brutos (opcional)
# #         if st.checkbox("Mostrar dados brutos"):
# #             st.dataframe(df_filtered[['data_formatada', 'ano', 'mes'] + selected_poluentes])