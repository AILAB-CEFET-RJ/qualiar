import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pages.sensores.Geral as geral
import pages.sensores.Estacoes as estacoes_page

def aggregate_general_data(df, poluentes):
    """Agrega dados de todas as estações para a opção 'Geral'"""
    # Calcula a média por data para todos os poluentes
    df_agg = df.groupby(['data_formatada', 'ano', 'mes'])[poluentes].mean().reset_index()
    df_agg['nome_estacao'] = 'GERAL (Média RJ)'
    return df_agg

def show(df_sensor, POLUENTES_TRADUCAO, month_names):
    st.title("🏭 Análise Comparativa de Sensores Ambientais")
    df_sensor['ano'] = df_sensor['ano'].astype(int)
    
    # Adicionando informações sobre o dataset
    with st.expander("ℹ️ Sobre os dados"):
        st.markdown("""
        Este dataset contém informações de qualidade do ar coletadas por estações de monitoramento na cidade do Rio de Janeiro.
        Cada registro representa uma medição. As medições são feitas a cada hora e com as seguintes informações:

        ### 📍 Informações da Estação
        - **nome_estacao**: Nome da estação de monitoramento
        - **latitude/longitude**: Coordenadas geográficas da estação
        - **data**: Data e hora da medição
        - **ano/mes**: Ano e mês da medição

        ### 🌡️ Variáveis Meteorológicas
        - **temp**: Temperatura em graus Celsius
        - **ur**: Umidade relativa do ar (%)
        - **chuva**: Precipitação em milímetros

        ### 🏭 Poluentes Atmosféricos
        - **co**: Monóxido de carbono (ppm)
        - **no**: Óxido nítrico (µg/m³)
        - **no2**: Dióxido de nitrogênio (µg/m³)
        - **so2**: Dióxido de enxofre (µg/m³)
        - **o3**: Ozônio (µg/m³)
        - **pm10**: Material particulado ≤10µm (µg/m³)
        - **pm2_5**: Material particulado ≤2.5µm (µg/m³)

        ### Estações Disponíveis:
        - ESTAÇÃO BANGU
        - ESTAÇÃO CAMPO GRANDE
        - ESTAÇÃO CENTRO
        - ESTAÇÃO COPACABANA
        - ESTAÇÃO IRAJÁ
        - ESTAÇÃO PEDRA DE GUARATIBA
        - ESTAÇÃO SÃO CRISTÓVÃO
        - ESTAÇÃO TIJUCA
        """)
        
    # Sidebar com controles
    with st.sidebar:
        st.header("⚙️ Configurações de Filtro")
        
        # Seleção de estações (incluindo opção 'Geral')
        estacoes = sorted(df_sensor['nome_estacao'].unique())
        selected_estacoes = st.multiselect(
            'Selecione as estações para comparação:', 
            ['GERAL (Média RJ)'] + estacoes,
            default=['GERAL (Média RJ)'],
            key='estacao_select'
        )
        
    if 'GERAL (Média RJ)' in selected_estacoes:
        st.warning("A opção 'GERAL (Média RJ)' agregará os dados de todas as estações.")
        geral.show(df_sensor, POLUENTES_TRADUCAO, month_names)
    elif 'GERAL (Média RJ)' not in selected_estacoes:
        st.error("Comparação entre estações não foi implementada ainda. Apenas a opção 'GERAL (Média RJ)' está disponível no momento.")
        # estacoes_page.show(df_sensor, POLUENTES_TRADUCAO, month_names, selected_estacoes)
        pass
    #     else:
    #         st.info("Selecione 'GERAL (Média RJ)' para ver a média de todas as estações.")
    #     # Seleção de poluentes
    #     selected_poluentes = st.multiselect(
    #         'Selecione os poluentes:', 
    #         options=list(POLUENTES_TRADUCAO.keys()),
    #         format_func=lambda x: POLUENTES_TRADUCAO[x],
    #         default=['pm10', 'o3'],
    #         key='poluentes_multiselect'
    #     )
        
    #     # Seleção de anos
    #     available_years = sorted(df_sensor['ano'].unique())
    #     selected_years = st.multiselect(
    #         'Selecione os anos:', 
    #         available_years,
    #         default=[available_years[-1]],
    #         key='years_multiselect'
    #     )
        
    #     # Seleção de meses
    #     selected_months = st.multiselect(
    #         'Selecione os meses:', 
    #         options=month_names.keys(),
    #         format_func=lambda x: month_names[x],
    #         default=list(month_names.keys())[:3],
    #         key='months_multiselect'
    #     )
        
    #     # Opções de visualização
    #     st.header("📊 Opções de Visualização")
    #     show_daily = st.checkbox("Mostrar dados diários", value=True)
    #     show_stats = st.checkbox("Mostrar análise estatística", value=True)
    #     show_comparison = st.checkbox("Mostrar comparação entre estações", value=True)
    #     show_map = st.checkbox("Mostrar mapa de calor por região", value=True)
    
    # # Verificação de seleções
    # if not selected_estacoes or not selected_poluentes or not selected_years or not selected_months:
    #     st.warning("Por favor, selecione pelo menos uma estação, um poluente, um ano e um mês.")
    #     return
    
    # # Filtragem dos dados básica
    # df_filtered = df_sensor[
    #     (df_sensor['ano'].isin(selected_years)) &
    #     (df_sensor['mes'].isin(selected_months))
    # ].sort_values(['nome_estacao', 'data_formatada'])
    
    # # Processa a opção GERAL se selecionada
    # if 'GERAL (Média RJ)' in selected_estacoes:
    #     df_general = aggregate_general_data(df_filtered, selected_poluentes)
        
    #     # Remove GERAL da lista para filtrar estações específicas
    #     stations_to_show = [est for est in selected_estacoes if est != 'GERAL (Média RJ)']
        
    #     if stations_to_show:
    #         df_filtered = df_filtered[df_filtered['nome_estacao'].isin(stations_to_show)]
    #         df_filtered = pd.concat([df_filtered, df_general])
    #     else:
    #         df_filtered = df_general
    # else:
    #     df_filtered = df_filtered[df_filtered['nome_estacao'].isin(selected_estacoes)]
    
    # if df_filtered.empty:
    #     st.error("Nenhum dado encontrado com os filtros selecionados.")
    #     return
    
    # # Container principal
    # main_container = st.container()
    
    # with main_container:
    #     # ---- SEÇÃO 0: VISÃO GERAL DA CIDADE ----
    #     if 'GERAL (Média RJ)' in selected_estacoes:
    #         st.subheader("🌆 Visão Geral da Cidade do Rio de Janeiro")
            
    #         # Cartões com métricas resumidas
    #         col1, col2, col3 = st.columns(3)
            
    #         with col1:
    #             st.metric("Período Analisado", 
    #                     f"{month_names[selected_months[0]]} a {month_names[selected_months[-1]]} de {selected_years[0]}")
            
    #         with col2:
    #             avg_temp = df_general['temp'].mean()
    #             st.metric("Temperatura Média", 
    #                       f"{avg_temp:.1f} °C", 
    #                       help="Temperatura média no período selecionado")
            
    #         with col3:
    #             avg_pm10 = df_general['pm10'].mean()
    #             st.metric("PM10 Médio", 
    #                       f"{avg_pm10:.1f} µg/m³", 
    #                       help="Material particulado médio no período")
            
    #         # Gráfico de radar para comparação de poluentes
    #         if len(selected_poluentes) > 1:
    #             st.markdown("### 📊 Comparação Relativa dos Poluentes")
                
    #             # Calcula médias normalizadas para o radar
    #             poluentes_radar = [p for p in selected_poluentes if p not in ['temp', 'chuva', 'ur']]
                
    #             if poluentes_radar:
    #                 avg_values = df_general[poluentes_radar].mean()
    #                 max_values = df_sensor[poluentes_radar].max()
    #                 normalized = (avg_values / max_values * 100).values.tolist()
                    
    #                 fig = go.Figure()
                    
    #                 fig.add_trace(go.Scatterpolar(
    #                     r=normalized + [normalized[0]],  # Fechar o radar
    #                     theta=[POLUENTES_TRADUCAO[p] for p in poluentes_radar] + [POLUENTES_TRADUCAO[poluentes_radar[0]]],
    #                     fill='toself',
    #                     name='Média RJ',
    #                     line=dict(color='royalblue')
    #                 ))
                    
    #                 fig.update_layout(
    #                     polar=dict(
    #                         radialaxis=dict(
    #                             visible=True,
    #                             range=[0, 100]
    #                         )),
    #                     showlegend=True,
    #                     title="Comparação Relativa dos Níveis de Poluentes<br>(Percentual do Máximo Histórico)",
    #                     height=500
    #                 )
                    
    #                 st.plotly_chart(fig, use_container_width=True)
            
    #         st.markdown("---")
        
    #     # ---- SEÇÃO 1: GRÁFICOS DIÁRIOS POR ESTAÇÃO ----
    #     if show_daily:
    #         st.subheader("📈 Variação Diária dos Poluentes")
            
    #         for poluente in selected_poluentes:
    #             # Cria um gráfico para cada poluente
    #             fig = go.Figure()
                
    #             # Define estilo especial para GERAL
    #             line_styles = {
    #                 'GERAL (Média RJ)': dict(width=4, color='black', dash='solid'),
    #                 'default': dict(width=2, color=None, dash='solid')
    #             }
                
    #             # Adiciona uma linha para cada estação
    #             for estacao in df_filtered['nome_estacao'].unique():
    #                 estacao_df = df_filtered[df_filtered['nome_estacao'] == estacao]
                    
    #                 if not estacao_df.empty:
    #                     style = line_styles['default'] if estacao != 'GERAL (Média RJ)' else line_styles['GERAL (Média RJ)']
                        
    #                     fig.add_trace(go.Scatter(
    #                         x=estacao_df['data_formatada'],
    #                         y=estacao_df[poluente],
    #                         name=estacao,
    #                         mode='lines+markers',
    #                         marker=dict(
    #                             size=8 if estacao == 'GERAL (Média RJ)' else 6,
    #                             symbol='star' if estacao == 'GERAL (Média RJ)' else 'circle'
    #                         ),
    #                         line=style,
    #                         hovertemplate=f"{estacao}<br>Data: %{{x}}<br>{POLUENTES_TRADUCAO[poluente]}: %{{y}}<extra></extra>"
    #                     ))
                
    #             # Configurações do layout
    #             fig.update_layout(
    #                 title=f"{POLUENTES_TRADUCAO[poluente]} - Comparação entre Estações",
    #                 xaxis_title="Data",
    #                 yaxis_title=POLUENTES_TRADUCAO[poluente],
    #                 hovermode="x unified",
    #                 height=500,
    #                 legend=dict(
    #                     orientation="h",
    #                     yanchor="bottom",
    #                     y=1.02,
    #                     xanchor="right",
    #                     x=1
    #                 ),
    #                 margin=dict(l=50, r=50, t=80, b=50)
    #             )
                
    #             # Adiciona linha de média geral se GERAL não estiver selecionado
    #             if 'GERAL (Média RJ)' not in selected_estacoes and len(selected_estacoes) > 1:
    #                 df_general_period = aggregate_general_data(
    #                     df_sensor[
    #                         (df_sensor['ano'].isin(selected_years)) &
    #                         (df_sensor['mes'].isin(selected_months))
    #                     ], 
    #                     [poluente]
    #                 )
                    
    #                 fig.add_trace(go.Scatter(
    #                     x=df_general_period['data_formatada'],
    #                     y=df_general_period[poluente],
    #                     name='Média RJ (referência)',
    #                     mode='lines',
    #                     line=dict(width=2, color='gray', dash='dot'),
    #                     opacity=0.6,
    #                     hovertemplate=f"Média RJ<br>Data: %{{x}}<br>{POLUENTES_TRADUCAO[poluente]}: %{{y}}<extra></extra>"
    #                 ))
                
    #             # Adiciona slider de zoom
    #             fig.update_xaxes(rangeslider_visible=True)
                
    #             st.plotly_chart(fig, use_container_width=True)
                
    #             # Adiciona espaço entre gráficos
    #             st.markdown("---")
        
    #     # ---- SEÇÃO 2: ANÁLISE ESTATÍSTICA ----
    #     if show_stats:
    #         st.subheader("📊 Análise Estatística Comparativa")
            
    #         for poluente in selected_poluentes:
    #             # Cria um DataFrame com estatísticas por estação
    #             stats_data = []
                
    #             for estacao in df_filtered['nome_estacao'].unique():
    #                 estacao_df = df_filtered[df_filtered['nome_estacao'] == estacao]
    #                 if not estacao_df.empty:
    #                     poluente_data = estacao_df[poluente].dropna()
    #                     if not poluente_data.empty:
    #                         stats_data.append({
    #                             'Estação': estacao,
    #                             'Média': poluente_data.mean(),
    #                             'Mediana': poluente_data.median(),
    #                             'Desvio Padrão': poluente_data.std(),
    #                             'Mínimo': poluente_data.min(),
    #                             'Máximo': poluente_data.max(),
    #                             'Q1': poluente_data.quantile(0.25),
    #                             'Q3': poluente_data.quantile(0.75),
    #                             'Nº Amostras': len(poluente_data),
    #                             'Acima da Média RJ': f"{(poluente_data > df_sensor[poluente].mean()).mean()*100:.1f}%"
    #                         })
                
    #             if stats_data:
    #                 stats_df = pd.DataFrame(stats_data)
                    
    #                 # Exibe tabela de estatísticas
    #                 with st.expander(f"Estatísticas para {POLUENTES_TRADUCAO[poluente]}", expanded=False):
    #                     st.dataframe(
    #                         stats_df.style.format({
    #                             'Média': '{:.2f}',
    #                             'Mediana': '{:.2f}',
    #                             'Desvio Padrão': '{:.2f}',
    #                             'Mínimo': '{:.2f}',
    #                             'Máximo': '{:.2f}',
    #                             'Q1': '{:.2f}',
    #                             'Q3': '{:.2f}'
    #                         }).background_gradient(subset=['Média', 'Acima da Média RJ'], cmap='YlOrRd'),
    #                         use_container_width=True
    #                     )
                    
    #                 # Gráfico de boxplot comparativo
    #                 fig = go.Figure()
                    
    #                 for estacao in df_filtered['nome_estacao'].unique():
    #                     estacao_df = df_filtered[df_filtered['nome_estacao'] == estacao]
    #                     if not estacao_df.empty:
    #                         fig.add_trace(go.Box(
    #                             y=estacao_df[poluente],
    #                             name=estacao,
    #                             boxpoints='outliers',
    #                             marker_color='#1f77b4' if estacao != 'GERAL (Média RJ)' else '#d62728',
    #                             line_color='#1f77b4' if estacao != 'GERAL (Média RJ)' else '#d62728',
    #                             jitter=0.3,
    #                             pointpos=-1.8
    #                         ))
                    
    #                 # Adiciona linha de referência da média da cidade
    #                 if 'GERAL (Média RJ)' not in df_filtered['nome_estacao'].unique():
    #                     city_avg = df_sensor[
    #                         (df_sensor['ano'].isin(selected_years)) &
    #                         (df_sensor['mes'].isin(selected_months))
    #                     ][poluente].mean()
                        
    #                     fig.add_hline(
    #                         y=city_avg,
    #                         line_dash="dot",
    #                         line_color="gray",
    #                         annotation_text=f"Média RJ: {city_avg:.2f}",
    #                         annotation_position="bottom right"
    #                     )
                    
    #                 fig.update_layout(
    #                     title=f"Distribuição de {POLUENTES_TRADUCAO[poluente]} por Estação",
    #                     yaxis_title=POLUENTES_TRADUCAO[poluente],
    #                     boxmode='group',
    #                     height=500
    #                 )
                    
    #                 st.plotly_chart(fig, use_container_width=True)
                    
    #                 # Teste de hipótese (se mais de uma estação selecionada)
    #                 if len(df_filtered['nome_estacao'].unique()) > 1:
    #                     st.markdown("**Teste de Diferença entre Estações (ANOVA):**")
                        
    #                     # Prepara dados para ANOVA
    #                     groups = []
    #                     for estacao in df_filtered['nome_estacao'].unique():
    #                         estacao_data = df_filtered[df_filtered['nome_estacao'] == estacao][poluente].dropna()
    #                         if len(estacao_data) > 0:
    #                             groups.append(estacao_data)
                        
    #                     if len(groups) >= 2:
    #                         # Teste ANOVA
    #                         f_val, p_val = stats.f_oneway(*groups)
                            
    #                         st.write(f"""
    #                         - Valor F: {f_val:.4f}
    #                         - Valor p: {p_val:.4f}
    #                         - {'Diferença estatisticamente significativa' if p_val < 0.05 else 'Sem diferença significativa'} (α=0.05)
    #                         """)
                    
    #                 st.markdown("---")
        
    #     # ---- SEÇÃO 3: MAPA DE CALOR POR REGIÃO ----
    #     if show_map and len(selected_poluentes) > 0 and len(selected_months) > 0:
    #         st.subheader("🗺️ Mapa de Calor por Região")
            
    #         # Pré-processamento para o mapa
    #         df_map = df_filtered.copy()
            
    #         # Adiciona coordenadas aproximadas por estação (exemplo)
    #         estacao_coords = {
    #             'ESTAÇÃO BANGU': dict(lat=-22.88, lon=-43.47),
    #             'ESTAÇÃO CAMPO GRANDE': dict(lat=-22.90, lon=-43.56),
    #             'ESTAÇÃO CENTRO': dict(lat=-22.91, lon=-43.18),
    #             'ESTAÇÃO COPACABANA': dict(lat=-22.97, lon=-43.19),
    #             'ESTAÇÃO IRAJÁ': dict(lat=-22.82, lon=-43.32),
    #             'ESTAÇÃO PEDRA DE GUARATIBA': dict(lat=-23.02, lon=-43.60),
    #             'ESTAÇÃO SÃO CRISTÓVÃO': dict(lat=-22.90, lon=-43.23),
    #             'ESTAÇÃO TIJUCA': dict(lat=-22.92, lon=-43.24),
    #             'GERAL (Média RJ)': dict(lat=-22.91, lon=-43.17)  # Centro do RJ
    #         }
            
    #         for estacao, coords in estacao_coords.items():
    #             df_map.loc[df_map['nome_estacao'] == estacao, 'lat'] = coords['lat']
    #             df_map.loc[df_map['nome_estacao'] == estacao, 'lon'] = coords['lon']
            
    #         # Widget para selecionar o poluente do mapa
    #         map_poluente = st.selectbox(
    #             "Selecione o poluente para o mapa:",
    #             selected_poluentes,
    #             format_func=lambda x: POLUENTES_TRADUCAO[x]
    #         )
            
    #         # Cria o mapa de calor
    #         fig = go.Figure(go.Densitymapbox(
    #             lat=df_map['lat'],
    #             lon=df_map['lon'],
    #             z=df_map[map_poluente],
    #             radius=20,
    #             colorscale='Jet',
    #             zmin=df_sensor[map_poluente].quantile(0.1),
    #             zmax=df_sensor[map_poluente].quantile(0.9)
    #         ))
            
    #         fig.update_layout(
    #             title=f"Distribuição Espacial de {POLUENTES_TRADUCAO[map_poluente]}",
    #             mapbox_style="stamen-terrain",
    #             mapbox_center_lat=-22.91,
    #             mapbox_center_lon=-43.17,
    #             mapbox_zoom=10,
    #             height=600,
    #             margin=dict(l=0, r=0, t=40, b=0)
    #         )
            
    #         st.plotly_chart(fig, use_container_width=True)
    #         st.markdown("---")
        
    #     # ---- SEÇÃO 4: DADOS BRUTOS ----
    #     with st.expander("📁 Visualizar Dados Brutos", expanded=False):
    #         st.dataframe(
    #             df_filtered[['nome_estacao', 'data_formatada', 'ano', 'mes'] + selected_poluentes].rename(columns=POLUENTES_TRADUCAO),
    #             height=300,
    #             use_container_width=True
    #         )
            
    #         # Opção para download
    #         csv = df_filtered[['nome_estacao', 'data_formatada', 'ano', 'mes'] + selected_poluentes].to_csv(index=False).encode('utf-8')
    #         st.download_button(
    #             label="📥 Baixar dados como CSV",
    #             data=csv,
    #             file_name=f'dados_sensores_{"_".join(selected_estacoes)}.csv',
    #             mime='text/csv'
    #         )