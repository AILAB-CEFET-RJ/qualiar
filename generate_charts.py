# generate_charts.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime
import os
from pathlib import Path

# Configurações
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "public" / "charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Constantes
MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

def load_and_combine_data():
    """Carrega e combina os 3 CSVs"""
    print("Carregando dados SUS...")
    
    files = [
        DATA_DIR / "INTERNACOES_STREAMLIT_parte1.csv",
        DATA_DIR / "INTERNACOES_STREAMLIT_parte2.csv",
        DATA_DIR / "INTERNACOES_STREAMLIT_parte3.csv"
    ]
    
    dfs = []
    for file in files:
        if file.exists():
            print(f"  Carregando {file.name}...")
            df = pd.read_csv(file, low_memory=False, dtype={'ANO': str, 'MES': str})
            dfs.append(df)
        else:
            print(f"  Arquivo não encontrado: {file}")
    
    if not dfs:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado")
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Total de registros carregados: {len(combined):,}")
    
    return combined

def preprocess_data(df):
    """Pré-processa os dados"""
    print("Pré-processando dados...")
    
    # Converte datas
    if 'DT_INTER' in df.columns:
        df['DT_INTER'] = pd.to_datetime(df['DT_INTER'], errors='coerce')
    
    # Converte colunas numéricas
    numeric_cols = ['IDADE', 'DIAS_PERM', 'MORTE', 'ANO', 'MES']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Preenche valores ausentes
    if 'SEXO_TXT' not in df.columns and 'SEXO' in df.columns:
        df['SEXO_TXT'] = df['SEXO'].map({'1': 'Masculino', '2': 'Feminino', '3': 'Não informado'})
    
    # Cria colunas derivadas se necessário
    if 'ANO' not in df.columns and 'DT_INTER' in df.columns:
        df['ANO'] = df['DT_INTER'].dt.year
    
    if 'MES' not in df.columns and 'DT_INTER' in df.columns:
        df['MES'] = df['DT_INTER'].dt.month
    
    return df

def calculate_metrics(df):
    """Calcula métricas básicas"""
    print("Calculando métricas...")
    
    metrics = {
        'total_internacoes': len(df),
        'media_idade': df['IDADE'].mean() if 'IDADE' in df.columns else 0,
        'taxa_mortalidade': (df['MORTE'].mean() * 100) if 'MORTE' in df.columns else 0,
        'media_permanencia': df['DIAS_PERM'].mean() if 'DIAS_PERM' in df.columns else 0,
        'ano_min': int(df['ANO'].min()) if 'ANO' in df.columns and df['ANO'].notna().any() else 0,
        'ano_max': int(df['ANO'].max()) if 'ANO' in df.columns and df['ANO'].notna().any() else 0,
    }
    
    return metrics

def generate_time_series_chart(df, output_path):
    """Gera gráfico de série temporal"""
    print("Gerando série temporal...")
    
    if 'DT_INTER' not in df.columns or df['DT_INTER'].isna().all():
        print("  Sem dados de data para série temporal")
        return None
    
    # Agrupa por dia
    df_daily = df.dropna(subset=['DT_INTER']).copy()
    df_daily = df_daily.set_index('DT_INTER').sort_index()
    ts_daily = df_daily.groupby(pd.Grouper(freq='D')).size()
    
    # Calcula médias móveis
    ts_ma7 = ts_daily.rolling(7, min_periods=1).mean()
    ts_ma30 = ts_daily.rolling(30, min_periods=1).mean()
    
    # Cria gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts_daily.index, 
        y=ts_daily.values, 
        mode='lines',
        name='Diário',
        opacity=0.3,
        line=dict(width=1, color='#1f77b4')
    ))
    fig.add_trace(go.Scatter(
        x=ts_ma7.index, 
        y=ts_ma7.values, 
        mode='lines',
        name='MM7',
        line=dict(width=2, color='#ff7f0e')
    ))
    fig.add_trace(go.Scatter(
        x=ts_ma30.index, 
        y=ts_ma30.values, 
        mode='lines',
        name='MM30',
        line=dict(width=3, color='#2ca02c')
    ))
    
    # Adiciona marcação da pandemia
    fig.add_vrect(
        x0="2020-03-01", 
        x1="2022-05-22",
        fillcolor="#ffcccc",
        opacity=0.2,
        line_width=0
    )
    
    fig.update_layout(
        title='Evolução Temporal das Internações',
        xaxis_title='Data',
        yaxis_title='Internações por Dia',
        margin=dict(l=60, r=20, t=50, b=50),
        hovermode='x unified',
        height=500,
        showlegend=True
    )
    
    # Salva como SVG
    fig.write_image(output_path, format='svg', width=1200, height=500)
    print(f"  Gráfico salvo em: {output_path}")
    
    return output_path

