import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def show(df_sensor, POLUENTES_TRADUCAO, month_names):
    """Mostra análises agregadas para toda a cidade (média das estações)"""
    
    st.title("🌆 Análise Avançada da Qualidade do Ar - Rio de Janeiro")
    
    # ---- FILTROS ----
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Seleção de poluentes
            selected_poluentes = st.multiselect(
                'Selecione os poluentes:', 
                options=list(POLUENTES_TRADUCAO.keys()),
                format_func=lambda x: POLUENTES_TRADUCAO[x],
                default=['temp', 'pm2_5'],
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
        
        # Novo filtro para seleção de data específica
        st.markdown("---")
        col4, col5 = st.columns(2)
        
        with col4:
            # Converter para datetime para usar no date_input
            df_sensor['data_formatada'] = pd.to_datetime(df_sensor['data_formatada'])
            min_date = df_sensor['data_formatada'].min()
            max_date = df_sensor['data_formatada'].max()
            
            selected_date = st.date_input(
                "Selecione uma data específica (opcional):",
                min_value=min_date,
                max_value=max_date,
                value=None,
                key='specific_date_input'
            )
    
    # Verificação de seleções mínimas
    if not selected_poluentes or (not selected_years and 'Todos' not in selected_years):
        st.warning("Por favor, selecione pelo menos um poluente e um ano.")
        return
    
    # ---- PRÉ-PROCESSAMENTO ----
    # Filtra por anos selecionados (se não for "Todos")
    if selected_years:
        df_filtered = df_sensor[df_sensor['ano'].isin(selected_years)].copy()
    else:
        df_filtered = df_sensor.copy()
    
    # Filtra por meses se algum foi selecionado e não for "Todos"
    if selected_months:
        df_filtered = df_filtered[df_filtered['mes'].isin(selected_months)]
    
    # Verifica se há uma data específica selecionada
    if selected_date:
        # Converte para datetime64[ns] para compatibilidade
        selected_date = pd.to_datetime(selected_date)
        df_specific_day = df_filtered[df_filtered['data_formatada'] == selected_date]
        
        if not df_specific_day.empty:
            st.success(f"Mostrando dados para {selected_date.strftime('%d/%m/%Y')}")
            
            # ---- VISUALIZAÇÃO DOS DADOS DO DIA ESPECÍFICO ----
            st.subheader(f"📊 Análise Detalhada para {selected_date.strftime('%d/%m/%Y')}")
            
            # Selecionar estação para análise
            stations = df_specific_day['nome_estacao'].unique()
            selected_station = st.selectbox(
                'Selecione uma estação para análise detalhada:',
                options=stations,
                key='station_select_specific_day'
            )
            
            # Filtrar dados para a estação selecionada
            df_station_day = df_specific_day[df_specific_day['nome_estacao'] == selected_station]
            
            # Criar abas para diferentes visualizações
            tab_day1, tab_day2 = st.tabs(["📋 Valores Medidos", "📈 Estatísticas"])
            
            with tab_day1:
                # Tabela com todos os valores medidos
                st.dataframe(
                    df_station_day[['nome_estacao'] + selected_poluentes].set_index('nome_estacao'),
                    use_container_width=True
                )
            
            with tab_day2:
                # Estatísticas descritivas para o dia selecionado
                st.subheader("Estatísticas do Dia")
                
                # Calcular estatísticas para cada poluente
                stats_list = []
                for poluente in selected_poluentes:
                    stats = df_station_day[poluente].describe().to_dict()
                    stats['Poluente'] = POLUENTES_TRADUCAO[poluente]
                    stats_list.append(stats)
                
                # Criar DataFrame de estatísticas
                df_stats = pd.DataFrame(stats_list)
                df_stats = df_stats[['Poluente', 'count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
                df_stats.columns = ['Poluente', 'Contagem', 'Média', 'Desvio Padrão', 'Mínimo', '25%', 'Mediana', '75%', 'Máximo']
                
                # Mostrar tabela de estatísticas
                st.dataframe(
                    df_stats.style.format({
                        'Média': '{:.2f}',
                        'Desvio Padrão': '{:.2f}',
                        'Mínimo': '{:.2f}',
                        '25%': '{:.2f}',
                        'Mediana': '{:.2f}',
                        '75%': '{:.2f}',
                        'Máximo': '{:.2f}'
                    }),
                    use_container_width=True
                )
                
                # Gráfico de boxplot para mostrar a distribuição
                fig = px.box(
                    df_station_day.melt(id_vars=['nome_estacao'], value_vars=selected_poluentes, 
                                      var_name='Poluente', value_name='Valor'),
                    x='Poluente',
                    y='Valor',
                    color='Poluente',
                    labels={'Poluente': '', 'Valor': 'Concentração'},
                    title='Distribuição das medições'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Não continuar com as outras análises se uma data específica foi selecionada
            return
        else:
            st.warning("Nenhum dado encontrado para a data selecionada. Mostrando análise agregada.")
            
    # Verifica e converte variáveis meteorológicas para numérico
    for var in ['temp', 'chuva', 'ur'] + selected_poluentes:
        if var in df_filtered.columns:
            df_filtered[var] = pd.to_numeric(df_filtered[var], errors='coerce')
    
    # ---- VISUALIZAÇÕES ----
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa de Distribuição", "📈 Série Temporal", "🏭 Comparação entre Estações", "🔗 Correlações"])
    
    with tab1:
        st.subheader("Distribuição Espacial dos Poluentes")
        
        # Selecionar um poluente para o mapa
        poluente_mapa = st.selectbox(
            'Selecione um poluente para visualizar no mapa:',
            options=selected_poluentes,
            format_func=lambda x: POLUENTES_TRADUCAO[x],
            key='poluente_mapa_select'
        )
        
        # Agrupar por estação para o mapa
        df_map = df_filtered.groupby(['nome_estacao', 'latitude', 'longitude'])[poluente_mapa].mean().reset_index()
        
        sizes = np.sqrt(df_map[poluente_mapa])
        sizes = sizes.replace([np.inf, -np.inf], np.nan).fillna(1)
        sizes[sizes < 1] = 1  # tamanho mínimo
        
        # Criar o mapa
        fig = px.scatter_mapbox(df_map, 
                               lat="latitude", 
                               lon="longitude", 
                               color=poluente_mapa,
                               size=sizes,
                               hover_name="nome_estacao",
                               hover_data={poluente_mapa: True, "latitude": False, "longitude": False},
                               color_continuous_scale=px.colors.sequential.Viridis,
                               zoom=10,
                               height=600)
        
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar informações sobre os valores
        st.markdown(f"""
        **Interpretação:**
        - Tamanho dos pontos: intensidade do poluente {POLUENTES_TRADUCAO[poluente_mapa]}
        - Cor: concentração (valores mais escuros indicam maior concentração)
        """)
    
    with tab2:
        st.subheader("Série Temporal dos Poluentes")
        
        # Agrupar por data para a série temporal
        df_ts = df_filtered.groupby(['data_formatada'])[selected_poluentes].mean().reset_index()
        df_ts['data_formatada'] = pd.to_datetime(df_ts['data_formatada'])
        
        # Criar um gráfico para cada poluente
        for poluente in selected_poluentes:
            st.markdown(f"### {POLUENTES_TRADUCAO[poluente]}")
            
            # Criar gráfico de série temporal individual
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_ts['data_formatada'],
                y=df_ts[poluente],
                name=POLUENTES_TRADUCAO[poluente],
                mode='lines+markers',
                line=dict(width=2)
            ))
            
            fig.update_layout(
                xaxis_title='Data',
                yaxis_title='Concentração',
                hovermode='x unified',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar análise de tendência
        st.markdown("""
        **Análise de Tendência:**
        - Cada gráfico mostra a variação temporal de um poluente específico
        - Use para identificar padrões sazonais ou tendências ao longo do tempo
        - Passe o mouse sobre os pontos para ver valores específicos
        """)
    
    with tab3:
        st.subheader("Comparação entre Estações de Monitoramento")
        
        # Selecionar um poluente para comparação
        poluente_comp = st.selectbox(
            'Selecione um poluente para comparar entre estações:',
            options=selected_poluentes,
            format_func=lambda x: POLUENTES_TRADUCAO[x],
            key='poluente_comp_select'
        )
        
        # Agrupar por estação
        df_estacoes = df_filtered.groupby('nome_estacao')[poluente_comp].agg(['mean', 'max', 'min']).reset_index()
        df_estacoes = df_estacoes.sort_values('mean', ascending=False)
        
        # Criar gráfico de barras
        fig = px.bar(df_estacoes, 
                     x='nome_estacao', 
                     y='mean',
                     error_y=df_estacoes['mean']-df_estacoes['min'],
                     error_y_minus=df_estacoes['max']-df_estacoes['mean'],
                     labels={'mean': f'Média {POLUENTES_TRADUCAO[poluente_comp]}', 'nome_estacao': 'Estação'},
                     color='mean',
                     color_continuous_scale=px.colors.sequential.Viridis)
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar tabela com dados detalhados
        st.dataframe(df_estacoes.style.background_gradient(cmap='viridis', subset=['mean']), 
                    use_container_width=True)
    
    with tab4:
        st.subheader("Análise de Correlação entre Variáveis")
        
        # Selecionar variáveis para correlação
        variaveis_corr = ['temp', 'ur', 'chuva'] + selected_poluentes
        # Remover duplicatas mantendo a ordem
        variaveis_corr = list(dict.fromkeys(variaveis_corr))
        df_corr = df_filtered[variaveis_corr].corr()
        
        # Mapear nomes para exibição
        cols_display = [POLUENTES_TRADUCAO.get(col, col) for col in df_corr.columns]
        
        # Criar heatmap de correlação
        fig = px.imshow(df_corr,
                        x=cols_display,
                        y=cols_display,
                        color_continuous_scale='RdBu',
                        zmin=-1,
                        zmax=1,
                        text_auto=True)
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar interpretação
        st.markdown("""
        **Interpretação das Correlações:**
        - Valores próximos a **1**: forte correlação positiva
        - Valores próximos a **-1**: forte correlação negativa
        - Valores próximos a **0**: pouca ou nenhuma correlação
        
        **Exemplos de análise:**
        - Temperatura vs Ozônio: correlação positiva comum em dias quentes
        - Umidade vs Material Particulado: correlação negativa comum
        """)

    # ---- MÉTRICAS GERAIS ----
    st.subheader("📊 Resumo do Período")

    # Determina o texto do período
    if selected_months:
        if len(selected_months) == len(month_names):
            period_text = f"Todos os meses de {', '.join(map(str, selected_years))}"
        else:
            period_text = f"{', '.join([month_names[m] for m in selected_months])} de {', '.join(map(str, selected_years))}"
    else:
        period_text = f"Ano(s) {', '.join(map(str, selected_years))}"

    st.markdown(f"**Período selecionado:** {period_text}")

    # Cria métricas para cada poluente selecionado
    metrics = {}
    for poluente in selected_poluentes:
        if poluente in ['temp', 'ur']:
            # Para temperatura e umidade, mostra média com unidade
            metrics[POLUENTES_TRADUCAO[poluente]] = f"{df_filtered[poluente].mean():.1f} {'°C' if poluente == 'temp' else '%'}"
        elif poluente == 'chuva':
            # Para chuva, mostra acumulado
            metrics[POLUENTES_TRADUCAO[poluente]] = f"{df_filtered[poluente].sum():.1f} mm"
        else:
            # Para poluentes, mostra média com unidade
            metrics[POLUENTES_TRADUCAO[poluente]] = f"{df_filtered[poluente].mean():.1f} {POLUENTES_TRADUCAO[poluente].split('(')[-1].split(')')[0]}"

    # Adiciona métrica de dias analisados
    metrics['Dias Analisados'] = len(df_filtered['data_formatada'].unique())

    # Organiza em colunas (4 métricas por linha)
    num_metrics = len(metrics)
    num_rows = (num_metrics + 3) // 4  # Arredonda para cima

    for i in range(num_rows):
        cols = st.columns(4)
        current_metrics = list(metrics.items())[i*4 : (i+1)*4]
        
        for (name, value), col in zip(current_metrics, cols):
            if name == 'Dias Analisados':
                col.metric(name, value)
            else:
                # Extrai o valor numérico para o delta (opcional)
                try:
                    num_value = float(value.split()[0])
                    col.metric(name, value, delta=f"{num_value:.1f}")
                except:
                    col.metric(name, value)