import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import pacf as pacf_vals_fn

# -------------------------
# Helpers
# -------------------------
def _ms_todos(label: str, options, current=None, key: str = None):
    """Multiselect com 'Todos'. Retorna lista de strings."""
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

def _ensure_datetime_col(df: pd.DataFrame):
    """Retorna nome da coluna de data existente e convertida para datetime ('DT_INTER' ou 'data_formatada')."""
    if "DT_INTER" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["DT_INTER"]):
            df["DT_INTER"] = pd.to_datetime(df["DT_INTER"], format="%Y%m%d", errors="coerce")
        return "DT_INTER"
    elif "data_formatada" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["data_formatada"]):
            df["data_formatada"] = pd.to_datetime(df["data_formatada"], errors="coerce")
        return "data_formatada"
    else:
        return None

def _ensure_cid3(df: pd.DataFrame):
    """Gera coluna CID_CAT3 (3 dígitos da DIAG_PRINC) se não existir."""
    if "CID_CAT3" not in df.columns and "DIAG_PRINC" in df.columns:
        df["CID_CAT3"] = df["DIAG_PRINC"].astype(str).str[:3]
    return "CID_CAT3" if "CID_CAT3" in df.columns else None

def _crosscorr_table(x: pd.Series, y: pd.Series, max_lag: int = 60) -> pd.DataFrame:
    """
    Retorna DataFrame com correlação de Pearson para lags de -max_lag a +max_lag.
    Definição: corr(lag) = corr( x , y.shift(lag) ).
      • lag > 0  → o poluente "antecede" internações (efeito antecedente)
      • lag < 0  → o poluente "segue" internações
    """
    x = x.copy().astype(float)
    y = y.copy().astype(float)
    out = []
    for lag in range(-max_lag, max_lag + 1):
        r = x.corr(y.shift(lag))
        out.append((lag, r))
    dfcc = pd.DataFrame(out, columns=["lag", "corr"]).dropna()
    return dfcc

