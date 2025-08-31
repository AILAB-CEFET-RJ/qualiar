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
    anos = range(2012, 2025)
    generic_url = (
        "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/Ano/dados_filtrados_{ano}.csv"
    )

    frames = []
    for ano in anos:
        df = pd.read_csv(generic_url.format(ano=ano), sep=",")
        frames.append(df)

    df_sus = pd.concat(frames, ignore_index=True)

    if "DT_INTER" in df_sus.columns:
        df_sus["DT_INTER"] = pd.to_datetime(df_sus["DT_INTER"].astype(str), format="%Y%m%d", errors="coerce")
    if "DT_SAIDA" in df_sus.columns:
        df_sus["DT_SAIDA"] = pd.to_datetime(df_sus["DT_SAIDA"].astype(str), format="%Y%m%d", errors="coerce")

    return df_sus

def _map_sexo_code(x) -> str:
    try:
        xi = int(x)
    except Exception:
        return str(x)
    if xi == 1:
        return "Masculino"
    if xi == 3:
        return "Feminino"
    return "Ignorado"

def _cid_to_cat3(cid: str) -> str | None:
    if isinstance(cid, str):
        cid = cid.strip().upper()
        import re
        m = re.match(r"^([A-Z]\d{2})", cid)
        return m.group(1) if m else None
    return None

def _map_grupo_J(cid: str) -> str:
    """
    Agrupa subcapítulos J00-J99 (respiratórios) a partir de DIAG_PRINC.
    """
    if not isinstance(cid, str):
        return "Não J/Indefinido"
    cid = cid.strip().upper()
    if not cid.startswith("J") or len(cid) < 3:
        return "Não J/Indefinido"
    try:
        num = int(cid[1:3])
    except Exception:
        return "J - Outros"
    if 0 <= num <= 6:
        return "J00-J06 Infecções agudas vias aéreas superiores"
    if 9 <= num <= 18:
        return "J09-J18 Influenza e Pneumonias"
    if 20 <= num <= 22:
        return "J20-J22 Outras infecções vias aéreas inferiores"
    if 40 <= num <= 47:
        return "J40-J47 Doenças crônicas das vias aéreas (ex.: DPOC, Asma)"
    if 60 <= num <= 70:
        return "J60-J70 Pneumoconioses e doenças por agentes externos"
    if 80 <= num <= 84:
        return "J80-J84 Doenças do interstício pulmonar"
    if 85 <= num <= 86:
        return "J85-J86 Supurações pulmonares"
    if 90 <= num <= 94:
        return "J90-J94 Doenças da pleura"
    if num == 95:
        return "J95 Complicações respiratórias pós-procedimentos"
    if 96 <= num <= 99:
        return "J96-J99 Outras doenças do aparelho respiratório"
    return "J - Outros"

@st.cache_data(show_spinner=False)
def prepare_sus_df(df_sus: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o df_sus bruto (com nomes originais) e:
      - Garante tipos adequados (datas, numéricos)
      - Cria colunas derivadas úteis para análise (ANO, MES, ANO_MES, DIA_SEMANA, SEMANA_ANO, FAIXA_ETARIA)
      - Deriva 'CID_CAT3' e 'CID_GRUPO_J' a partir de DIAG_PRINC.
      - Cria 'SEXO_TXT' com rótulos legíveis.
    NÃO renomeia nem muda nomes originais.
    """
    df = df_sus.copy()

    if "DT_INTER" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["DT_INTER"]):
        df["DT_INTER"] = pd.to_datetime(df["DT_INTER"].astype(str), format="%Y%m%d", errors="coerce")
    if "DT_SAIDA" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["DT_SAIDA"]):
        df["DT_SAIDA"] = pd.to_datetime(df["DT_SAIDA"].astype(str), format="%Y%m%d", errors="coerce")

    for c in ["IDADE", "DIAS_PERM", "MORTE"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "DT_INTER" in df.columns:
        df["ANO"] = df["DT_INTER"].dt.year
        df["MES"] = df["DT_INTER"].dt.month
        df["DIA"] = df["DT_INTER"].dt.day
        df["ANO_MES"] = df["DT_INTER"].dt.to_period("M").astype(str)
        weekday_map = {0:"segunda-feira",1:"terça-feira",2:"quarta-feira",3:"quinta-feira",4:"sexta-feira",5:"sábado",6:"domingo"}
        df["DIA_SEMANA"] = df["DT_INTER"].dt.weekday.map(weekday_map)
        df["SEMANA_ANO"] = df["DT_INTER"].dt.isocalendar().week.astype(int)

    if "IDADE" in df.columns:
        bins = [-1, 4, 14, 24, 44, 64, 79, 120]
        labels = ["0-4", "5-14", "15-24", "25-44", "45-64", "65-79", "80+"]
        df["FAIXA_ETARIA"] = pd.cut(df["IDADE"], bins=bins, labels=labels, include_lowest=True)

    if "SEXO" in df.columns:
        df["SEXO_TXT"] = df["SEXO"].apply(_map_sexo_code)

    if "DIAG_PRINC" in df.columns:
        df["DIAG_PRINC"] = df["DIAG_PRINC"].astype(str).str.upper().str.strip()
        df["CID_CAT3"] = df["DIAG_PRINC"].apply(_cid_to_cat3)
        df["CID_GRUPO_J"] = df["DIAG_PRINC"].apply(_map_grupo_J)

    
    
    return df

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