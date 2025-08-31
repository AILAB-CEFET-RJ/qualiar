import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# Helpers
# -------------------------
def _kpi_int(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return "-"

_MONTH_ORDER = list(range(1, 13))
_MONTH_LABELS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

_AQI_BINS = [
    (0, 40,  "N1 - Boa"),
    (41, 80, "N2 - Moderada"),
    (81, 120,"N3 - Ruim"),
    (121,200,"N4 - Muito Ruim"),
    (201,400,"N5 - Péssima"),
]

_POL_BINS = {
    "pm10":  [(0,50,"N1 - Boa"), (50,100,"N2 - Moderada"), (100,150,"N3 - Ruim"), (150,250,"N4 - Muito Ruim"), (250,600,"N5 - Péssima")],
    "pm2_5": [(0,25,"N1 - Boa"), (25,50,"N2 - Moderada"), (50,75,"N3 - Ruim"), (75,125,"N4 - Muito Ruim"), (125,300,"N5 - Péssima")],
    "o3":    [(0,100,"N1 - Boa"), (100,130,"N2 - Moderada"), (130,160,"N3 - Ruim"), (160,200,"N4 - Muito Ruim"), (200,800,"N5 - Péssima")],
    "co":    [(0,9,"N1 - Boa"), (9,11,"N2 - Moderada"), (11,13,"N3 - Ruim"), (13,15,"N4 - Muito Ruim"), (15,50,"N5 - Péssima")],
    "no2":   [(0,200,"N1 - Boa"), (200,240,"N2 - Moderada"), (240,320,"N3 - Ruim"), (320,1130,"N4 - Muito Ruim"), (1130,3750,"N5 - Péssima")],
    "so2":   [(0,20,"N1 - Boa"), (20,40,"N2 - Moderada"), (40,365,"N3 - Ruim"), (365,800,"N4 - Muito Ruim"), (800,2620,"N5 - Péssima")],
}

def _bucket(value, bins):
    if pd.isna(value):
        return None
    v = float(value)
    v = round(v) 
    for lo, hi, label in bins:
        if v >= lo and v <= hi:   
            return label
    return "Fora da escala"

def classifica_aqi(aqi_val):
    return _bucket(float(aqi_val), _AQI_BINS) if pd.notna(aqi_val) else None

def classifica_pol(val, pol_col):
    pol = pol_col.lower()
    if pol in _POL_BINS and pd.notna(val):
        return _bucket(float(val), _POL_BINS[pol])
    return None

def _ym_pivot_agg(df: pd.DataFrame, value_col: str, agg: str = "mean"):
    """Retorna uma matriz Ano (linhas) x Mês (colunas) para a variável e agregação escolhidas."""
    req = {"ano", "mes", value_col}
    if not req.issubset(df.columns):
        return None
    tmp = df.dropna(subset=[value_col]).copy()
    if tmp.empty:
        return None
    piv = (tmp.groupby(["ano", "mes"])[value_col]
               .agg(agg)
               .unstack("mes")
               .reindex(columns=_MONTH_ORDER))
    return piv

def show(df_rio: pd.DataFrame):
    st.title("🌆 Rio de Janeiro — EDA Ambiental (2012–2024)")

    with st.expander("ℹ️ Sobre os dados", expanded=False):
        st.markdown(
            """
            **Cobertura:** cidade do **Rio de Janeiro**, **séries diárias** agregadas das 8 estações (2012–2024).  
            **Chave temporal:** `data_dia` (YYYY-MM-DD) com `ano`, `mes`, `dia`.

            ### 🌡️ Variáveis Meteorológicas
            - `temp` (°C), `ur` (%), `chuva` (mm)

            ### 🏭 Poluentes Atmosféricos
            - `co` (ppm), `no` (µg/m³), `no2` (µg/m³), `nox` (µg/m³), `so2` (µg/m³), `o3` (µg/m³), `pm10` (µg/m³), `pm2_5` (µg/m³)

            ### Qualidade do Ar
            - `AQI` (índice), `Qualidade_do_Ar` (classe numérica no dataset)
            """
        )

    df = df_rio.copy()

    st.sidebar.header("🔎 Filtro (global da página)")
    min_d = df["data_dia"].min() if "data_dia" in df.columns else None
    max_d = df["data_dia"].max() if "data_dia" in df.columns else None

    if "rio_filters" not in st.session_state:
        st.session_state["rio_filters"] = {
            "d_ini": (min_d.date() if isinstance(min_d, pd.Timestamp) else None),
            "d_fim": (max_d.date() if isinstance(max_d, pd.Timestamp) else None),
        }
    applied = st.session_state["rio_filters"]

    with st.sidebar.form("form_filtros_rio"):
        if min_d is not None and max_d is not None:
            # defaults robustos
            d_ini = applied.get("d_ini") or min_d.date()
            d_fim = applied.get("d_fim") or max_d.date()
            d_ini_sel, d_fim_sel = st.date_input(
                "Período",
                value=(d_ini, d_fim),
                min_value=min_d.date(),
                max_value=max_d.date(),
                key="rio_periodo",
            )
        else:
            d_ini_sel, d_fim_sel = applied.get("d_ini"), applied.get("d_fim")
        submitted = st.form_submit_button("Filtrar")

    if submitted:
        st.session_state["rio_filters"] = {"d_ini": d_ini_sel, "d_fim": d_fim_sel}
    applied = st.session_state["rio_filters"]

    mask = pd.Series(True, index=df.index)
    if "data_dia" in df.columns and applied["d_ini"] and applied["d_fim"]:
        mask &= df["data_dia"].dt.date.between(applied["d_ini"], applied["d_fim"])
    dff = df[mask].copy()

    numeric_cols = [c for c in ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"] if c in dff.columns]

    # -------------------------
    # Visão Geral
    # -------------------------
    st.header("📊 Visão Geral")
    n_dias = dff["data_dia"].nunique() if "data_dia" in dff.columns else len(dff)

    chuva_media = dff["chuva"].mean() if "chuva" in dff.columns else np.nan
    temp_media  = dff["temp"].mean() if "temp" in dff.columns else np.nan
    ur_media    = dff["ur"].mean()   if "ur"   in dff.columns else np.nan
    aqi_med     = dff["AQI"].mean()  if "AQI"  in dff.columns else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dias no período", _kpi_int(n_dias))
    c2.metric("Chuva média diária (mm)", f"{chuva_media:.1f}" if pd.notna(chuva_media) else "–")
    c3.metric("Temperatura média (°C)", f"{temp_media:.1f}" if pd.notna(temp_media) else "–")
    c4.metric("UR média (%)", f"{ur_media:.1f}" if pd.notna(ur_media) else "–")
    c5.metric("AQI médio", f"{aqi_med:.0f}" if pd.notna(aqi_med) else "–")

    aqi_cls = classifica_aqi(aqi_med) if pd.notna(aqi_med) else None
    if aqi_cls:
        c5.caption(f"Classificação: **{aqi_cls}**")

    st.caption(f"Período aplicado: {applied['d_ini']} → {applied['d_fim']}")

    pol_labels = {
        "pm2_5": "MP₂.₅ (24h)",
        "pm10":  "MP₁₀ (24h)",
        "o3":    "O₃ (8h)",
        "co":    "CO (8h)",
        "no2":   "NO₂ (1h)",
        "so2":   "SO₂ (24h)",
    }
    present_pols = [p for p in pol_labels.keys() if p in dff.columns]
    if present_pols:
        st.markdown("**Classificação pelas médias do período:**")
        cols = st.columns(3)
        for i, pol in enumerate(present_pols):
            val = dff[pol].mean()
            cls = classifica_pol(val, pol)
            with cols[i % 3]:
                st.metric(pol_labels[pol], f"{val:.1f}" if pd.notna(val) else "–")
                if cls:
                    st.caption(f"Classificação: **{cls}**")


    # -------------------------
    # Série temporal — AQI diário com faixas de qualidade
    # -------------------------
    st.subheader("Série temporal do AQI diário (com faixas de qualidade)")

    if {"data_dia","AQI"}.issubset(dff.columns) and not dff["AQI"].dropna().empty:
        ts = dff[["data_dia","AQI"]].dropna().sort_values("data_dia")
        ts["AQI_MM30"] = ts["AQI"].rolling(30, min_periods=1).mean()

        fig_aqi = go.Figure()

        bands = [
            (0,   40,  "N1 — Boa (0–40)",          "#1f77b4"),  
            (41,  80,  "N2 — Moderada (41–80)",    "#f1c40f"),  
            (81,  120, "N3 — Ruim (81–120)",       "#e67e22"),  
            (121, 200, "N4 — Muito Ruim (121–200)","#e74c3c"),  
            (201, 400, "N5 — Péssima (201–400)",   "#8e44ad"),  
        ]

        for y0, y1, label, color in bands:
            fig_aqi.add_hrect(y0=y0, y1=y1, line_width=0, fillcolor=color, opacity=0.16, layer="below")

        fig_aqi.add_trace(go.Scatter(
            x=ts["data_dia"], y=ts["AQI"],
            mode="lines+markers",
            name="AQI diário",
            line=dict(width=1.5, color="#34495e"),
            marker=dict(size=3),
            opacity=0.8,
            hovertemplate="Data: %{x|%Y-%m-%d}<br>AQI: %{y:.0f}<extra></extra>"
        ))
        
        fig_aqi.add_trace(go.Scatter(
          x=ts["data_dia"], y=ts["AQI_MM30"],
          mode="lines",
          name="AQI (MM30)",
          line=dict(width=3),
          hovertemplate="Data: %{x|%Y-%m-%d}<br>AQI (MM30): %{y:.1f}<extra></extra>"
        ))

        for thr in [40, 80, 120, 200, 400]:
            fig_aqi.add_hline(y=thr, line_dash="dash", line_color="#7f8c8d", opacity=0.6)

        for _, _, label, color in bands:
            fig_aqi.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=10, color=color),
                name=label, showlegend=True
            ))

        fig_aqi.update_layout(
            xaxis_title="Data",
            yaxis_title="AQI",
            legend_title_text="Faixas de qualidade",
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig_aqi, use_container_width=True)
    else:
        st.info("Sem dados de AQI para o período selecionado.")

    
    # -------------------------
    # Tendência diária (MM30) — múltiplas variáveis sobrepostas (normalizadas)
    # -------------------------
    st.subheader("📈 Tendência diária (MM30) — variáveis sobrepostas")
    if "data_dia" in dff.columns and not dff.empty:
        vars_default = [v for v in ["temp", "no2", "o3"] if v in dff.columns]
        vars_sel = st.multiselect(
            "Selecione variáveis para sobrepor (normalização min–máx por variável)",
            options=numeric_cols,
            default=vars_default,
            key="rio_ts_vars",
        )
        if vars_sel:
            ts = dff[["data_dia"] + vars_sel].dropna(how="all", subset=vars_sel).copy()
            ts = ts.sort_values("data_dia")

            long = ts.melt(id_vars=["data_dia"], value_vars=vars_sel,
                           var_name="variavel", value_name="valor").dropna()
            long = long.sort_values(["variavel","data_dia"])
            long["mm30"] = long.groupby("variavel")["valor"].transform(lambda s: s.rolling(30, min_periods=1).mean())

            def _minmax(s):
                lo, hi = s.min(), s.max()
                return (s - lo) / (hi - lo) if hi != lo else 0.5

            long["y"] = long.groupby("variavel")["mm30"].transform(_minmax)

            fig_ts = px.line(long, x="data_dia", y="y", color="variavel",
                             title=f"Tendência (MM30) — {'; '.join(vars_sel)} (escala normalizada)")
            fig_ts.update_layout(xaxis_title="Data", yaxis_title="Normalizado [0–1]",
                                 legend_title="Variável", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("Selecione ao menos uma variável.")
    else:
        st.info("Sem dados diários após o filtro.")

    # -------------------------
    # Sazonalidade — Heatmaps Ano x Mês (3 visões úteis)
    # -------------------------
    st.subheader("🔥 Sazonalidade (Ano x Mês)")

    if numeric_cols:
        c1, c2, c3 = st.columns([1.4, 1, 1])
        with c1:
            var_hm = st.selectbox(
                "Variável",
                options=[c for c in numeric_cols if c != "AQI"],
                index=0,
                key="rio_hm_var"
            )
        with c2:
            col_agg = st.selectbox("Agregação", options=["média", "soma", "máximo"], index=0, key="rio_hm_agg")
            
        show_labels = st.checkbox("Mostrar rótulos", value=True, key="rio_hm_labels")

        agg_map = {"média": "mean", "soma": "sum", "máximo": "max"}

        tabs = st.tabs(["Média/Total", "% no ano", "Anomalia vs. média do mês"])

        with tabs[0]:
            piv = _ym_pivot_agg(dff, var_hm, agg=agg_map[col_agg])
            if piv is None or piv.empty:
                st.info("Sem dados para construir o heatmap.")
            else:
                yyears = piv.index.tolist()[::-1]  
                fig = px.imshow(
                    piv.loc[yyears, _MONTH_ORDER].values,
                    x=_MONTH_LABELS,
                    y=[str(y) for y in yyears],
                    text_auto=show_labels,
                    aspect="auto",
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(
                    title=f"{var_hm} — {col_agg} por Ano x Mês",
                    margin=dict(l=20, r=20, t=40, b=20),
                    coloraxis_colorbar=dict(title=var_hm),
                )
                st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            piv = _ym_pivot_agg(dff, var_hm, agg="sum")  
            if piv is None or piv.empty:
                st.info("Sem dados para participação.")
            else:
                share = piv.div(piv.sum(axis=1).replace(0, np.nan), axis=0) * 100
                yyears = share.index.tolist()[::-1]
                fig = px.imshow(
                    share.loc[yyears, _MONTH_ORDER].values,
                    x=_MONTH_LABELS,
                    y=[str(y) for y in yyears],
                    text_auto=show_labels,
                    aspect="auto",
                    color_continuous_scale="Blues",
                )
                fig.update_layout(
                    title=f"{var_hm} — participação mensal dentro do ano (%)",
                    margin=dict(l=20, r=20, t=40, b=20),
                    coloraxis_colorbar=dict(title="% do ano"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with tabs[2]:
            piv = _ym_pivot_agg(dff, var_hm, agg=agg_map[col_agg])
            if piv is None or piv.empty:
                st.info("Sem dados para anomalia.")
            else:
                climatologia = piv.mean(axis=0) 
                anom = piv - climatologia  
                yyears = anom.index.tolist()[::-1]
                zmin = np.nanpercentile(anom.values, 5)
                zmax = np.nanpercentile(anom.values, 95)
                zmid = 0.0
                fig = px.imshow(
                    anom.loc[yyears, _MONTH_ORDER].values,
                    x=_MONTH_LABELS,
                    y=[str(y) for y in yyears],
                    text_auto=show_labels,
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=zmin, zmax=zmax,
                    color_continuous_midpoint=zmid,
                )
                fig.update_layout(
                    title=f"{var_hm} — anomalia em relação à média de cada mês",
                    margin=dict(l=20, r=20, t=40, b=20),
                    coloraxis_colorbar=dict(title="Desvio"),
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem variáveis numéricas para os heatmaps.")


    # -------------------------
    # Sazonalidade — Boxplot por mês
    # -------------------------
    st.subheader("📅 Sazonalidade mensal (boxplot)")
    if "mes" in dff.columns and numeric_cols:
        var_bx = st.selectbox("Variável", options=[c for c in numeric_cols if c != "AQI"], index=1, key="rio_bx_var")
        bx = dff[["mes", var_bx]].dropna()
        if not bx.empty:
            bx["mes_lbl"] = pd.Categorical(bx["mes"].map(dict(zip(_MONTH_ORDER, _MONTH_LABELS))),
                                           categories=_MONTH_LABELS, ordered=True)
            fig_bx = px.box(bx, x="mes_lbl", y=var_bx, title=f"{var_bx} — distribuição por mês")
            fig_bx.update_layout(xaxis_title="Mês", yaxis_title=var_bx, margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_bx, use_container_width=True)

    # -------------------------
    # Correlação entre variáveis
    # -------------------------
    st.subheader("🔗 Correlação entre variáveis")
    if numeric_cols:
        cols_corr = st.multiselect("Variáveis para correlação", options=numeric_cols,
                                   default=[c for c in ["temp","ur","chuva","no2","o3","pm2_5","pm10","AQI"] if c in numeric_cols],
                                   key="rio_corr_vars")
        if cols_corr:
            corr_df = dff[cols_corr].corr(method="pearson").round(2)
            fig_corr = px.imshow(
                corr_df.values,
                x=corr_df.columns, y=corr_df.columns,
                color_continuous_scale="RdBu", zmin=-1, zmax=1, text_auto=True,
                labels=dict(color="corr")
            )
            fig_corr.update_layout(title="Matriz de correlação (Pearson)", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Selecione ao menos duas variáveis.")
    else:
        st.info("Sem variáveis numéricas para correlação.")

    # -------------------------
    # Relação variável x variável (dispersão)
    # -------------------------
    st.subheader("🔁 Relação entre variáveis (dispersão)")

    num_cols = [c for c in ["chuva","temp","ur","co","no","no2","nox","so2","o3","pm10","pm2_5","AQI"] if c in dff.columns]
    if len(num_cols) >= 2:
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            x_var = st.selectbox(
                "Variável (eixo X)",
                options=num_cols,
                index=(num_cols.index("temp") if "temp" in num_cols else 0),
                key="rio_scatter_x"
            )
        with c2:
            y_var = st.selectbox(
                "Variável (eixo Y)",
                options=num_cols,
                index=(num_cols.index("ur") if "ur" in num_cols else (1 if len(num_cols) > 1 else 0)),
                key="rio_scatter_y"
            )
        with c3:
            add_trend = st.checkbox("Adicionar linha de tendência (OLS)", value=False, key="rio_scatter_trend")

        if x_var == y_var:
            st.info("Escolha variáveis diferentes para X e Y.")
        else:
            sc = dff[[x_var, y_var]].dropna()
            if not sc.empty:
                try:
                    fig_sc = px.scatter(
                        sc, x=x_var, y=y_var,
                        trendline=("ols" if add_trend else None),
                        title=f"{x_var} x {y_var}"
                    )
                except Exception:
                    fig_sc = px.scatter(sc, x=x_var, y=y_var, title=f"{x_var} x {y_var}")
                fig_sc.update_layout(xaxis_title=x_var, yaxis_title=y_var, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_sc, use_container_width=True)
            else:
                st.info("Sem dados suficientes para a dispersão após o filtro.")
    else:
        st.info("Variáveis numéricas insuficientes para a dispersão.")


    # -------------------------
    # Completude por variável
    # -------------------------
    st.subheader("🧪 Completude por variável (não nulos %)")
    if numeric_cols:
        pct = (1 - dff[numeric_cols].isna().mean()).mul(100).round(1)
        fig_pct = px.bar(pct.sort_values(ascending=False).reset_index().rename(columns={"index":"variavel",0:"pct"}),
                         x="variavel", y="pct", text_auto=".1f")
        fig_pct.update_layout(title="Completude de dados (%)", xaxis_title="", yaxis_title="%", margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_pct, use_container_width=True)

    # -------------------------
    # Top dias extremos (tabela) — variável escolhida
    # -------------------------
    st.subheader("🚩 Dias extremos")
    if numeric_cols:
        var_ext = st.selectbox("Variável para ranquear", options=[c for c in numeric_cols if c not in ["AQI"]], index=0, key="rio_ext_var")
        k = st.slider("Quantos dias mostrar", min_value=5, max_value=50, value=10, step=5, key="rio_ext_k")
        top = dff[["data_dia", var_ext]].dropna().nlargest(k, var_ext)
        st.dataframe(top.rename(columns={"data_dia":"Data", var_ext: var_ext}).reset_index(drop=True),
                     use_container_width=True)

    # -------------------------
    # Exportar CSV filtrado
    # -------------------------
    st.subheader("⬇️ Exportar dados filtrados")
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV filtrado", data=csv, file_name="rio_filtrado.csv", mime="text/csv")
