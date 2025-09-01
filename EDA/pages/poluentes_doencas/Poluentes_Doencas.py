# pages/poluentes_doencas/Poluentes_Doencas.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import pacf as pacf_vals_fn

# =========================
# Helpers
# =========================
def _ms_todos(label: str, options, current=None, key: str = None):
    """Multiselect com 'Todos'. Retorna lista de strings (ou lista completa se 'Todos')."""
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
    """Garante e retorna a coluna de data ('DT_INTER' ou 'data_formatada') como datetime64[ns]."""
    if "DT_INTER" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["DT_INTER"]):
            df["DT_INTER"] = pd.to_datetime(df["DT_INTER"], format="%Y%m%d", errors="coerce")
        return "DT_INTER"
    if "data_formatada" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["data_formatada"]):
            df["data_formatada"] = pd.to_datetime(df["data_formatada"], errors="coerce")
        return "data_formatada"
    return None

def _ensure_cid3(df: pd.DataFrame):
    """Gera CID_CAT3 (3 dígitos) se não existir; retorna o nome da coluna ('CID_CAT3' ou None)."""
    if "CID_CAT3" not in df.columns and "DIAG_PRINC" in df.columns:
        df["CID_CAT3"] = df["DIAG_PRINC"].astype(str).str[:3]
    return "CID_CAT3" if "CID_CAT3" in df.columns else None