def generate_heatmap_charts(df, output_dir):
    """Gera heatmaps de sazonalidade"""
    print("Gerando heatmaps...")
    
    if 'ANO' not in df.columns or 'MES' not in df.columns:
        print("  Sem dados de ano/mês para heatmap")
        return []
    
    # Prepara dados
    hm = df.groupby(['ANO', 'MES']).size().reset_index(name='qtd')
    if hm.empty:
        print("  Sem dados para heatmap")
        return []
    
    # Heatmap de contagem
    mat = (hm.pivot(index='ANO', columns='MES', values='qtd')
             .reindex(columns=range(1, 13))
             .fillna(0)
             .astype(int))
    
    fig1 = px.imshow(
        mat.values,
        labels=dict(x='Mês', y='Ano', color='Internações'),
        x=MONTH_LABELS,
        y=mat.index.astype(str).tolist()[::-1],
        aspect='auto',
        color_continuous_scale='Blues',
        text_auto=True
    )
    fig1.update_layout(
        title='Sazonalidade - Contagem Absoluta',
        margin=dict(l=60, r=20, t=40, b=50),
        height=400
    )
    fig1.update_yaxes(autorange='reversed')
    
    output1 = output_dir / 'heatmap_count.svg'
    fig1.write_image(output1, format='svg', width=1000, height=400)
    print(f"  Heatmap 1 salvo em: {output1}")
    
    # Heatmap de participação percentual
    row_sums = mat.sum(axis=1).replace(0, np.nan)
    share = (mat.div(row_sums, axis=0) * 100).round(1)
    
    fig2 = px.imshow(
        share.values,
        labels=dict(x='Mês', y='Ano', color='% no ano'),
        x=MONTH_LABELS,
        y=share.index.astype(str).tolist()[::-1],
        aspect='auto',
        color_continuous_scale='Viridis',
        text_auto=True
    )
    fig2.update_layout(
        title='Sazonalidade - Participação Percentual',
        margin=dict(l=60, r=20, t=40, b=50),
        height=400
    )
    fig2.update_yaxes(autorange='reversed')
    
    output2 = output_dir / 'heatmap_share.svg'
    fig2.write_image(output2, format='svg', width=1000, height=400)
    print(f"  Heatmap 2 salvo em: {output2}")
    
    return [output1, output2]

