from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st


SELECTED_HOSP = [
    "2296748",
    "2269384",
    "2295423",
    "2291266",
    "2269481",
    "2798662",
    "2277751",
    "2270269",
    "2296306",
    "2269341",
    "2269724",
    "2270609",
    "2269783",
    "2296616",
    "2280167",
    "2273411",
    "2270234",
    "2298120",
]


def encontrar_raiz_projeto() -> Path:
    diretorio_atual = Path(__file__).resolve().parent
    for caminho in [diretorio_atual, *diretorio_atual.parents]:
        if (caminho / "Data").exists():
            return caminho
    return diretorio_atual


def normalizar_cnes(valor: object) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return texto.zfill(7)


def matriz_haversine_km(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> np.ndarray:
    raio_terra_km = 6371.0088

    lat1_rad = np.radians(lat1)[:, None]
    lon1_rad = np.radians(lon1)[:, None]
    lat2_rad = np.radians(lat2)[None, :]
    lon2_rad = np.radians(lon2)[None, :]

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arcsin(np.sqrt(a))

    return raio_terra_km * c


@st.cache_data(show_spinner=False)
def carregar_bases() -> tuple[pd.DataFrame, pd.DataFrame]:
    raiz = encontrar_raiz_projeto()
    caminho_hospitais = (
        raiz
        / "Data"
        / "IntermediaryData"
        / "DataSus"
        / "respiratory_hospitalization_time_series_by_hospital_with_endereco.parquet"
    )
    caminho_estacoes = (
        raiz
        / "Data"
        / "IntermediaryData"
        / "MonitorAr"
        / "InitialMergedData"
        / "merged_air_quality_data.csv"
    )

    if not caminho_hospitais.exists() or not caminho_estacoes.exists():
        raise FileNotFoundError(
            "Arquivos esperados nao encontrados em Data/IntermediaryData."
        )

    df_hospitais = pd.read_parquet(
        caminho_hospitais,
        usecols=["CNES", "LAT", "LON"],
        dtype={"CNES": "string"},
    )
    df_hospitais["CNES"] = df_hospitais["CNES"].map(normalizar_cnes)
    df_hospitais["LAT"] = pd.to_numeric(df_hospitais["LAT"], errors="coerce")
    df_hospitais["LON"] = pd.to_numeric(df_hospitais["LON"], errors="coerce")
    df_hospitais = (
        df_hospitais.dropna(subset=["CNES", "LAT", "LON"])
        .drop_duplicates(subset=["CNES", "LAT", "LON"])
        .sort_values("CNES")
        .drop_duplicates(subset=["CNES"], keep="first")
        .reset_index(drop=True)
    )

    df_estacoes = pd.read_csv(
        caminho_estacoes,
        usecols=["Nome", "lat", "lon"],
        dtype={"Nome": "string"},
    )
    df_estacoes["Nome"] = df_estacoes["Nome"].astype("string").str.strip()
    df_estacoes["lat"] = pd.to_numeric(df_estacoes["lat"], errors="coerce")
    df_estacoes["lon"] = pd.to_numeric(df_estacoes["lon"], errors="coerce")
    df_estacoes = (
        df_estacoes.dropna(subset=["Nome", "lat", "lon"])
        .drop_duplicates(subset=["Nome", "lat", "lon"])
        .sort_values(["Nome", "lat", "lon"])
        .reset_index(drop=True)
    )

    return df_hospitais, df_estacoes


@st.cache_data(show_spinner=False)
def calcular_estacao_mais_proxima(
    hospitais: pd.DataFrame, estacoes: pd.DataFrame
) -> pd.DataFrame:
    distancias_km = matriz_haversine_km(
        hospitais["LAT"].to_numpy(),
        hospitais["LON"].to_numpy(),
        estacoes["lat"].to_numpy(),
        estacoes["lon"].to_numpy(),
    )

    idx_estacao_mais_proxima = distancias_km.argmin(axis=1)
    menor_distancia_km = distancias_km[
        np.arange(len(hospitais)), idx_estacao_mais_proxima
    ]
    estacao_proxima = estacoes.iloc[idx_estacao_mais_proxima].reset_index(drop=True)

    resultado = hospitais.copy().reset_index(drop=True)
    resultado["estacao_mais_proxima"] = estacao_proxima["Nome"].to_numpy()
    resultado["lat_estacao"] = estacao_proxima["lat"].to_numpy()
    resultado["lon_estacao"] = estacao_proxima["lon"].to_numpy()
    resultado["distancia_km"] = np.round(menor_distancia_km, 3)

    return resultado


def construir_mapa(
    hospitais_filtrados: pd.DataFrame,
    estacoes_filtradas: pd.DataFrame,
    linhas_proximidade: pd.DataFrame,
    mostrar_linhas: bool,
) -> pdk.Deck:
    pontos_hospitais = hospitais_filtrados.rename(
        columns={"CNES": "identificador", "LAT": "lat", "LON": "lon"}
    ).copy()
    pontos_hospitais["tipo"] = "Hospital"
    pontos_hospitais["distancia_km"] = pontos_hospitais["distancia_km"].map(
        lambda valor: f"{valor:.3f}" if pd.notna(valor) else "-"
    )

    pontos_estacoes = estacoes_filtradas.rename(columns={"Nome": "identificador"}).copy()
    pontos_estacoes["tipo"] = "Estacao"
    pontos_estacoes["distancia_km"] = "-"

    todos_os_pontos = pd.concat(
        [
            pontos_hospitais[["lat", "lon"]],
            pontos_estacoes[["lat", "lon"]],
        ],
        ignore_index=True,
    )

    if todos_os_pontos.empty:
        centro_lat, centro_lon = -22.90, -43.20
        zoom = 9.5
    else:
        centro_lat = todos_os_pontos["lat"].mean()
        centro_lon = todos_os_pontos["lon"].mean()
        zoom = 10.5

    layers: list[pdk.Layer] = []

    if not pontos_estacoes.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=pontos_estacoes,
                get_position="[lon, lat]",
                get_radius=320,
                get_fill_color=[34, 111, 226, 190],
                pickable=True,
            )
        )

    if not pontos_hospitais.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=pontos_hospitais,
                get_position="[lon, lat]",
                get_radius=340,
                get_fill_color=[220, 53, 69, 195],
                pickable=True,
            )
        )

    if mostrar_linhas and not linhas_proximidade.empty:
        layers.append(
            pdk.Layer(
                "LineLayer",
                data=linhas_proximidade,
                get_source_position="[LON, LAT]",
                get_target_position="[lon_estacao, lat_estacao]",
                get_color=[20, 20, 20, 140],
                get_width=3,
                pickable=True,
            )
        )

    view_state = pdk.ViewState(
        latitude=float(centro_lat),
        longitude=float(centro_lon),
        zoom=zoom,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{tipo}</b><br/>"
            "<b>ID:</b> {identificador}<br/>"
            "<b>Lat:</b> {lat}<br/>"
            "<b>Lon:</b> {lon}<br/>"
            "<b>Dist. estacao mais proxima (km):</b> {distancia_km}"
        ),
        "style": {
            "backgroundColor": "rgba(18, 18, 18, 0.9)",
            "color": "white",
            "fontSize": "12px",
        },
    }

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_provider="carto",
        map_style="light",
        tooltip=tooltip,
    )


