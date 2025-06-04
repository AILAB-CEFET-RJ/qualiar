import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def show(df_sus, df_sus_aggregated, month_names):
    st.title("🩺 Dados de Saúde - Internações por Doenças Respiratórias")
    
    # Adicionando informações sobre o dataset
    with st.expander("ℹ️ Sobre os dados"):
        st.markdown("""
        Este dataset contém informações de hospitalizações por doenças respiratórias na cidade do Rio de Janeiro.
        Cada linha representa uma internação com as seguintes informações:
        - **Data de internação** e **saída**
        - **Idade** e **sexo** do paciente
        - **Diagnósticos** principal e secundários
        - **Duração** da internação
        - **Óbito** (se ocorreu)
        """)
    
    # --- SEÇÃO 1: VISÃO GERAL ---
    st.header("📊 Visão Geral das Internações")
    
    # Criar colunas para os KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcular métricas
    total_internacoes = df_sus.shape[0]
    media_idade = df_sus['IDADE'].mean()
    taxa_mortalidade = df_sus['MORTE'].mean() * 100
    media_permanencia = df_sus['DIAS_PERM'].mean()
    
    # Exibir KPIs
    col1.metric("Total de Internações", f"{total_internacoes:,}".replace(",", "."))
    col2.metric("Média de Idade", f"{media_idade:.1f} anos")
    col3.metric("Taxa de Mortalidade", f"{taxa_mortalidade:.2f}%")
    col4.metric("Média de Permanência", f"{media_permanencia:.1f} dias")
    
    # --- SEÇÃO 2: ANÁLISE TEMPORAL ---
    st.header("📈 Análise Temporal")
    
    # Gráfico de linhas - Internações por mês/ano
    fig = px.line(df_sus_aggregated, 
                 x='mes_ano', 
                 y='num_internacoes',
                 title='Número de Internações por Mês/Ano',
                 labels={'mes_ano': 'Mês/Ano', 'num_internacoes': 'Número de Internações'},
                 markers=True)
    
    fig.update_layout(
        xaxis_title='Mês/Ano',
        yaxis_title='Número de Internações',
        hovermode="x unified",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- SEÇÃO 3: FILTROS E ANÁLISE DETALHADA ---
    st.header("🔍 Análise Detalhada")
    
    # Criar abas para diferentes análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Por Idade", "Por Sexo", "Por Diagnóstico", "Mortalidade", "Top Causas de Morte"])
    
    with tab1:
        # Análise por idade
        st.subheader("Distribuição por Idade")
        
        # Criar faixas etárias
        bins = [0, 5, 12, 18, 30, 50, 65, 100]
        labels = ['0-5', '6-12', '13-18', '19-30', '31-50', '51-65', '66+']
        df_sus['faixa_etaria'] = pd.cut(df_sus['IDADE'], bins=bins, labels=labels, right=False)
        
        # Agrupar por faixa etária
        df_idade = df_sus.groupby('faixa_etaria').size().reset_index(name='count')
        
        # Gráfico de barras
        fig = px.bar(df_idade, 
                    x='faixa_etaria', 
                    y='count',
                    title='Internações por Faixa Etária',
                    labels={'faixa_etaria': 'Faixa Etária', 'count': 'Número de Internações'})
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Análise por sexo
        st.subheader("Distribuição por Sexo")
        
        # Traduzir códigos de sexo
        sexo_map = {1: 'Masculino', 3: 'Feminino'}
        df_sus['sexo_desc'] = df_sus['SEXO'].map(sexo_map)
        
        # Agrupar por sexo
        df_sexo = df_sus.groupby('sexo_desc').size().reset_index(name='count')
        
        # Gráfico de pizza
        fig = px.pie(df_sexo, 
                    values='count', 
                    names='sexo_desc',
                    title='Proporção de Internações por Sexo',
                    hole=0.3)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Análise por diagnóstico
        st.subheader("Principais Diagnósticos")
        
        # Contar diagnósticos principais
        top_diag = df_sus['DIAG_PRINC'].value_counts().head(10).reset_index()
        top_diag.columns = ['diagnostico', 'count']
        
        # Gráfico de barras horizontais
        fig = px.bar(top_diag, 
                    y='diagnostico', 
                    x='count',
                    orientation='h',
                    title='Top 10 Diagnósticos Principais',
                    labels={'diagnostico': 'Código CID-10', 'count': 'Número de Internações'})
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Análise de mortalidade
        st.subheader("Análise de Mortalidade")
        
        # Agrupar por mês/ano e calcular taxa de mortalidade
        df_mortalidade = df_sus.groupby(['ANO_CMPT', 'MES_CMPT']).agg(
            total_internacoes=('MORTE', 'size'),
            total_obitos=('MORTE', 'sum')
        ).reset_index()
        
        df_mortalidade['taxa_mortalidade'] = (df_mortalidade['total_obitos'] / df_mortalidade['total_internacoes']) * 100
        df_mortalidade['mes_ano'] = df_mortalidade['ANO_CMPT'].astype(str) + '-' + df_mortalidade['MES_CMPT'].astype(str)
        
        # Gráfico de linhas
        fig = px.line(df_mortalidade, 
                     x='mes_ano', 
                     y='taxa_mortalidade',
                     title='Taxa de Mortalidade por Mês/Ano (%)',
                     labels={'mes_ano': 'Mês/Ano', 'taxa_mortalidade': 'Taxa de Mortalidade (%)'},
                     markers=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
      st.subheader("Top 10 Causas de Morte")
      
      # Filtrar apenas óbitos e contar diagnósticos principais
      df_obitos = df_sus[df_sus['MORTE'] == 1]
      top_causas_morte = df_obitos['DIAG_PRINC'].value_counts().head(10).reset_index()
      top_causas_morte.columns = ['diagnostico', 'obitos']
      
      if len(top_causas_morte) > 0:
          # Calcular total de internações por diagnóstico (incluindo não-óbitos)
          total_internacoes_diag = df_sus['DIAG_PRINC'].value_counts().reset_index()
          total_internacoes_diag.columns = ['diagnostico', 'total_internacoes']
          
          # Juntar os dados
          df_mortalidade_diag = pd.merge(top_causas_morte, total_internacoes_diag, on='diagnostico', how='left')
          
          # Calcular taxa de mortalidade
          df_mortalidade_diag['taxa_mortalidade'] = (df_mortalidade_diag['obitos'] / df_mortalidade_diag['total_internacoes']) * 100
          
          # Ordenar por número de óbitos
          df_mortalidade_diag = df_mortalidade_diag.sort_values('obitos', ascending=True)
          
          # Criar gráfico de barras
          fig = go.Figure()
          
          fig.add_trace(go.Bar(
              y=df_mortalidade_diag['diagnostico'],
              x=df_mortalidade_diag['obitos'],
              name='Óbitos',
              orientation='h',
              marker_color='#EF553B',
              text=[f"{rate:.1f}%" for rate in df_mortalidade_diag['taxa_mortalidade']],
              textposition='outside'
          ))
          
          # Configurações do layout
          fig.update_layout(
              title='Top 10 Causas de Morte por Doenças Respiratórias',
              yaxis=dict(
                  title='Código CID-10'
              ),
              xaxis=dict(
                  title='Número de Óbitos'
              ),
              height=500,
              showlegend=False,
              margin=dict(l=100, r=50, t=80, b=50)
          )
          
          st.plotly_chart(fig, use_container_width=True)
          
          # Adicionar tabela com os dados detalhados (formatada)
          with st.expander("📊 Ver dados detalhados"):
              df_detalhes = df_mortalidade_diag.sort_values('obitos', ascending=False)
              df_detalhes['taxa_mortalidade'] = df_detalhes['taxa_mortalidade'].map("{:.1f}%".format)
              st.dataframe(df_detalhes[['diagnostico', 'obitos', 'total_internacoes', 'taxa_mortalidade']]
                          .rename(columns={
                              'diagnostico': 'Diagnóstico',
                              'obitos': 'Óbitos',
                              'total_internacoes': 'Total Internações',
                              'taxa_mortalidade': 'Taxa Mortalidade'
                          }))
      else:
          st.warning("Não há registros de óbitos no período selecionado.")
    # --- SEÇÃO 4: FILTROS INTERATIVOS ---
    st.header("🎚️ Filtros Interativos")
    
    # Criar colunas para os filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        anos = sorted(df_sus['ANO_CMPT'].unique())
        ano_selecionado = st.selectbox('Selecione o ano:', ['Todos'] + anos)
    
    with col2:
        meses = sorted(df_sus['MES_CMPT'].unique())
        mes_selecionado = st.selectbox('Selecione o mês:', ['Todos'] + meses, format_func=lambda x: month_names[x] if x != 'Todos' else x)
    
    with col3:
        sexos = ['Todos'] + sorted(df_sus['SEXO'].unique())
        sexo_selecionado = st.selectbox('Selecione o sexo:', sexos, format_func=lambda x: {1: 'Masculino', 2: 'Feminino', 3: 'Indeterminado'}.get(x, 'Todos'))
    
    # Aplicar filtros
    df_filtrado = df_sus.copy()
    
    if ano_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ANO_CMPT'] == ano_selecionado]
    
    if mes_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['MES_CMPT'] == mes_selecionado]
    
    if sexo_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['SEXO'] == sexo_selecionado]
    
    # Exibir estatísticas filtradas
    st.subheader("Estatísticas Filtradas")
    
    # Criar colunas para os KPIs filtrados
    col1, col2, col3, col4 = st.columns(4)
    
    total_filtrado = df_filtrado.shape[0]
    media_idade_filtrado = df_filtrado['IDADE'].mean()
    taxa_mortalidade_filtrado = df_filtrado['MORTE'].mean() * 100 if total_filtrado > 0 else 0
    media_permanencia_filtrado = df_filtrado['DIAS_PERM'].mean()
    
    col1.metric("Total de Internações", f"{total_filtrado:,}".replace(",", "."), delta=f"{total_filtrado - total_internacoes:,}" if total_filtrado != total_internacoes else None)
    col2.metric("Média de Idade", f"{media_idade_filtrado:.1f} anos", delta=f"{media_idade_filtrado - media_idade:.1f}" if total_filtrado != total_internacoes else None)
    col3.metric("Taxa de Mortalidade", f"{taxa_mortalidade_filtrado:.2f}%", delta=f"{taxa_mortalidade_filtrado - taxa_mortalidade:.2f}%" if total_filtrado != total_internacoes else None)
    col4.metric("Média de Permanência", f"{media_permanencia_filtrado:.1f} dias", delta=f"{media_permanencia_filtrado - media_permanencia:.1f}" if total_filtrado != total_internacoes else None)
    
    # Exibir dataframe filtrado
    with st.expander("🔎 Visualizar Dados Filtrados"):
        st.dataframe(df_filtrado.head(100))
    
    # --- SEÇÃO 5: DOWNLOAD DOS DADOS ---
    st.header("📥 Download dos Dados")
    
    # Opções de download
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Baixar Dados Completos (CSV)",
            data=df_sus.to_csv(index=False).encode('utf-8'),
            file_name='internacoes_respiratorias_rj_completo.csv',
            mime='text/csv'
        )
    
    with col2:
        st.download_button(
            label="Baixar Dados Filtrados (CSV)",
            data=df_filtrado.to_csv(index=False).encode('utf-8'),
            file_name='internacoes_respiratorias_rj_filtrado.csv',
            mime='text/csv'
        )