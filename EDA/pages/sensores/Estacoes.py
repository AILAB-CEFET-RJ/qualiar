import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def show(df_sensor, POLUENTES_TRADUCAO, month_names, selected_estacoes): 
  st.title("🖥️ Análise avançada entre estações de qualidade do ar")
  with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Seleção de poluentes
            selected_poluentes = st.multiselect(
                'Selecione os poluentes:', 
                options=list(POLUENTES_TRADUCAO.keys()),
                format_func=lambda x: POLUENTES_TRADUCAO[x],
                default=['temp'],
                key='poluentes_multiselect_general'
            )
        
        with col2:
            # Seleção de anos com opção "Todos"
            available_years = sorted(df_sensor['ano'].unique())
            year_options = ['Todos'] + available_years
            selected_years = st.multiselect(
                'Selecione os anos:', 
                year_options,
                default=[available_years[-1]],
                key='years_multiselect_general'
            )
            
            if 'Todos' in selected_years:
                selected_years = available_years
        
        with col3:
            # Seleção de meses com opção "Todos"
            month_options = ['Todos'] + list(month_names.keys())
            selected_months = st.multiselect(
                'Selecione os meses:', 
                options=month_options,
                format_func=lambda x: month_names[x] if x != 'Todos' else 'Todos',
                default=[],
                key='months_multiselect_general'
            )
            
            if 'Todos' in selected_months:
                selected_months = list(month_names.keys())
                # Filtrar o DataFrame conforme seleções
                df_filtered = df_sensor[
                  (df_sensor['poluente'].isin(selected_poluentes)) &
                  (df_sensor['ano'].isin(selected_years)) &
                  (df_sensor['mes'].isin(selected_months)) &
                  (df_sensor['estacao'].isin(selected_estacoes))
                ]

  # Gráfico 1: Boxplot comparando distribuições dos poluentes entre estações
  st.subheader("Distribuição dos poluentes por estação")
  for poluente in selected_poluentes:
    df_plot = df_filtered[df_filtered['poluente'] == poluente]
    fig = px.box(
      df_plot,
      x='estacao',
      y='valor',
      color='estacao',
      title=f"Distribuição de {POLUENTES_TRADUCAO.get(poluente, poluente)} por estação",
      labels={'valor': 'Valor', 'estacao': 'Estação'}
    )
    st.plotly_chart(fig, use_container_width=True)

  # Gráfico 2: Linha temporal média dos poluentes por estação
  st.subheader("Evolução temporal dos poluentes por estação")
  for poluente in selected_poluentes:
    df_plot = df_filtered[df_filtered['poluente'] == poluente]
    if not df_plot.empty:
      df_plot['data'] = pd.to_datetime(df_plot[['ano', 'mes']].assign(dia=1))
      df_grouped = df_plot.groupby(['data', 'estacao'])['valor'].mean().reset_index()
      fig = px.line(
        df_grouped,
        x='data',
        y='valor',
        color='estacao',
        title=f"Evolução temporal de {POLUENTES_TRADUCAO.get(poluente, poluente)}",
        labels={'valor': 'Valor', 'data': 'Data', 'estacao': 'Estação'}
      )
      st.plotly_chart(fig, use_container_width=True)