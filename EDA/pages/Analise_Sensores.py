import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def show(df_sensor, POLUENTES_TRADUCAO, month_names):
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