def main() -> None:
    st.set_page_config(
        page_title="Hospitais x Estacoes de Qualidade do Ar",
        page_icon=":hospital:",
        layout="wide",
    )

    st.title("Analise espacial: hospitais e estacoes de qualidade do ar")
    st.write(
        "Visualize hospitais e estacoes no mapa e veja qual estacao esta mais "
        "proxima de cada hospital, com distancia em quilometros."
    )

    try:
        hospitais, estacoes = carregar_bases()
    except Exception as exc:
        st.error(f"Erro ao carregar dados: {exc}")
        st.stop()

    proximidade = calcular_estacao_mais_proxima(hospitais, estacoes)
    cnes_alvo = sorted({normalizar_cnes(cnes) for cnes in SELECTED_HOSP})
    proximidade = proximidade[proximidade["CNES"].isin(cnes_alvo)].copy()

    if proximidade.empty:
        st.error("Nenhum hospital da lista SELECTED_HOSP foi encontrado na base.")
        st.stop()

    cnes_ausentes = sorted(set(cnes_alvo) - set(proximidade["CNES"].astype(str)))
    if cnes_ausentes:
        st.warning(
            "Alguns CNES da lista nao foram encontrados com coordenadas validas: "
            + ", ".join(cnes_ausentes)
        )

    cnes_disponiveis = proximidade["CNES"].astype(str).tolist()
    estacoes_disponiveis = sorted(estacoes["Nome"].astype(str).unique().tolist())

    with st.sidebar:
        st.header("Filtros")
        cnes_selecionados = st.multiselect(
            "Hospitais (CNES)",
            options=cnes_disponiveis,
            default=cnes_disponiveis,
        )
        estacoes_selecionadas = st.multiselect(
            "Estacoes no mapa",
            options=estacoes_disponiveis,
            default=estacoes_disponiveis,
        )
        mostrar_linhas = st.checkbox(
            "Mostrar ligacao hospital -> estacao mais proxima",
            value=True,
        )

    if not cnes_selecionados:
        st.warning("Selecione ao menos um hospital para exibir o mapa e a tabela.")
        st.stop()

    hospitais_filtrados = proximidade[proximidade["CNES"].isin(cnes_selecionados)].copy()
    estacoes_filtradas = estacoes[estacoes["Nome"].isin(estacoes_selecionadas)].copy()

    linhas = hospitais_filtrados.copy()
    linhas["tipo"] = "Ligacao"
    linhas["identificador"] = (
        "Hospital " + linhas["CNES"] + " -> " + linhas["estacao_mais_proxima"]
    )
    linhas["lat"] = linhas["LAT"]
    linhas["lon"] = linhas["LON"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Hospitais no mapa", f"{len(hospitais_filtrados)}")
    col2.metric("Estacoes no mapa", f"{len(estacoes_filtradas)}")
    col3.metric(
        "Distancia media (km)",
        f"{hospitais_filtrados['distancia_km'].mean():.2f}",
    )

    mapa = construir_mapa(
        hospitais_filtrados=hospitais_filtrados,
        estacoes_filtradas=estacoes_filtradas,
        linhas_proximidade=linhas,
        mostrar_linhas=mostrar_linhas,
    )
    st.pydeck_chart(mapa, use_container_width=True)

    st.caption("Legenda: vermelho = hospital, azul = estacao, linha = estacao mais proxima.")

    st.subheader("Estacao mais proxima por hospital")
    tabela = (
        hospitais_filtrados[
            [
                "CNES",
                "estacao_mais_proxima",
                "distancia_km",
                "lat_estacao",
                "lon_estacao",
            ]
        ]
        .sort_values(["distancia_km", "CNES"])
        .rename(
            columns={
                "CNES": "Hospital (CNES)",
                "estacao_mais_proxima": "Estacao mais proxima",
                "distancia_km": "Distancia (km)",
                "lat_estacao": "Lat estacao",
                "lon_estacao": "Lon estacao",
            }
        )
    )

    st.dataframe(tabela, hide_index=True, use_container_width=True)

    csv_tabela = tabela.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar tabela de proximidade (CSV)",
        data=csv_tabela,
        file_name="hospitais_estacoes_proximidade.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
