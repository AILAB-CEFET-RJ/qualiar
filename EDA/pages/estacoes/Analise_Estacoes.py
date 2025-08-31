import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def _kpi_int(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return "-"

def _ms_todos_form(label: str, options, current=None, key: str = None):
    """Multiselect com 'Todos' (para usar dentro de st.form). Retorna lista de strings."""
    options = sorted({str(o) for o in options})
    token = "Todos"
    mult_opts = [token] + options

    if not options:
        default = []
    else:
        if current is None or set(map(str, current)) == set(options):
            default = [token]
        else:
            default = [s for s in map(str, current) if s in mult_opts]

    sel = st.multiselect(label, mult_opts, default=default, key=key)
    return options if (not sel or token in sel) else [s for s in sel if s != token]

def _section_filters(df_base: pd.DataFrame, nome_col: str, key_prefix: str,
                     default_d_ini=None, default_d_fim=None, default_estacoes=None):
    """
    Cria um form no corpo da seção (não no sidebar) para filtrar apenas aquela seção.
    Retorna (df_filtrado, state_dict).
    """
    if "data_dia" in df_base.columns:
        min_d = pd.to_datetime(df_base["data_dia"]).min()
        max_d = pd.to_datetime(df_base["data_dia"]).max()
    else:
        min_d = max_d = None

    if default_d_ini is None and isinstance(min_d, pd.Timestamp):
        default_d_ini = min_d.date()
    if default_d_fim is None and isinstance(max_d, pd.Timestamp):
        default_d_fim = max_d.date()

    if default_estacoes is None and nome_col:
        default_estacoes = sorted(df_base[nome_col].dropna().astype(str).unique().tolist())
    if default_estacoes is None:
        default_estacoes = []

    state_key = f"{key_prefix}_filters"
    if state_key not in st.session_state:
        st.session_state[state_key] = {
            "d_ini": default_d_ini,
            "d_fim": default_d_fim,
            "estacoes": default_estacoes,
        }

    cur = st.session_state[state_key]

    with st.form(f"{key_prefix}_form"):
        c1, c2 = st.columns(2)
        with c1:
            d_ini = st.date_input("Início", value=cur["d_ini"], key=f"{key_prefix}_dini",
                                  min_value=default_d_ini, max_value=default_d_fim)
        with c2:
            d_fim = st.date_input("Fim", value=cur["d_fim"], key=f"{key_prefix}_dfim",
                                  min_value=default_d_ini, max_value=default_d_fim)

        sel_estacoes = _ms_todos_form("Estações desta seção", default_estacoes,
                                      current=cur["estacoes"], key=f"{key_prefix}_ests")
        submitted = st.form_submit_button("Aplicar")

    if submitted:
        st.session_state[state_key] = {"d_ini": d_ini, "d_fim": d_fim, "estacoes": sel_estacoes}
        cur = st.session_state[state_key]

    mask = pd.Series(True, index=df_base.index)
    if "data_dia" in df_base.columns and cur["d_ini"] and cur["d_fim"]:
        mask &= pd.to_datetime(df_base["data_dia"]).dt.date.between(cur["d_ini"], cur["d_fim"])
    if nome_col and cur["estacoes"]:
        mask &= df_base[nome_col].astype(str).isin(cur["estacoes"])

    return df_base[mask].copy(), cur


def show(df_estacoes: pd.DataFrame):
    st.title("🗺️ Estações de Monitoramento — EDA")

    with st.expander("ℹ️ Sobre os dados", expanded=False):
        st.markdown(
            """
            ### 📍 Informações da Estação
            - **nome_estacao**: Nome da estação de monitoramento  
            - **lat/lon**: Coordenadas geográficas da estação  
            - **data_dia**: Data da medição (YYYY-MM-DD)  
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
            - ESTAÇÃO BANGU • ESTAÇÃO CAMPO GRANDE • ESTAÇÃO CENTRO • ESTAÇÃO COPACABANA  
            - ESTAÇÃO IRAJÁ • ESTAÇÃO PEDRA DE GUARATIBA • ESTAÇÃO SÃO CRISTÓVÃO • ESTAÇÃO TIJUCA
            """
        )

    df = df_estacoes.copy()

    if "data_dia" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["data_dia"]):
        df["data_dia"] = pd.to_datetime(df["data_dia"].astype(str), format="%Y-%m-%d", errors="coerce")

    if "data_dia" in df.columns:
        if "ano" not in df.columns:
            df["ano"] = df["data_dia"].dt.year
        if "mes" not in df.columns:
            df["mes"] = df["data_dia"].dt.month

    for c in ["lat", "lon"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    numeric_cols = [c for c in ["temp","ur","chuva","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"] if c in df.columns]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    st.sidebar.header("🔎 Filtros")

    nome_col = "nome_estacao" if "nome_estacao" in df.columns else None
    estacoes_opts = df[nome_col].dropna().astype(str).unique().tolist() if nome_col else []
    min_d = df["data_dia"].min() if "data_dia" in df.columns else None
    max_d = df["data_dia"].max() if "data_dia" in df.columns else None

    if "est_filters" not in st.session_state:
        st.session_state["est_filters"] = {
            "d_ini": (min_d.date() if isinstance(min_d, pd.Timestamp) else None),
            "d_fim": (max_d.date() if isinstance(max_d, pd.Timestamp) else None),
            "estacoes": list(map(str, estacoes_opts)),
        }
    applied = st.session_state["est_filters"]
  
    with st.sidebar.form("form_filtros_estacoes"):
      if min_d is not None and max_d is not None:
          # Força conversão para date
          d_ini = applied.get("d_ini")
          d_fim = applied.get("d_fim")
          if isinstance(d_ini, pd.Timestamp):
              d_ini = d_ini.date()
          if isinstance(d_fim, pd.Timestamp):
              d_fim = d_fim.date()
          d_ini = d_ini if d_ini is not None else min_d.date()
          d_fim = d_fim if d_fim is not None else max_d.date()
          d_ini_sel, d_fim_sel = st.date_input(
              "Período",
              value=(d_ini, d_fim),
              min_value=min_d.date(),
              max_value=max_d.date(),
              key="est_periodo",
          )
      else:
          d_ini_sel, d_fim_sel = applied.get("d_ini"), applied.get("d_fim")

      sel_estacoes = _ms_todos_form("Estações", estacoes_opts, current=applied["estacoes"], key="est_estacoes")

      submitted = st.form_submit_button("Filtrar")

    if submitted:
        st.session_state["est_filters"] = {
            "d_ini": d_ini_sel,
            "d_fim": d_fim_sel,
            "estacoes": sel_estacoes,
        }
    applied = st.session_state["est_filters"]

    mask = pd.Series(True, index=df.index)
    if "data_dia" in df.columns and applied["d_ini"] and applied["d_fim"]:
        mask &= df["data_dia"].dt.date.between(applied["d_ini"], applied["d_fim"])
    if nome_col and applied["estacoes"]:
        mask &= df[nome_col].astype(str).isin(applied["estacoes"])

    dff = df[mask].copy()

    n_reg = len(dff)
    n_est = dff[nome_col].nunique() if nome_col else 0
    periodo_txt = f'{applied["d_ini"]} → {applied["d_fim"]}' if applied["d_ini"] and applied["d_fim"] else "-"

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros (filtro)", _kpi_int(n_reg))
    col2.metric("Estações ativas", _kpi_int(n_est))
    col3.metric("Período", periodo_txt)

    st.caption(f'Mostrando {n_reg:,} registros após filtros.'.replace(",", "."))

    st.subheader("🗺️ Mapa das Estações (RJ) — cor e tamanho por variável")

    if {"lat", "lon", nome_col}.issubset(dff.columns) and not dff.empty and numeric_cols:
        left, mid, right = st.columns([2,1,1])
        with left:
            var_col = st.selectbox(
                "Variável para cor/tamanho",
                options=numeric_cols,
                index=(numeric_cols.index("temp") if "temp" in numeric_cols else 0),
                key="map_var"
            )
        with mid:
            agg_label = st.selectbox("Agregação", options=["média", "mediana", "máximo"], index=0, key="map_agg")
        with right:
            max_size = st.slider("Tamanho máx. do marcador", min_value=16, max_value=64, value=40, step=2, key="map_size")

        agg_func = {"média": "mean", "mediana": "median", "máximo": "max"}[agg_label]
        grp_cols = [nome_col, "lat", "lon"]
        df_map = (dff[grp_cols + [var_col]]
                  .groupby(grp_cols, dropna=True)[var_col]
                  .agg(agg_func)
                  .reset_index()
                  .rename(columns={var_col: "valor"}))

        df_map = df_map.dropna(subset=["lat","lon","valor"])
        if not df_map.empty:
            p5, p95 = np.nanpercentile(df_map["valor"], [5, 95]) if df_map["valor"].notna().sum() > 1 else (df_map["valor"].min(), df_map["valor"].max())
            if p95 == p5:
                norm = np.ones(len(df_map))
            else:
                norm = (df_map["valor"] - p5) / (p95 - p5)
                norm = np.clip(norm, 0, 1)

            size_min = max(6, int(max_size * 0.25))
            df_map["mk_size"] = size_min + norm * (max_size - size_min)

            center_lat = df_map["lat"].mean()
            center_lon = df_map["lon"].mean()

            fig_map = go.Figure(go.Scattermapbox(
                lat=df_map["lat"],
                lon=df_map["lon"],
                mode="markers",
                text=df_map[nome_col],
                customdata=np.stack([df_map["valor"]], axis=-1),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    f"{var_col} ({agg_label}): " + "%{customdata[0]:.2f}<extra></extra>"
                ),
                marker=dict(
                    size=df_map["mk_size"],
                    color=df_map["valor"],
                    colorscale="Turbo",
                    cmin=float(df_map["valor"].min()),
                    cmax=float(df_map["valor"].max()),
                    opacity=0.9,
                    showscale=True,
                    colorbar=dict(title=var_col)
                ),
            ))

            fig_map.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=10),
                margin=dict(l=10, r=10, t=10, b=10),
                height=520,
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Sem valores válidos para a variável selecionada nas estações filtradas.")
    else:
        st.warning("Dados insuficientes para o mapa (precisa de colunas: lat, lon, nome_estacao e ao menos uma variável numérica).")

    st.subheader("📈 Tendências diárias por estação (MM30)")

    df_ts_base, ts_state = _section_filters(df, nome_col, key_prefix="ts_mm30")

    if "data_dia" in df_ts_base.columns and not df_ts_base.empty:

        all_vars = [c for c in ["temp","ur","chuva","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"]
                    if c in df_ts_base.columns]
        default_vars = [v for v in ["temp","no2","o3"] if v in all_vars]

        vars_sel = st.multiselect(
            "Variáveis (sobrepostas em cada estação, normalizadas por estação+variável)",
            options=all_vars,
            default=default_vars,
            key="ts_vars_mm30"
        )

        if vars_sel:
            mm_window = 30  

            sub = df_ts_base[[nome_col, "data_dia"] + vars_sel].copy()
            sub["data_dia"] = pd.to_datetime(sub["data_dia"], errors="coerce")
            sub = sub.dropna(subset=["data_dia"]).sort_values(["data_dia"])

            long = sub.melt(id_vars=[nome_col, "data_dia"],
                            value_vars=vars_sel,
                            var_name="variavel", value_name="valor").dropna(subset=["valor"])
            long = long.sort_values([nome_col, "variavel", "data_dia"])
            long["mm30"] = long.groupby([nome_col, "variavel"])["valor"]\
                              .transform(lambda s: s.rolling(mm_window, min_periods=1).mean())

            def _minmax_grp(s: pd.Series):
                lo, hi = s.min(), s.max()
                if pd.isna(lo) or pd.isna(hi) or hi == lo:
                    return pd.Series(np.full(len(s), 0.5), index=s.index)
                return (s - lo) / (hi - lo)

            long["y"] = long.groupby([nome_col, "variavel"])["mm30"].transform(_minmax_grp)

            ordem_fix = [
                "ESTAÇÃO BANGU", "ESTAÇÃO CAMPO GRANDE", "ESTAÇÃO CENTRO", "ESTAÇÃO COPACABANA",
                "ESTAÇÃO IRAJÁ", "ESTAÇÃO PEDRA DE GUARATIBA", "ESTAÇÃO SÃO CRISTÓVÃO", "ESTAÇÃO TIJUCA"
            ]
            est_disp = [e for e in ordem_fix if e in long[nome_col].unique().tolist()]
            if not est_disp:
                est_disp = sorted(long[nome_col].unique())

            fig_mult = px.line(
                long,
                x="data_dia", y="y",
                color="variavel",
                facet_row=nome_col,
                category_orders={nome_col: est_disp},
                title=f"Tendências (MM30) — {'; '.join(vars_sel)}",
            )

            fig_mult.update_layout(
                height=max(320, 180 * len(est_disp)),
                legend_title="Variável",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            fig_mult.update_xaxes(matches="x", showgrid=True)
            fig_mult.update_yaxes(showticklabels=False, title_text="")

            fig_mult.for_each_annotation(lambda a: a.update(text="") if isinstance(a.text, str) and f"{nome_col}=" in a.text else ())

            for i, est in enumerate(est_disp, start=1):
              xref = "x domain" if i == 1 else f"x{i} domain"
              yref = "y domain" if i == 1 else f"y{i} domain"
              fig_mult.add_annotation(
                  x=0.5, y=1.02,            
                  xref=xref, yref=yref,
                  text=est,
                  showarrow=False,
                  xanchor="center", yanchor="bottom",
                  font=dict(size=13)
            ) 

            st.plotly_chart(fig_mult, use_container_width=True)
        else:
            st.info("Selecione ao menos uma variável para exibir as tendências por estação.")
    else:
        st.info("Não foi possível montar tendências (coluna 'data_dia' ausente ou sem dados).")

  
    num_cols = [c for c in ["temp","ur","chuva","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"] if c in dff.columns]

    st.subheader("🏷️ Comparação por Estação (Boxplots)")
    if nome_col and num_cols:
        col_sel = st.selectbox("Escolha a variável", options=num_cols, index=0, key="bx_var")
        data_box = dff[[nome_col, col_sel]].dropna()
        if not data_box.empty:
            med = data_box.groupby(nome_col)[col_sel].median().sort_values(ascending=False).index.tolist()
            fig_box = px.box(data_box, x=nome_col, y=col_sel, category_orders={nome_col: med}, points="outliers",
                             title=f"{col_sel} — distribuição por estação")
            fig_box.update_layout(xaxis_title="Estação", yaxis_title=col_sel, xaxis_tickangle=-30, margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Não há dados suficientes para os boxplots após os filtros.")

    st.subheader("📅 Sazonalidade Mensal (Boxplot por Mês)")
    if "mes" in dff.columns and num_cols:
        col_sel2 = st.selectbox("Variável para sazonalidade", options=num_cols, index=min(1, len(num_cols)-1), key="bx_mes")
        data_month = dff[["mes", col_sel2]].dropna()
        if not data_month.empty:
            order_m = list(range(1,13))
            labels_m = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
            data_month["mes_lbl"] = pd.Categorical(data_month["mes"].map(dict(zip(order_m, labels_m))), categories=labels_m, ordered=True)
            fig_bm = px.box(data_month, x="mes_lbl", y=col_sel2, title=f"{col_sel2} — sazonalidade por mês")
            fig_bm.update_layout(xaxis_title="Mês", yaxis_title=col_sel2, margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_bm, use_container_width=True)

    st.subheader("🔗 Correlação entre Variáveis")
    if num_cols:
        corr_df = dff[num_cols].corr(method="pearson").round(2)
        fig_corr = px.imshow(
            corr_df.values,
            x=corr_df.columns, y=corr_df.columns,
            color_continuous_scale="RdBu", zmin=-1, zmax=1, text_auto=True,
            labels=dict(color="corr")
        )
        fig_corr.update_layout(title="Matriz de correlação (Pearson)", margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("🧪 Completude por Variável (não nulos %)")
    pct = (1 - dff[num_cols].isna().mean()).mul(100).round(1) if num_cols else pd.Series(dtype=float)
    if not pct.empty:
        fig_pct = px.bar(pct.sort_values(ascending=False).reset_index().rename(columns={"index":"variavel",0:"pct"}),
                         x="variavel", y="pct", text_auto=".1f")
        fig_pct.update_layout(title="Completude de dados por variável (%)", xaxis_title="", yaxis_title="%", margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_pct, use_container_width=True)

    st.subheader("⬇️ Exportar dados filtrados")
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV filtrado", data=csv, file_name="estacoes_filtrado.csv", mime="text/csv")