# =========================
# Página
# =========================
def show(df_sus: pd.DataFrame, df_rio_treated: pd.DataFrame):
    st.title("📈 Poluentes x Doenças Respiratórias — Rio de Janeiro")

    with st.expander("ℹ️ Sobre esta página", expanded=False):
        st.markdown(
            """
            Cruzamos **internações por doenças respiratórias** (SUS) com **variáveis ambientais** (QualiAR).
            1) Você filtra o **SUS** (período, idade, CID-10, município);  
            2) Agregamos as **internações por dia**;  
            3) Unimos com a série ambiental diária (`data_dia`);  
            4) Exploramos **PACF**, **médias móveis** e **correlações** (lag 0 e por defasagens).
            """
        )

    # -------- Coerções iniciais (sem fragmentar) --------
    df_sus = df_sus.copy()
    df_env = df_rio_treated.copy()
    df_sus['DT_INTER'] = pd.to_datetime(df_sus['DT_INTER'], errors='coerce')
    date_col = _ensure_datetime_col(df_sus)  # 'DT_INTER' ou 'data_formatada'
    if date_col is None:
        st.error("Não encontrei a coluna de data de internação ('DT_INTER' ou 'data_formatada') no df_sus.")
        return

    # Série datetime coerçada (reuso)
    dt_sus = pd.to_datetime(df_sus[date_col], errors="coerce")

    if "data_dia" in df_env.columns and not pd.api.types.is_datetime64_any_dtype(df_env["data_dia"]):
        df_env["data_dia"] = pd.to_datetime(df_env["data_dia"], errors="coerce")

    if "IDADE" in df_sus.columns:
        df_sus["IDADE"] = pd.to_numeric(df_sus["IDADE"], errors="coerce")

    cid_col = _ensure_cid3(df_sus)

    # Limites para date_input (objetos date)
    if dt_sus.notna().any():
        min_d = dt_sus.min().date()
        max_d = dt_sus.max().date()
    else:
        min_d = max_d = None

    cid_opts = df_sus[cid_col].dropna().astype(str).unique().tolist() if cid_col else []
    munic_opts = df_sus["MUNIC_RES"].dropna().astype(str).unique().tolist() if "MUNIC_RES" in df_sus.columns else []

    # Estado dos filtros
    if "pxd_filters" not in st.session_state:
        st.session_state["pxd_filters"] = {
            "d_ini": min_d, "d_fim": max_d,
            "cids": list(map(str, cid_opts)),
            "munics": list(map(str, munic_opts)),
        }
    applied = st.session_state["pxd_filters"]

    # -------- Formulário --------
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

    # Atualiza estado
    st.session_state["pxd_filters"] = {
        "d_ini": d_ini_sel, "d_fim": d_fim_sel,
        "cids": sel_cid, "munics": sel_munic,
    }
    applied = st.session_state["pxd_filters"]

    # -------- Aplica filtros ao SUS --------
    mask = pd.Series(True, index=df_sus.index)

    if applied.get("d_ini") and applied.get("d_fim"):
        mask &= dt_sus.dt.date.between(applied["d_ini"], applied["d_fim"])

    if "IDADE" in df_sus.columns and (applied.get("idade_min") is not None) and (applied.get("idade_max") is not None):
        mask &= df_sus["IDADE"].between(applied["idade_min"], applied["idade_max"])

    if cid_col and applied.get("cids"):
        mask &= df_sus[cid_col].astype(str).isin(applied["cids"])

    if "MUNIC_RES" in df_sus.columns and applied.get("munics"):
        mask &= df_sus["MUNIC_RES"].astype(str).isin(applied["munics"])

    df_sus_filtrado = df_sus[mask].copy()
    st.caption(f"Após filtros: **{len(df_sus_filtrado):,}** registros SUS.".replace(",", "."))

    if df_sus_filtrado.empty:
        st.info("Nenhum registro após os filtros. Ajuste os critérios e tente novamente.")
        return

    # -------- Internações por dia + merge ambiental --------
    df_sus_filtrado["data_dia"] = pd.to_datetime(df_sus_filtrado[date_col], errors="coerce").dt.normalize()
    internacoes_dia = (
        df_sus_filtrado.groupby("data_dia")
        .size()
        .reset_index(name="internacoes")
        .sort_values("data_dia")
    )

    if "data_dia" not in df_env.columns:
        st.error("df_rio_treated não possui a coluna 'data_dia'. Verifique o carregamento.")
        return

    df_merged = pd.merge(internacoes_dia, df_env, on="data_dia", how="inner").sort_values("data_dia")

    # =========================
    # SESSÃO 1 — PACF e Médias Móveis
    # =========================
    st.header("🔁 Sessão 1 — Autocorrelação & persistência das internações")

    ts_int = internacoes_dia.copy()
    s = ts_int["internacoes"].astype(float)
    n_obs = int(s.notna().sum())
    max_lags = int(min(15, max(1, n_obs - 1)))

    st.subheader("📐 PACF — Autocorrelação Parcial (até 15 lags)")
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

    st.subheader("🧪 Médias móveis como preditoras (D+1 e D+7)")
    cols_mm = st.columns([1, 1])
    with cols_mm[0]:
        st.markdown("**Correlação fixa:** Spearman")
    with cols_mm[1]:
        show_annot_mm = st.checkbox("Mostrar rótulos", value=True, key="pxd_mm_ann_live")

    base = ts_int.copy()
    base["y_d1"] = base["internacoes"].shift(-1)
    base["y_d7"] = base["internacoes"].shift(-7)

    # Janela máxima = 15
    ks = list(range(1, 16))

    # Sem criar dezenas de colunas no DataFrame (evita fragmentação):
    res = {}
    for target in ["y_d1", "y_d7"]:
        vals = []
        for k in ks:
            mmk = base["internacoes"].rolling(k, min_periods=1).mean()  # série temporária
            dfv = pd.concat([mmk, base[target]], axis=1).dropna()
            if len(dfv) >= 5:
                # Spearman sempre
                r = dfv.iloc[:, 0].rank().corr(dfv.iloc[:, 1].rank())
            else:
                r = np.nan
            vals.append(r)
        res[target] = pd.Series(vals, index=ks)

    for target in ["y_d1", "y_d7"]:
        series = pd.Series(res[target]).dropna()
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
            title=f"Correlação (spearman) — MM(k=1..15) vs Internações {ttl}",
            xaxis_title="Janela k (dias)",
            yaxis_title="Correlação",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(figb, use_container_width=True)

    # =========================
    # SESSÃO 2 — Séries e correlação lag 0 (ambiente)
    # =========================
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
        # MM30 sem fragmentar: cria DataFrame auxiliar e concatena 1x
        df_mm = df_plot.set_index("data_dia")
        mm_dict = {"internacoes_mm30": df_mm["internacoes"].rolling("30D", min_periods=1).mean()}
        for v in vars_sel:
            mm_dict[f"{v}_mm30"] = df_mm[v].rolling("30D", min_periods=1).mean()
        df_mm = pd.concat(mm_dict, axis=1).reset_index()

        if use_z:
            # normaliza só as séries do eixo direito
            z_cols = [f"{v}_mm30" for v in vars_sel]
            z_df = df_mm[z_cols]
            mu = z_df.mean()
            sd = z_df.std(ddof=0).replace(0, 1.0)
            df_mm[z_cols] = (z_df - mu) / sd

        fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ts.add_trace(
            go.Scatter(x=df_mm["data_dia"], y=df_mm["internacoes_mm30"],
                       mode="lines", name="Internações (MM30)", line=dict(width=2, color="#2c3e50")),
            secondary_y=False
        )
        for v in vars_sel:
            fig_ts.add_trace(
                go.Scatter(x=df_mm["data_dia"], y=df_mm[f"{v}_mm30"],
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
    df_valid = df_merged.dropna(subset=["internacoes"]).copy()
    features = [c for c in df_valid.columns if c not in non_features]

    if features:
        if method0 == "spearman":
            Xr = df_valid[features].rank()
            yr = df_valid["internacoes"].rank()
            s0 = Xr.corrwith(yr, method="pearson")
        else:
            s0 = df_valid[features].corrwith(df_valid["internacoes"], method="pearson")

        s0 = s0.dropna().sort_values(key=lambda v: v.abs(), ascending=False)
        if not s0.empty:
            fig_corr = go.Figure(go.Bar(
                x=s0.index.tolist(), y=s0.values,
                marker=dict(color=s0.values, colorscale="RdBu", cmin=-1, cmax=1, showscale=True),
                text=[f"{v:.2f}" for v in s0.values],
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

    # =========================
    # SESSÃO 2.3 — Melhor janela + lag (Spearman) — PERFORMÁTICO
    # =========================
    st.subheader("🏁 Melhor janela + lag por variável (Spearman)")

    df = df_merged.copy()
    df["internacoes_d1"] = df["internacoes"].shift(-1)
    df["internacoes_d7"] = df["internacoes"].shift(-7)

    # Lista de candidatos (case-insensitive)
    pollutant_candidates = ['co','no','no2','nox','so2','o3','pm10','pm2_5','AQI','temp','chuva','ur']
    cols_lower_map = {c.lower(): c for c in df.columns}
    pollutants = [(v if v in df.columns else cols_lower_map.get(v.lower())) for v in pollutant_candidates]
    pollutants = [v for v in dict.fromkeys(pollutants) if v is not None]

    # Numéricos somente onde precisamos
    for c in pollutants + ["internacoes_d1", "internacoes_d7"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    janelas = [3, 7, 14, 21, 30, 60, 90, 120, 150]
    shifts = range(0, 16)  # 0..15

    # Em vez de criar dezenas de colunas mm e mais dezenas shiftadas (que fragmenta),
    # calculamos on-the-fly e NUNCA inserimos no df principal:
    results = []
    for tgt in ["internacoes_d1", "internacoes_d7"]:
        if tgt not in df.columns:
            continue
        y = df[tgt]
        for var in pollutants:
            if var not in df.columns:
                continue
            s = df[var]
            for w in janelas:
                mm = s.rolling(window=w, min_periods=w).mean()
                for k in shifts:
                    x = mm.shift(k)
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