def show(df_sus: pd.DataFrame, df_rio_treated: pd.DataFrame):
    st.title("📈 Poluentes x Doenças Respiratórias — Rio de Janeiro")

    with st.expander("ℹ️ Sobre esta página", expanded=False):
        st.markdown(
            """
            Esta página cruza **internações por doenças respiratórias** (SUS) com as **variáveis ambientais** (QualiAR) do Rio:

            1. Você escolhe os **filtros** (período, idade, CID-10 em 3 dígitos, município).  
            2. Agregamos as **internações por dia**.  
            3. Unimos com a série diária ambiental (`data_dia`).  
            4. Exploramos correlações em duas frentes:
               - **Sessão 1:** a série de internações com ela mesma (persistência), via **PACF** e **médias móveis** (janelas deslizantes).  
               - **Sessão 2:** internações x **variáveis ambientais** (séries e correlações de referência).
            """
        )

    df_sus = df_sus.copy()
    df_env = df_rio_treated.copy()

    date_col = _ensure_datetime_col(df_sus)  # 'DT_INTER' ou 'data_formatada'
    if "data_dia" in df_env.columns and not pd.api.types.is_datetime64_any_dtype(df_env["data_dia"]):
        df_env["data_dia"] = pd.to_datetime(df_env["data_dia"], errors="coerce")
    if "IDADE" in df_sus.columns:
        df_sus["IDADE"] = pd.to_numeric(df_sus["IDADE"], errors="coerce")
    cid_col = _ensure_cid3(df_sus)  

    if date_col and df_sus[date_col].notna().any():
        min_d = df_sus[date_col].min().date()
        max_d = df_sus[date_col].max().date()
    else:
        min_d = max_d = None

    if "IDADE" in df_sus.columns:
        age_min = int(np.nanmin(df_sus["IDADE"])) if df_sus["IDADE"].notna().any() else 0
        age_max = int(np.nanmax(df_sus["IDADE"])) if df_sus["IDADE"].notna().any() else 100
    else:
        age_min, age_max = 0, 100

    cid_opts = df_sus[cid_col].dropna().astype(str).unique().tolist() if cid_col else []

    munic_opts = df_sus["MUNIC_RES"].dropna().astype(str).unique().tolist() if "MUNIC_RES" in df_sus.columns else []

    if "pxd_filters" not in st.session_state:
        st.session_state["pxd_filters"] = {
            "d_ini": min_d, "d_fim": max_d,
            "idade_min": age_min, "idade_max": age_max,
            "cids": list(map(str, cid_opts)),
            "munics": list(map(str, munic_opts)),
        }
    applied = st.session_state["pxd_filters"]

    # -------------------------
    # Formulário de filtros 
    # -------------------------
    st.header("🔎 Filtros de internações (SUS)")
    with st.form("form_poluentes_doencas"):
        c1, c2 = st.columns(2)
        with c1:
            if min_d and max_d:
                d_ini = applied.get("d_ini") or min_d
                d_fim = applied.get("d_fim") or max_d
                d_ini_sel, d_fim_sel = st.date_input(
                    "Período de internação",
                    value=(d_ini, d_fim),
                    min_value=min_d, max_value=max_d,
                    key="pxd_periodo",
                )
            else:
                d_ini_sel, d_fim_sel = None, None

            if "IDADE" in df_sus.columns:
                idade_min_sel, idade_max_sel = st.slider(
                    "Faixa etária (anos)",
                    min_value=int(age_min), max_value=int(age_max),
                    value=(int(applied.get("idade_min", age_min)), int(applied.get("idade_max", age_max))),
                    step=1, key="pxd_idade"
                )
            else:
                idade_min_sel, idade_max_sel = None, None

        with c2:
            sel_cid = _ms_todos(
                "CID-10 (3 dígitos)",
                cid_opts,
                current=applied.get("cids", cid_opts),
                key="pxd_cid3"
            )
            sel_munic = _ms_todos(
                "Município de residência",
                munic_opts,
                current=applied.get("munics", munic_opts),
                key="pxd_munic"
            )

        st.form_submit_button("Filtrar")

    st.session_state["pxd_filters"] = {
        "d_ini": d_ini_sel, "d_fim": d_fim_sel,
        "idade_min": idade_min_sel, "idade_max": idade_max_sel,
        "cids": sel_cid, "munics": sel_munic,
    }
    applied = st.session_state["pxd_filters"]

    # -------------------------
    # Aplicação dos filtros ao df_sus
    # -------------------------
    if date_col is None:
        st.error("Não encontrei a coluna de data de internação ('DT_INTER' ou 'data_formatada') no df_sus.")
        return

    mask = pd.Series(True, index=df_sus.index)

    if applied.get("d_ini") and applied.get("d_fim"):
        mask &= df_sus[date_col].dt.date.between(applied["d_ini"], applied["d_fim"])

    if "IDADE" in df_sus.columns and applied.get("idade_min") is not None and applied.get("idade_max") is not None:
        mask &= df_sus["IDADE"].between(applied["idade_min"], applied["idade_max"])

    if cid_col and applied.get("cids"):
        mask &= df_sus[cid_col].astype(str).isin(applied["cids"])

    if "MUNIC_RES" in df_sus.columns and applied.get("munics"):
        mask &= df_sus["MUNIC_RES"].astype(str).isin(applied["munics"])

    df_sus_filtrado = df_sus[mask].copy()
    st.caption(f"Após filtros: **{len(df_sus_filtrado):,}** registros SUS.".replace(",", "."))

    # -------------------------
    # Internações por dia e merge com o ambiental
    # -------------------------
    if df_sus_filtrado.empty:
        st.info("Nenhum registro após os filtros. Ajuste os critérios e tente novamente.")
        return

    df_sus_filtrado["data_dia"] = df_sus_filtrado[date_col].dt.normalize()
    internacoes_dia = (df_sus_filtrado.groupby("data_dia").size()
                       .reset_index(name="internacoes"))

    if "data_dia" not in df_env.columns:
        st.error("df_rio_treated não possui a coluna 'data_dia'. Verifique o carregamento.")
        return

    df_merged = pd.merge(internacoes_dia, df_env, on="data_dia", how="inner").sort_values("data_dia")

    # -------------------------
    # Prévia
    # -------------------------
    st.subheader("🧾 Prévia do dataset unido (internações x ambiente)")
    st.dataframe(df_merged.head(), use_container_width=True)

    # =========================================================
    # SESSÃO 1 — Autocorrelação & Persistência das internações
    # =========================================================
    st.header("🔁 Sessão 1 — Autocorrelação & persistência das internações")

    ts_int = internacoes_dia.sort_values("data_dia").reset_index(drop=True)
    s = ts_int["internacoes"].astype(float)
    n_obs = int(s.notna().sum())
    max_lags = int(min(30, max(1, n_obs - 1)))

    st.subheader("📐 PACF — Autocorrelação Parcial (até 30 lags)")
    if n_obs >= 10 and max_lags >= 1:
        pacf_arr = pacf_vals_fn(s.values, nlags=max_lags, method="ywm")
        x_lags = np.arange(1, max_lags + 1)
        y_vals = pacf_arr[1:] 

        bound = 1.96 / np.sqrt(n_obs)  

        fig_pacf = go.Figure()
        fig_pacf.add_hrect(y0=-bound, y1=bound, line_width=0, fillcolor="#95a5a6", opacity=0.2, layer="below")
        fig_pacf.add_hline(y=0, line_color="#7f8c8d", line_width=1)
        fig_pacf.add_trace(go.Bar(
            x=x_lags, y=y_vals,
            marker=dict(color=y_vals, colorscale="RdBu", cmin=-1, cmax=1),
            text=[f"{v:.2f}" for v in y_vals],
            textposition="outside",
            name="PACF",
        ))
        fig_pacf.update_layout(
            title=f"PACF — Internações (n={n_obs}, lags=1..{max_lags})",
            xaxis_title="Lag",
            yaxis_title="PACF",
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False,
            yaxis=dict(range=[-1.15, 1.15]),
        )
        st.plotly_chart(fig_pacf, use_container_width=True)

        top_lags = (pd.Series(y_vals, index=x_lags).abs().sort_values(ascending=False).head(3))
        st.caption("Maiores |PACF|: " + ", ".join([f"lag {int(i)} ({v:.2f})" for i, v in top_lags.items()]))
    else:
        st.info("Série insuficiente para PACF (mín. ~10 observações).")

    st.markdown(
        "> A série de internações tem **alta persistência** e **padrão semanal**; a **média móvel** resume o comportamento recente "
        "sem usar informação do futuro (**sem vazamento**). Isso ajuda a identificar **qual janela** (3, 7, 14… dias) melhor resume "
        "a dinâmica para **prever** D+1 e D+7, servindo de baseline e guiando a **engenharia de atributos**."
    )

    st.subheader("🧪 Médias móveis como preditoras (D+1 e D+7)")
    cols_mm = st.columns([1, 1])
    with cols_mm[0]:
        corr_method_mm = st.selectbox("Correlação (MM x futuro)", options=["spearman", "pearson"], index=0, key="pxd_mm_corrm_live")
    with cols_mm[1]:
        show_annot_mm = st.checkbox("Mostrar rótulos", value=True, key="pxd_mm_ann_live")

    base = ts_int.copy()
    base["y_d1"] = base["internacoes"].shift(-1)
    base["y_d7"] = base["internacoes"].shift(-7)
    ks = list(range(1, 31))
    for k in ks:
        base[f"mm{k}"] = base["internacoes"].rolling(k, min_periods=1).mean()

    res = {}
    for target in ["y_d1", "y_d7"]:
        vals = []
        for k in ks:
            col = f"mm{k}"
            dfv = base[[col, target]].dropna()
            if len(dfv) >= 5:
                if corr_method_mm == "spearman":
                    r = dfv[col].rank().corr(dfv[target].rank())
                else:
                    r = dfv[col].corr(dfv[target])
            else:
                r = np.nan
            vals.append(r)
        res[target] = pd.Series(vals, index=ks)

    for target in ["y_d1", "y_d7"]:
        series = res[target].dropna()
        if series.empty:
            st.info(f"Dados insuficientes para correlação ({'D+1' if target=='y_d1' else 'D+7'}).")
            continue
        x = [str(k) for k in series.index]
        y = series.values
        figb = go.Figure(go.Bar(
            x=x, y=y,
            marker=dict(color=y, colorscale="RdBu", cmin=-1, cmax=1, showscale=True),
            text=[f"{v:.2f}" for v in y] if show_annot_mm else None,
            textposition="outside" if show_annot_mm else "none"
        ))
        ttl = "D+1" if target == "y_d1" else "D+7"
        figb.add_hline(y=0, line_dash="dash", line_color="#7f8c8d")
        figb.update_layout(
            title=f"Correlação ({corr_method_mm}) — MM(k=1..30) vs Internações {ttl}",
            xaxis_title="Janela k (dias)",
            yaxis_title="Correlação",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(figb, use_container_width=True)

    st.subheader("📈 Correlação rolante — MM(k) x Internações futuras")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        k_sel = st.selectbox("Janela MM(k)", options=[3, 7, 14, 21, 30], index=2, key="pxd_mm_k_live")
    with c2:
        h_sel = st.selectbox("Horizonte (dias à frente)", options=[1, 7], index=0, key="pxd_mm_h_live")
    with c3:
        win = st.slider("Janela rolante (dias)", min_value=30, max_value=180, value=90, step=10, key="pxd_mm_win_live")
    with c4:
        roll_method = st.selectbox("Correlação rolante", options=["spearman", "pearson"], index=0, key="pxd_mm_roll_live")

    base = ts_int.copy()
    base["mm"] = base["internacoes"].rolling(k_sel, min_periods=1).mean()
    base["y_future"] = base["internacoes"].shift(-h_sel)
    dfv = base[["data_dia", "mm", "y_future"]].dropna().set_index("data_dia").sort_index()

    if not dfv.empty:
        if roll_method == "spearman":
            def _roll_spearman(a: pd.Series, b: pd.Series, w: int) -> pd.Series:
                out = []
                idx = a.index
                av = a.values; bv = b.values
                for i in range(len(a)):
                    i0 = max(0, i - w + 1)
                    aa = av[i0:i+1]; bb = bv[i0:i+1]
                    if len(aa) >= max(10, w//2):
                        ra = pd.Series(aa).rank().values
                        rb = pd.Series(bb).rank().values
                        out.append(pd.Series(ra).corr(pd.Series(rb)))
                    else:
                        out.append(np.nan)
                return pd.Series(out, index=idx)
            roll = _roll_spearman(dfv["mm"], dfv["y_future"], win)
        else:
            roll = dfv["mm"].rolling(window=win, min_periods=max(10, win // 2)).corr(dfv["y_future"])

        figr = go.Figure()
        figr.add_trace(go.Scatter(x=roll.index, y=roll.values, mode="lines", name="corr rolante"))
        figr.add_hline(y=0, line_dash="dash", line_color="#7f8c8d")
        figr.update_layout(
            title=f"Correlação rolante ({roll_method}) — MM({k_sel}) x D+{h_sel} (janela={win}d)",
            xaxis_title="Data",
            yaxis_title="Correlação",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(figr, use_container_width=True)
    else:
        st.info("Série insuficiente para correlação rolante.")

    # =========================================================
    # SESSÃO 2 — Internações x Variáveis ambientais
    # =========================================================
    st.header("🌫️ Sessão 2 — Internações x variáveis ambientais")

    st.subheader("🧭 Série temporal: Internações x variáveis ambientais (MM30)")
    non_features = {"data_dia", "internacoes", "ano", "mes", "dia", "Qualidade_do_Ar"}
    env_cols = [c for c in df_merged.columns
                if c not in non_features and pd.api.types.is_numeric_dtype(df_merged[c])]

    default_vars = [v for v in ["temp", "no2", "o3"] if v in env_cols]
    c1, c2 = st.columns([1.5, 1])
    with c1:
        vars_sel = st.multiselect(
            "Variáveis ambientais (eixo direito)",
            options=env_cols,
            default=(default_vars if default_vars else env_cols[:2]),
            key="pxd_ts_vars"
        )
    with c2:
        use_z = st.checkbox("Normalizar (z-score) no eixo direito", value=True, key="pxd_ts_norm")

    df_plot = df_merged[["data_dia", "internacoes"] + (vars_sel if vars_sel else [])] \
        .dropna(subset=["data_dia"]).sort_values("data_dia")

    if vars_sel and not df_plot.empty:
        # MM30
        df_mm = df_plot.set_index("data_dia")
        cols_right = vars_sel.copy()
        cols_all = ["internacoes"] + cols_right
        for c in cols_all:
            if c in df_mm.columns:
                df_mm[f"{c}_mm30"] = df_mm[c].rolling("30D", min_periods=1).mean()
        df_mm = df_mm.reset_index()

        df_plot_norm = df_mm.copy()
        if use_z:
            for v in cols_right:
                col = f"{v}_mm30"
                mu = df_plot_norm[col].mean()
                sd = df_plot_norm[col].std(ddof=0)
                df_plot_norm[col] = (df_plot_norm[col] - mu) / (sd if sd not in (0, np.nan) else 1.0)

        fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ts.add_trace(
            go.Scatter(x=df_plot_norm["data_dia"], y=df_plot_norm["internacoes_mm30"],
                       mode="lines", name="Internações (MM30)", line=dict(width=2, color="#2c3e50")),
            secondary_y=False
        )
        for v in cols_right:
            fig_ts.add_trace(
                go.Scatter(x=df_plot_norm["data_dia"], y=df_plot_norm[f"{v}_mm30"],
                           mode="lines", name=f"{v} (MM30)"),
                secondary_y=True
            )
        fig_ts.update_layout(
            title=f"Internações (MM30) x {'; '.join(vars_sel)} (MM30)",
            margin=dict(l=20, r=20, t=40, b=20),
            legend_title_text="Séries"
        )
        fig_ts.update_xaxes(title_text="Data")
        fig_ts.update_yaxes(title_text="Internações/dia (MM30)", secondary_y=False)
        fig_ts.update_yaxes(title_text=("Z-score (MM30)" if use_z else "Valor (MM30)"), secondary_y=True)
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Selecione ao menos uma variável ambiental para o eixo direito.")

    st.subheader("📊 Correlação lag 0 — Internações x variáveis ambientais (toda a série)")

    method0 = st.selectbox("Método", options=["spearman", "pearson"], index=0, key="pxd_lag0_m")
    # alinhamento e limpeza
    df_valid = df_merged.dropna(subset=["internacoes"]).copy()
    features = [c for c in df_valid.columns if c not in non_features]

    if features:
        if method0 == "spearman":
            Xr = df_valid[features].rank()
            yr = df_valid["internacoes"].rank()
            s = Xr.corrwith(yr, method="pearson")
        else:
            s = df_valid[features].corrwith(df_valid["internacoes"], method="pearson")

        s = s.dropna().sort_values(key=lambda v: v.abs(), ascending=False)

        if not s.empty:
            fig_corr = go.Figure(go.Bar(
                x=s.index.tolist(), y=s.values,
                marker=dict(color=s.values, colorscale="RdBu", cmin=-1, cmax=1, showscale=True),
                text=[f"{v:.2f}" for v in s.values],
                textposition="outside"
            ))
            fig_corr.add_hline(y=0, line_dash="dash", line_color="#7f8c8d")
            fig_corr.update_layout(
                title=f"Correlação (lag 0, método={method0}) — Internações x variáveis",
                xaxis_title="Variáveis ambientais",
                yaxis_title="Correlação",
                margin=dict(l=20, r=20, t=50, b=20),
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Sem colunas numéricas válidas para a correlação.")
    else:
        st.info("Nenhuma variável ambiental disponível para correlação.")
        
    # --------------------------------------------
    # 2.3) Melhor janela + lag por variável (Spearman)
    # --------------------------------------------
    st.subheader("🏁 Melhor janela + lag por variável (Spearman)")

    df = df_merged.copy()

    df["internacoes_d1"] = df["internacoes"].shift(-1)
    df["internacoes_d7"] = df["internacoes"].shift(-7)

    pollutant_candidates = ['co','no','no2','nox','so2','o3','pm10','pm2_5','AQI','temp','chuva','ur']

    cols_lower_map = {c.lower(): c for c in df.columns}
    pollutants = [(v if v in df.columns else cols_lower_map.get(v.lower())) for v in pollutant_candidates]
    pollutants = [v for v in dict.fromkeys(pollutants) if v is not None]  

    for c in pollutants + ["internacoes_d1", "internacoes_d7"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    janelas = [3, 7, 14, 21, 30, 60, 90, 120, 150]
    shifts = list(range(0, 16))  # 0..15

    for var in pollutants:
        if var not in df.columns:
            continue
        s = df[var]
        for w in janelas:
            df[f"{var}_mm{w}"] = s.rolling(window=w, min_periods=w).mean()

    results = []
    for tgt in ["internacoes_d1", "internacoes_d7"]:
        if tgt not in df.columns:
            continue
        for var in pollutants:
            for w in janelas:
                base_col = f"{var}_mm{w}"
                if base_col not in df.columns:
                    continue
                for k in shifts:
                    x = df[base_col].shift(k)
                    y = df[tgt]
                    sub = pd.concat([x, y], axis=1).dropna()
                    if len(sub) >= 5:
                        corr = sub.corr(method="spearman").iloc[0, 1]
                        results.append({"target": tgt, "variavel": var, "janela": w, "shift": k, "spearman": corr})

    res = pd.DataFrame(results)

    if res.empty:
        st.info("Sem resultados para as combinações avaliadas (verifique período/variáveis).")
    else:
        best_per_var = (
            res.assign(abs_s=res["spearman"].abs())
            .sort_values(["target", "variavel", "abs_s"], ascending=[True, True, False])
            .groupby(["target", "variavel"], as_index=False)
            .first()
            .drop(columns="abs_s")
        )

        for tgt, titulo in [("internacoes_d1", "Internações D+1"), ("internacoes_d7", "Internações D+7")]:
            df_t = best_per_var[best_per_var["target"] == tgt].copy()
            if df_t.empty:
                st.info(f"Sem resultados para {titulo}.")
                continue

            df_t = df_t.sort_values("spearman", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)
            df_t["label"] = df_t.apply(lambda r: f"{r['variavel']}<br>MM{int(r['janela'])} | k={int(r['shift'])}", axis=1)

            fig_best = go.Figure(go.Bar(
                x=df_t["label"],
                y=df_t["spearman"],
                marker=dict(color=df_t["spearman"], colorscale="RdBu", cmin=-1, cmax=1, showscale=True),
                text=[f"{v:.2f}" for v in df_t["spearman"]],
                textposition="outside"
            ))
            fig_best.add_hline(y=0, line_dash="dash", line_color="#7f8c8d")
            fig_best.update_layout(
                title=f"Melhor janela + lag por variável — Spearman ({titulo})",
                xaxis_title="Variável | Melhor (MM, lag)",
                yaxis_title="Correlação",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            fig_best.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_best, use_container_width=True)

        with st.expander("📋 Tabela — melhores combinações por variável", expanded=False):
            tbl = best_per_var.copy()
            tbl["abs_s"] = pd.to_numeric(tbl["spearman"], errors="coerce").abs()
            tbl = tbl.sort_values(["target", "abs_s"], ascending=[True, False]).drop(columns="abs_s")
            st.dataframe(tbl.reset_index(drop=True), use_container_width=True)
    
    # =========================================================
    # SESSÃO 3 — Curvas de correlação por lag (CCF)
    # =========================================================
    st.header("🔀 Sessão 3 — Curvas de correlação por lag (CCF)")

    non_features = {"data_dia", "internacoes", "ano", "mes", "dia", "Qualidade_do_Ar"}
    env_cols_all = [c for c in df_merged.columns
                    if c not in non_features and pd.api.types.is_numeric_dtype(df_merged[c])]

    if env_cols_all:
        c1, c2 = st.columns([2, 1])
        with c1:
            vars_ccf = st.multiselect(
                "Variáveis para analisar (até 5)",
                options=env_cols_all,
                default=[v for v in ["no2", "o3", "pm2_5"] if v in env_cols_all][:3],
                key="pxd_ccf_vars"
            )
        with c2:
            max_lag = st.slider("Lags (±)", min_value=5, max_value=30, value=15, step=1, key="pxd_ccf_lags")

        if vars_ccf:
            fig_ccf = go.Figure()
            n_eff = int(df_merged["internacoes"].notna().sum())
            bound = (1.96 / np.sqrt(n_eff)) if n_eff > 0 else None

            for v in vars_ccf[:5]:
                x = df_merged[v].astype(float)
                y = df_merged["internacoes"].astype(float)
                dfcc = _crosscorr_table(x, y, max_lag=max_lag) 
                fig_ccf.add_trace(go.Scatter(x=dfcc["lag"], y=dfcc["corr"], mode="lines+markers", name=v))

            fig_ccf.add_vline(x=0, line_dash="dash", line_color="#7f8c8d")
            if bound is not None and np.isfinite(bound):
                fig_ccf.add_hrect(y0=-bound, y1=bound, line_width=0, fillcolor="#95a5a6", opacity=0.15, layer="below")

            fig_ccf.update_layout(
                title="Correlação por lag — positivo: variável antecede internações",
                xaxis_title="Lag (dias) — corr( X(t), Y(t+lag) )",
                yaxis_title="Correlação (Pearson)",
                margin=dict(l=20, r=20, t=50, b=20),
                legend_title_text="Variável"
            )
            st.plotly_chart(fig_ccf, use_container_width=True)
        else:
            st.info("Selecione ao menos uma variável para traçar as curvas de correlação por lag.")
    else:
        st.info("Não há variáveis numéricas ambientais para esta análise.")
