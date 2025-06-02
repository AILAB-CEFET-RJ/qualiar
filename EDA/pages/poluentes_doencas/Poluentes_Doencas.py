import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def show(df_sensor_boxcox, df_sus_aggregated):
    st.title("📈 Relação entre Poluentes e Doenças Respiratórias")
  
    df_merged = pd.merge(df_sensor_boxcox, df_sus_aggregated, on=['ano', 'mes'], how='inner')
    
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
        'temp': 'Temperatura',
        'ur': 'Umidade',
        'num_internacoes': 'Internações'
    }

    # Aplica os nomes amigáveis
    correlation_matrix = correlation_matrix.rename(columns=nome_colunas, index=nome_colunas)

    # Criação do heatmap interativo com Plotly
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        colorscale='RdBu_r',  # Escala divergente vermelho-azul (invertida)
        zmin=-1,
        zmax=1,
        hoverongaps=False,
        text=correlation_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size":16},
        colorbar=dict(
            title='Correlação',
            thickness=15,
            len=0.75
        )
    ))

    # Configurações do layout
    fig.update_layout(
        title='<b>Matriz de Correlação: Poluentes vs Internações</b>',
        title_x=0.40,  # Centraliza o título
        title_y=0.95, # Ajusta a posição vertical do título (mais acima)
        title_font_size=18,
        width=700,
        height=600,
        xaxis=dict(
            tickangle=45,
            color='black',
            tickfont=dict(size=12),
            side='top'
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            autorange='reversed'  # Inverte o eixo Y para ficar igual ao Seaborn
        ),
        margin=dict(l=100, r=50, t=120, b=100),  # Aumenta o topo para dar espaço ao título
        paper_bgcolor="#b0b0b0"
    )

    # Destacar valores importantes (|correlação| >= 0.45)
    for i, row in enumerate(correlation_matrix.values):
        for j, value in enumerate(row):
            if abs(value) >= 0.45:
                fig.add_annotation(
                    font=dict(size=16, color='black', weight='bold'),
                )

    # Adicionar bordas às células
    fig.update_traces(
        xgap=1,
        ygap=1,
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Correlação: %{z:.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legenda explicativa
    st.markdown("""
    <style>
        .legenda-box {
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            border-left: 4px solid #6c757d;
        }
        .zoom-info {
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 10px;
        }
    </style>
    <div class="legenda-box">
        <strong>Interpretação:</strong><br>
        • Correlação positiva (valores próximos de +1): ambas as variáveis aumentam juntas<br>
        • Correlação negativa (valores próximos de -1): uma variável aumenta enquanto a outra diminui<br>
        • Valores em <strong>negrito</strong> indicam correlações moderadas/fortes (|r| ≥ 0.45)
    </div>
    <div class="zoom-info">
        <i class="fas fa-mouse-pointer"></i> Dica: Use o zoom (scroll do mouse) e arraste para navegar na matriz
    </div>
    """, unsafe_allow_html=True)
    
    # --- NOVA SEÇÃO: Análise Individual por Poluente ---
    st.header("🔍 Análise Individual por Poluente")

    # Dicionário de poluentes básicos disponíveis
    poluentes_basicos = {
        'pm2_5': 'PM2.5', 
        'pm10': 'PM10',
        'co': 'CO',
        'no': 'NO',
        'no2': 'NO₂',
        'nox': 'NOx',
        'so2': 'SO₂',
        'o3': 'Ozônio',
        'chuva': 'Chuva',
        'temp': 'Temperatura',
        'ur': 'Umidade Relativa'
    }

    # Widget de seleção individual
    poluente_selecionado = st.selectbox(
        'Selecione um poluente para análise detalhada:',
        options=list(poluentes_basicos.keys()),
        format_func=lambda x: poluentes_basicos[x],
        index=1
    )

    # Verificação para PM2.5
    if poluente_selecionado == 'pm2_5' and df_merged['pm2_5'].isnull().any():
        st.warning("⚠️ O poluente PM2.5 contém valores vazios e não pode ser plotado.")
    else:
        # Criação do gráfico de dispersão
        plt.figure(figsize=(12, 7))
        
        # Scatter plot
        plt.scatter(
            x=df_merged[poluente_selecionado],
            y=df_merged['num_internacoes'],
            color='#1f77b4',  # Azul padrão do matplotlib
            s=60,
            alpha=0.7,
            edgecolor='white',
            linewidth=0.8,
            label='Dados Observados'
        )
        
        # Linha de tendência (regressão linear)
        from sklearn.linear_model import LinearRegression
        X = df_merged[[poluente_selecionado]].dropna()
        y = df_merged.loc[X.index, 'num_internacoes']
        
        if not X.empty:
            reg = LinearRegression().fit(X, y)
            y_pred = reg.predict(X)
            
            plt.plot(X, y_pred, 
                    color='#d62728',  # Vermelho padrão
                    linewidth=2.5, 
                    linestyle='--',
                    label=f'Linha de Tendência (R²={reg.score(X,y):.2f})')
            
            # Intervalo de confiança
            sns.regplot(x=X[poluente_selecionado], y=y,
                        scatter=False, ci=95,
                        line_kws={'color':'#d62728', 'alpha':0.2})
            
            # Estatísticas
            correlacao = X[poluente_selecionado].corr(y)
            stats_text = f'''
            Estatísticas:
            Correlação: {correlacao:.2f}
            Equação: y = {reg.coef_[0]:.2f}x + {reg.intercept_:.2f}
            '''
            plt.gcf().text(0.15, 0.82, stats_text,
                        bbox=dict(facecolor='white', alpha=0.8, 
                                    edgecolor='lightgray'),
                        fontsize=10)
        
        # Formatação
        plt.xlabel(f'Concentração de {poluentes_basicos[poluente_selecionado]}', 
                fontsize=12, fontweight='bold')
        plt.ylabel('Número de Internações', fontsize=12, fontweight='bold')
        plt.title(f'Relação entre {poluentes_basicos[poluente_selecionado]} e Internações',
                fontsize=14, pad=15, fontweight='bold')
        
        plt.grid(True, linestyle=':', alpha=0.4)
        plt.legend(loc='upper right', framealpha=1)
        plt.tight_layout()
        
    st.pyplot(plt)
    
    # --- NOVA SEÇÃO: Gráficos Individuais com Plotly ---
    st.header("📊 Análise Temporal por Poluente (Interativa)")

    # Dicionário de poluentes disponíveis
    poluentes_disponiveis = {
        'pm2_5_scaled': 'PM2.5 (Escalado)',
        'pm10_scaled': 'PM10 (Escalado)',
        'nox_scaled': 'NOx (Escalado)',
        'temp_scaled': 'Temperatura (Escalado)',
        'o3_scaled': 'Ozônio (Escalado)'
    }

    # Widget de seleção
    poluentes_selecionados = st.multiselect(
        'Selecione um ou mais poluentes para análise:',
        options=list(poluentes_disponiveis.keys()),
        format_func=lambda x: poluentes_disponiveis[x],
        default=['pm10_scaled', 'o3_scaled']
    )

    if poluentes_selecionados:
        # Configurações de estilo
        cores_poluentes = {
            'pm2_5_scaled': '#90D1CA',
            'pm10_scaled': '#129990',
            'nox_scaled': '#096B68',
            'temp_scaled': '#604652',
            'o3_scaled': '#3E3B3C'
        }
        
        marcadores = {
            'pm2_5_scaled': 'circle',
            'pm10_scaled': 'square',
            'nox_scaled': 'diamond',
            'temp_scaled': 'triangle-up',
            'o3_scaled': 'pentagon'
        }
        
        # Criar um gráfico para cada poluente selecionado
        for poluente in poluentes_selecionados:
            nome_amigavel = poluentes_disponiveis[poluente]
            
            # Criar figura com eixo secundário
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Adicionar poluente (eixo primário)
            fig.add_trace(
                go.Scatter(
                    x=df_merged['mes_ano'],
                    y=df_merged[poluente],
                    name=nome_amigavel,
                    line=dict(color=cores_poluentes[poluente], width=2),
                    marker=dict(
                        symbol=marcadores[poluente],
                        size=8
                    ),
                    mode='lines+markers',
                    hovertemplate=f"{nome_amigavel}: %{{y:.2f}}<extra></extra>"
                ),
                secondary_y=False
            )
            
            # Adicionar linha de média do poluente
            media_poluente = df_merged[poluente].mean()
            fig.add_hline(
                y=media_poluente,
                line_dash="dot",
                line_color=cores_poluentes[poluente],
                opacity=0.4,
                annotation_text=f"Média {nome_amigavel.split(' ')[0]}: {media_poluente:.2f}",
                annotation_position="bottom right"
            )
            
            # Adicionar internações (eixo secundário)
            fig.add_trace(
                go.Scatter(
                    x=df_merged['mes_ano'],
                    y=df_merged['num_internacoes'],
                    name='Internações Respiratórias',
                    line=dict(color='#FF0000', width=3),
                    marker=dict(
                        symbol='star',
                        size=10
                    ),
                    mode='lines+markers',
                    hovertemplate="Internações: %{y}<extra></extra>"
                ),
                secondary_y=True
            )
            
            # Configurações do layout
            fig.update_layout(
                title=f'Relação entre {nome_amigavel} e Internações Respiratórias',
                xaxis_title='Mês/Ano',
                yaxis_title=f'Concentração ({nome_amigavel})',
                yaxis2_title='Número de Internações',
                hovermode="x unified",
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            # Configurações dos eixos
            fig.update_yaxes(
                title_text=f'Concentração ({nome_amigavel})',
                secondary_y=False,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=0.5
            )
            
            fig.update_yaxes(
                title_text='Número de Internações',
                secondary_y=True,
                showgrid=False
            )
            
            # Adicionar zoom e scroll
            fig.update_xaxes(
                rangeslider_visible=True,
                tickangle=45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Adicionar espaço entre gráficos
            st.markdown("---")
        
        # Explicação dos símbolos
        st.markdown("""
        <div class="legenda-box">
            <strong>Legenda dos Marcadores:</strong><br>
            • <i class="fas fa-circle" style="color:#90D1CA"></i> PM2.5<br>
            • <i class="fas fa-square" style="color:#129990"></i> PM10<br>
            • <i class="fas fa-gem" style="color:#096B68"></i> NOx<br>
            • <i class="fas fa-caret-up" style="color:#604652"></i> Temperatura<br>
            • <i class="fas fa-star" style="color:#3E3B3C"></i> Ozônio<br>
            • <i class="fas fa-star" style="color:#FF0000"></i> Internações
        </div>
        """, unsafe_allow_html=True)
      
        # # --- NOVA SEÇÃO: Gráfico Consolidado ---
        # st.header("📊 Visão Consolidada dos Poluentes Selecionados")
        
        # # Configurações do gráfico consolidado
        # # Filtro por período
        # anos = sorted(df_merged['ano'].unique())
        # periodo = st.select_slider(
        #     "Selecione o período:",
        #     options=anos,
        #     value=(min(anos), max(anos)))

        # # Filtrar dados
        # df_filtrado = df_merged[df_merged['ano'].between(periodo[0], periodo[1])]
        
        
        # plt.figure(figsize=(20, 6))
        # ax1 = plt.gca()
        
        # # Mapeamento de cores e estilos para o gráfico consolidado
        # cores_consolidado = {
        #     'pm2_5_scaled': '#90D1CA',
        #     'pm10_scaled': '#27548A',
        #     'nox_scaled': '#FEBA17',
        #     'temp_scaled': '#604652',
        #     'o3_scaled': '#3E3B3C'
        # }
        
        # estilos_consolidado = ['-', '--', ':', '-.', '--']
        # marcadores_consolidado = ['o', 's', 'D', '^', 'p']
        
        # # Plotar cada poluente selecionado
        # for i, poluente in enumerate(poluentes_selecionados):
        #     ax1.plot(df_filtrado['mes_ano'], df_filtrado[poluente],
        #                 label=poluentes_disponiveis[poluente],
        #                 color=cores_consolidado[poluente],
        #                 linestyle=estilos_consolidado[i % len(estilos_consolidado)],
        #                 marker=marcadores_consolidado[i % len(marcadores_consolidado)],
        #                 linewidth=2.5,
        #                 markersize=8,
        #                 alpha=0.9)
        
        # # Configurar eixos (igual ao código original)
        # ax1.set_ylabel('Concentração de Poluentes (Scaled)', fontsize=13, fontweight='bold', color='#2E8B57')
        # ax1.tick_params(axis='y', colors='#2E8B57', labelsize=11)
        # ax1.grid(True, linestyle=':', alpha=0.4)
        
        # ax2 = ax1.twinx()
        # ax2.plot(df_filtrado['mes_ano'], df_filtrado['num_internacoes'],
        #             label='Internações Respiratórias',
        #             color='#FF0000',
        #             linestyle='-',
        #             marker='*',
        #             linewidth=3,
        #             markersize=10,
        #             alpha=1)
        
        # ax2.set_ylabel('Número de Internações', color='#FF0000', fontsize=13, fontweight='bold')
        # ax2.tick_params(axis='y', labelcolor='#FF0000', labelsize=11)
        
        # # Melhorias no eixo X
        # plt.xticks(rotation=45, ha='right', fontsize=11)
        # ax1.xaxis.set_major_locator(plt.MaxNLocator(15))
        
        # # Linhas de média
        # for poluente in poluentes_selecionados:
        #     ax1.axhline(y=df_filtrado[poluente].mean(), 
        #                 color=cores_consolidado[poluente], 
        #                 linestyle='--', 
        #                 alpha=0.4,
        #                 linewidth=1.5)
        
        # # Título e legenda
        # plt.title('Relação entre Poluentes Atmosféricos e Internações Respiratórias\n', 
        #             fontsize=16, fontweight='bold', pad=20)
        
        # lines1, labels1 = ax1.get_legend_handles_labels()
        # lines2, labels2 = ax2.get_legend_handles_labels()
        # ax1.legend(lines1 + lines2, labels1 + labels2,
        #             loc='upper center',
        #             bbox_to_anchor=(0.5, -0.15),
        #             ncol=3,
        #             fontsize=12,
        #             framealpha=1)
        
        # plt.tight_layout()
        # plt.subplots_adjust(bottom=0.2)
        # st.pyplot(plt)
        
        # # Adicionando explicação
        # st.markdown("""
        # <div class="legenda-box">
        #     <strong>Interpretação dos Gráficos:</strong><br>
        #     • <span style="color:#FF0000">Linha vermelha</span> mostra o número de internações respiratórias<br>
        #     • Linhas coloridas mostram a concentração dos poluentes selecionados<br>
        #     • Linhas tracejadas mostram a média histórica de cada poluente
        # </div>
        # """, unsafe_allow_html=True)
        
        # --- NOVA SEÇÃO: Gráfico Consolidado Interativo ---
        st.header("📊 Visão Consolidada Interativa")

        # Criar figura com eixo secundário
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Adicionar cada poluente
        cores_plotly = {
                'pm2_5_scaled': '#90D1CA',
                'pm10_scaled': '#27548A',
                'nox_scaled': '#FEBA17',
                'temp_scaled': '#604652',
                'o3_scaled': '#3E3B3C'
        }

        for poluente in poluentes_selecionados:
                fig.add_trace(
                        go.Scatter(
                                x=df_merged['mes_ano'],
                                y=df_merged[poluente],
                                name=poluentes_disponiveis[poluente],
                                line=dict(color=cores_plotly[poluente], width=2),
                                mode='lines+markers',
                                marker=dict(size=6)
                        ),
                        secondary_y=False
                )
                
                # Linha de média
                fig.add_hline(
                        y=df_merged[poluente].mean(),
                        line_dash="dot",
                        line_color=cores_plotly[poluente],
                        opacity=0.5,
                        annotation_text=f"Média {poluentes_disponiveis[poluente]}",
                        annotation_position="bottom right"
                )

        # Adicionar internações (eixo secundário)
        fig.add_trace(
                go.Scatter(
                        x=df_merged['mes_ano'],
                        y=df_merged['num_internacoes'],
                        name='Internações',
                        line=dict(color='#FF0000', width=3),
                        mode='lines+markers',
                        marker=dict(size=8, symbol='star')
                ),
                secondary_y=True
        )

        # Layout do gráfico
        fig.update_layout(
                title='Relação entre Poluentes e Internações Respiratórias',
                xaxis_title='Mês/Ano',
                yaxis_title='Concentração de Poluentes',
                yaxis2_title='Número de Internações',
                hovermode="x unified",
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=100, r=100, t=100, b=200)  # Espaço para legendas
        )

        # Adicionar zoom e scroll nativo
        fig.update_xaxes(rangeslider_visible=True)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Selecione pelo menos um poluente para visualizar os gráficos.")

        
    
    st.write("Gráficos de correlação e análises estatísticas...")