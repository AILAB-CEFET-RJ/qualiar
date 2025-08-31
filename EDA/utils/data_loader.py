import pandas as pd
import streamlit as st
import requests
import zipfile
import io

@st.cache_data
def load_estacoes_data():
    url_estacoes_unificadas = 'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/Estacoes_Tratadas_Por_Dia/ESTACOES_UNIFICADAS_POR_DIA.csv'
    
    df_estacoes_unificadas = pd.read_csv(url_estacoes_unificadas, sep=',')
    
    return df_estacoes_unificadas

@st.cache_data
def load_rio_de_janeiro_qualiar_data():
  url_rio_de_janeiro_qualiar = r'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO.csv'
  
  df_rio_de_janeiro_qualiar = pd.read_csv(url_rio_de_janeiro_qualiar, sep=',')
  
  return df_rio_de_janeiro_qualiar
  
@st.cache_data
def load_rio_de_janeiro_qualiar_treated_data():
  url_rio_de_janeiro_qualiar_treated = r'https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv'
  
  df_rio_de_janeiro_qualiar_treated = pd.read_csv(url_rio_de_janeiro_qualiar_treated, sep=',')
  
  return df_rio_de_janeiro_qualiar_treated

@st.cache_data(show_spinner=True)
def load_sus_data() -> pd.DataFrame:
    """
    Lê os CSVs anuais diretamente do GitHub e concatena em um único DataFrame.
    Converte DT_INTER e DT_SAIDA para datetime no formato exigido (%Y%m%d).
    NÃO altera nomes de colunas — usa exatamente os do CSV.
    """
    url1 = "https://github.com/AILAB-CEFET-RJ/qualiar/raw/main/data/datasus/INTERNACOES_STREAMLIT_parte1.zip"
    url2 = "https://github.com/AILAB-CEFET-RJ/qualiar/raw/main/data/datasus/INTERNACOES_STREAMLIT_parte2.zip"

    def read_zip_csv_from_url(url):
        response = requests.get(url)
        response.raise_for_status()
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        print(f"Arquivos no ZIP ({url}): {zip_file.namelist()}")
        with zip_file.open(zip_file.namelist()[0]) as file:
            df = pd.read_csv(file)
        return df

    df1 = read_zip_csv_from_url(url1)
    df2 = read_zip_csv_from_url(url2)

    df_sus = pd.concat([df1, df2], ignore_index=True)
    
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