def generate_distribution_charts(df, output_dir):
    """Gera gráficos de distribuição"""
    print("Gerando gráficos de distribuição...")
    
    outputs = []
    
    # Distribuição por sexo
    if 'SEXO_TXT' in df.columns or 'SEXO' in df.columns:
        sex_col = 'SEXO_TXT' if 'SEXO_TXT' in df.columns else 'SEXO'
        
        # Pie chart
        sex_counts = df[sex_col].value_counts()
        fig_pie = go.Figure(data=[go.Pie(
            labels=sex_counts.index,
            values=sex_counts.values,
            hole=0.4,
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        )])
        fig_pie.update_layout(
            title='Distribuição por Sexo',
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        
        output_pie = output_dir / 'sex_distribution_pie.svg'
        fig_pie.write_image(output_pie, format='svg', width=600, height=400)
        outputs.append(output_pie)
        print(f"  Pie chart salvo em: {output_pie}")
        
        # Bar chart
        fig_bar = go.Figure(data=[go.Bar(
            x=sex_counts.values,
            y=sex_counts.index,
            orientation='h',
            marker=dict(color='#1f77b4')
        )])
        fig_bar.update_layout(
            title='Internações por Sexo',
            xaxis_title='Número de Internações',
            yaxis_title='Sexo',
            margin=dict(l=60, r=20, t=40, b=50),
            height=400
        )
        
        output_bar = output_dir / 'sex_distribution_bar.svg'
        fig_bar.write_image(output_bar, format='svg', width=600, height=400)
        outputs.append(output_bar)
        print(f"  Bar chart salvo em: {output_bar}")
    
    # Distribuição por faixa etária
    if 'FAIXA_ETARIA' in df.columns:
        age_counts = df['FAIXA_ETARIA'].value_counts().sort_index()
        
        fig_age = go.Figure(data=[go.Bar(
            x=age_counts.index,
            y=age_counts.values,
            marker=dict(color='#2ca02c')
        )])
        fig_age.update_layout(
            title='Distribuição por Faixa Etária',
            xaxis_title='Faixa Etária',
            yaxis_title='Internações',
            margin=dict(l=60, r=20, t=40, b=50),
            height=400
        )
        
        output_age = output_dir / 'age_distribution.svg'
        fig_age.write_image(output_age, format='svg', width=800, height=400)
        outputs.append(output_age)
        print(f"  Age distribution salvo em: {output_age}")
    
    # Distribuição por grupo CID
    if 'CID_GRUPO_J' in df.columns:
        cid_counts = df['CID_GRUPO_J'].value_counts().head(15)
        
        fig_cid = go.Figure(data=[go.Bar(
            x=cid_counts.values,
            y=cid_counts.index,
            orientation='h',
            marker=dict(color='#ff7f0e')
        )])
        fig_cid.update_layout(
            title='Top 15 Grupos CID-10',
            xaxis_title='Internações',
            yaxis_title='Grupo CID-10',
            margin=dict(l=100, r=20, t=40, b=50),
            height=500
        )
        
        output_cid = output_dir / 'cid_distribution.svg'
        fig_cid.write_image(output_cid, format='svg', width=800, height=500)
        outputs.append(output_cid)
        print(f"  CID distribution salvo em: {output_cid}")
    
    return outputs

def generate_mortality_charts(df, output_dir):
    """Gera gráficos relacionados à mortalidade"""
    print("Gerando gráficos de mortalidade...")
    
    outputs = []
    
    if 'MORTE' in df.columns and 'FAIXA_ETARIA' in df.columns:
        # Mortalidade por faixa etária
        mort_by_age = df.groupby('FAIXA_ETARIA')['MORTE'].mean().reset_index(name='taxa')
        mort_by_age['taxa_pct'] = mort_by_age['taxa'] * 100
        
        fig_mort_age = go.Figure(data=[go.Bar(
            x=mort_by_age['FAIXA_ETARIA'],
            y=mort_by_age['taxa_pct'],
            text=[f'{x:.1f}%' for x in mort_by_age['taxa_pct']],
            textposition='auto',
            marker=dict(color='#d62728')
        )])
        fig_mort_age.update_layout(
            title='Taxa de Mortalidade por Faixa Etária',
            xaxis_title='Faixa Etária',
            yaxis_title='Taxa de Mortalidade (%)',
            margin=dict(l=60, r=20, t=40, b=50),
            height=400
        )
        
        output_mort_age = output_dir / 'mortality_by_age.svg'
        fig_mort_age.write_image(output_mort_age, format='svg', width=800, height=400)
        outputs.append(output_mort_age)
        print(f"  Mortality by age salvo em: {output_mort_age}")
    
    if 'MORTE' in df.columns and 'DT_INTER' in df.columns:
        # Mortalidade ao longo do tempo
        df_mort = df.dropna(subset=['DT_INTER']).copy()
        df_mort = df_mort.set_index('DT_INTER').sort_index()
        mort_daily = df_mort.groupby(pd.Grouper(freq='D'))['MORTE'].mean()
        mort_ma30 = mort_daily.rolling(30, min_periods=7).mean()
        
        fig_mort_time = go.Figure()
        fig_mort_time.add_trace(go.Scatter(
            x=mort_daily.index,
            y=mort_daily.values * 100,
            mode='lines',
            name='Diária',
            opacity=0.3,
            line=dict(color='#d62728', width=1)
        ))
        fig_mort_time.add_trace(go.Scatter(
            x=mort_ma30.index,
            y=mort_ma30.values * 100,
            mode='lines',
            name='MM30',
            line=dict(color='#9467bd', width=2)
        ))
        fig_mort_time.update_layout(
            title='Mortalidade ao Longo do Tempo',
            xaxis_title='Data',
            yaxis_title='Taxa de Óbito (%)',
            margin=dict(l=60, r=20, t=40, b=50),
            height=400
        )
        
        output_mort_time = output_dir / 'mortality_time_series.svg'
        fig_mort_time.write_image(output_mort_time, format='svg', width=1000, height=400)
        outputs.append(output_mort_time)
        print(f"  Mortality time series salvo em: {output_mort_time}")
    
    return outputs

def generate_metadata(metrics, output_dir):
    """Gera arquivo de metadados com as métricas"""
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'metrics': metrics,
        'charts': {
            'time_series': 'time_series.svg',
            'heatmap_count': 'heatmap_count.svg',
            'heatmap_share': 'heatmap_share.svg',
            'sex_distribution_pie': 'sex_distribution_pie.svg',
            'sex_distribution_bar': 'sex_distribution_bar.svg',
            'age_distribution': 'age_distribution.svg',
            'cid_distribution': 'cid_distribution.svg',
            'mortality_by_age': 'mortality_by_age.svg',
            'mortality_time_series': 'mortality_time_series.svg',
        }
    }
    
    output_file = output_dir / 'metadata.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"Metadados salvos em: {output_file}")
    return output_file

