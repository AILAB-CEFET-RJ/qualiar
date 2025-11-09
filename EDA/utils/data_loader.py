import pandas as pd
import streamlit as st

@st.cache_data
def load_estacoes_data():
    url_estacoes_unificadas = 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/Estacoes_Tratadas_Por_Dia/ESTACOES_UNIFICADAS_POR_DIA.csv'
    
    df_estacoes_unificadas = pd.read_csv(url_estacoes_unificadas, sep=',')
    
    return df_estacoes_unificadas

@st.cache_data
def load_rio_de_janeiro_qualiar_data():
    url_rio_de_janeiro_qualiar = r'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO.csv'
  
    df_rio_de_janeiro_qualiar = pd.read_csv(url_rio_de_janeiro_qualiar, sep=',')
  
    df_rio_de_janeiro_qualiar["data_dia"] = pd.to_datetime(df_rio_de_janeiro_qualiar["data_dia"], format="%Y-%m-%d", errors="coerce")
    df_rio_de_janeiro_qualiar["ano"] = df_rio_de_janeiro_qualiar["data_dia"].dt.year
    df_rio_de_janeiro_qualiar["mes"] = df_rio_de_janeiro_qualiar["data_dia"].dt.month
    df_rio_de_janeiro_qualiar["ano_mes"] = df_rio_de_janeiro_qualiar["data_dia"].dt.to_period("M").astype(str)

    return df_rio_de_janeiro_qualiar
  
@st.cache_data
def load_rio_de_janeiro_qualiar_treated_data():
    url_rio_de_janeiro_qualiar_treated = r'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv'
  
    df_rio_de_janeiro_qualiar_treated = pd.read_csv(url_rio_de_janeiro_qualiar_treated, sep=',')
  
    df_rio_de_janeiro_qualiar_treated["data_dia"] = pd.to_datetime(df_rio_de_janeiro_qualiar_treated["data_dia"], format="%Y-%m-%d", errors="coerce")
    df_rio_de_janeiro_qualiar_treated["ano"] = df_rio_de_janeiro_qualiar_treated["data_dia"].dt.year
    df_rio_de_janeiro_qualiar_treated["mes"] = df_rio_de_janeiro_qualiar_treated["data_dia"].dt.month
    df_rio_de_janeiro_qualiar_treated["ano_mes"] = df_rio_de_janeiro_qualiar_treated["data_dia"].dt.to_period("M").astype(str)
  
    return df_rio_de_janeiro_qualiar_treated

@st.cache_data(show_spinner=True)
def load_sus_data() -> pd.DataFrame:
    """
    Lê os CSVs anuais diretamente do GitHub e concatena em um único DataFrame.
    Converte DT_INTER e DT_SAIDA para datetime no formato exigido (%Y%m%d).
    NÃO altera nomes de colunas — usa exatamente os do CSV.
    """
    url1 = "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte1.csv"
    url2 = "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte2.csv"
    url3 = "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte3.csv"
    
    df1 = pd.read_csv(url1, sep=",")
    df2 = pd.read_csv(url2, sep=",")
    df3 = pd.read_csv(url3, sep=",")
    df_sus = pd.concat([df1, df2, df3], ignore_index=True)
    

    
    return df_sus

def describe_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo do schema: tipo, % nulos, exemplos."""
    rows = []
    n = len(df)
    for c in df.columns:
        dtype = str(df[c].dtype)
        n_null = int(df[c].isna().sum())
        pct_null = 100 * n_null / n if n else 0.0
        sample_vals = df[c].dropna().astype(str).head(3).tolist()
        rows.append({
            "coluna": c,
            "dtype": dtype,
            "%_nulos": round(pct_null, 2),
            "exemplos": " | ".join(sample_vals)
        })
    return pd.DataFrame(rows).sort_values("%_nulos", ascending=False)