def main():
    """Função principal"""
    print("=" * 60)
    print("GERADOR DE GRÁFICOS SIH/SUS")
    print("=" * 60)
    
    try:
        # 1. Carregar dados
        df = load_and_combine_data()
        
        # 2. Pré-processar
        df = preprocess_data(df)
        
        # 3. Calcular métricas
        metrics = calculate_metrics(df)
        
        print(f"\nMétricas calculadas:")
        print(f"  Total de internações: {metrics['total_internacoes']:,}")
        print(f"  Média de idade: {metrics['media_idade']:.1f} anos")
        print(f"  Taxa de mortalidade: {metrics['taxa_mortalidade']:.2f}%")
        print(f"  Média de permanência: {metrics['media_permanencia']:.1f} dias")
        print(f"  Período: {metrics['ano_min']} - {metrics['ano_max']}")
        
        # 4. Gerar gráficos
        print(f"\nGerando gráficos...")
        
        # Série temporal
        time_series_path = generate_time_series_chart(
            df, 
            OUTPUT_DIR / 'time_series.svg'
        )
        
        # Heatmaps
        heatmap_paths = generate_heatmap_charts(df, OUTPUT_DIR)
        
        # Distribuições
        distribution_paths = generate_distribution_charts(df, OUTPUT_DIR)
        
        # Mortalidade
        mortality_paths = generate_mortality_charts(df, OUTPUT_DIR)
        
        # 5. Gerar metadados
        metadata_path = generate_metadata(metrics, OUTPUT_DIR)
        
        print(f"\n✅ Processo concluído!")
        print(f"📊 Gráficos gerados: {len(heatmap_paths) + len(distribution_paths) + len(mortality_paths) + 1}")
        print(f"📁 Pasta de saída: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    main()