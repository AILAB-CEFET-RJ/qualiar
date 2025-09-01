import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def _kpi(num):
    try:
        return f"{int(num):,}".replace(",", ".")
    except Exception:
        return "-"

_MONTH_ORDER = list(range(1, 13))
_MONTH_LABELS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

def _heatmap_counts(df: pd.DataFrame, title: str, show_text: bool = True):
    hm = df.groupby(["ANO","MES"]).size().reset_index(name="qtd")
    if hm.empty:
        st.info("Sem dados suficientes para o heatmap.")
        return
    mat = (hm.pivot(index="ANO", columns="MES", values="qtd")
             .reindex(columns=_MONTH_ORDER)
             .fillna(0)
             .astype(int))
    fig = px.imshow(
        mat.values,
        labels=dict(x="Mês", y="Ano", color="Internações"),
        x=_MONTH_LABELS,
        y=mat.index.astype(str).tolist()[::-1],
        aspect="auto",
        color_continuous_scale="Blues",
        text_auto=True if show_text else False,
    )
    fig.update_layout(title=title, margin=dict(l=20,r=20,t=40,b=20))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def _heatmap_share(df: pd.DataFrame, title: str, show_text: bool = True):
    hm = df.groupby(["ANO","MES"]).size().reset_index(name="qtd")
    if hm.empty:
        st.info("Sem dados suficientes para o heatmap de participação.")
        return
    mat = (hm.pivot(index="ANO", columns="MES", values="qtd")
             .reindex(columns=_MONTH_ORDER)
             .fillna(0))
    row_sums = mat.sum(axis=1).replace(0, np.nan)
    share = (mat.div(row_sums, axis=0) * 100).round(1)
    fig = px.imshow(
        share.values,
        labels=dict(x="Mês", y="Ano", color="% no ano"),
        x=_MONTH_LABELS,
        y=share.index.astype(str).tolist()[::-1],
        aspect="auto",
        color_continuous_scale="Viridis",
        text_auto=True if show_text else False,
    )
    fig.update_layout(title=title, margin=dict(l=20,r=20,t=40,b=20))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def _ms_todos_form(label: str, options, current=None, key: str = None):
    """Renderiza multiselect com 'Todos'. Retorna SEMPRE a lista final (strings).
    - options: lista de opções originais (de qualquer tipo)
    - current: seleção aplicada anteriormente (para manter o estado visual)
    """
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

def show(df_sus: pd.DataFrame):
    st.title("🩺 SIH/SUS — Internações por Doenças Respiratórias (RJ)")

    with st.expander("ℹ️ Sobre os dados", expanded=False):
        st.markdown(
            """
            **Fonte:** SIH/SUS (AIH), registros de internações **por doenças respiratórias (CID-10 J00-J99)** no município do **Rio de Janeiro**.
            
            **Unidade de análise:** cada linha é **uma internação** (AIH).  
            **Campos-chave esperados:** `DT_INTER`, `DT_SAIDA`, `IDADE`, `SEXO` (e/ou `SEXO_TXT`), `DIAG_PRINC`, `DIAS_PERM`, `MORTE`, além das derivadas `ANO`, `MES`, `ANO_MES`, `DIA_SEMANA`, `SEMANA_ANO`, `FAIXA_ETARIA`, `CID_CAT3`, `CID_GRUPO_J`.
            """
        )

    df = df_sus
    
    st.sidebar.header("🔎 Filtros")

    sexo_col = "SEXO_TXT" if "SEXO_TXT" in df.columns else ("SEXO" if "SEXO" in df.columns else None)
    hosp_col = "HOSPITAL" if "HOSPITAL" in df.columns else ("CNES" if "CNES" in df.columns else None)

    min_date = max_date = None
    dt_inter = None 
    if "DT_INTER" in df.columns:
        dt_inter = pd.to_datetime(df["DT_INTER"], errors="coerce") 
        dates = dt_inter.dropna()                                  
        if not dates.empty:
            min_date = dates.min()
            max_date = dates.max()


    sexo_opts  = df[sexo_col].dropna().unique().tolist() if sexo_col else []
    munic_opts = df["MUNIC_RES"].dropna().astype(str).unique().tolist() if "MUNIC_RES" in df.columns else []
    faixa_opts = df["FAIXA_ETARIA"].dropna().unique().tolist() if "FAIXA_ETARIA" in df.columns else []
    grupo_opts = df["CID_GRUPO_J"].dropna().unique().tolist() if "CID_GRUPO_J" in df.columns else []
    hosp_opts  = df[hosp_col].dropna().astype(str).unique().tolist() if hosp_col else []

    if "CID_CAT3" in df.columns:
        cid_all_opts = df["CID_CAT3"].dropna().astype(str).unique().tolist()
    elif "DIAG_PRINC" in df.columns:
        cid_all_opts = df["DIAG_PRINC"].dropna().astype(str).str[:3].unique().tolist()
    else:
        cid_all_opts = []
    
    if "sus_filters" not in st.session_state:
        st.session_state["sus_filters"] = {
        "d_ini": min_date,
        "d_fim": max_date,
        "sexo":  list(map(str, sexo_opts)),
        "faixa": list(map(str, faixa_opts)),
        "grupo": list(map(str, grupo_opts)),
        "hosp":  list(map(str, hosp_opts)),
        "cid3":  list(map(str, cid_all_opts)),   
        "municipios": list(map(str, munic_opts)),
    }

    applied = st.session_state["sus_filters"]

    with st.sidebar.form("form_filtros_sus"):
        if min_date is not None and max_date is not None:
            d_ini_sel, d_fim_sel = st.date_input(
                "Período de internação",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
                key="ms_periodo",
            )
        else:
            d_ini_sel = applied.get("d_ini")
            d_fim_sel = applied.get("d_fim")

        sel_sexo = _ms_todos_form("Sexo", sexo_opts, current=applied["sexo"], key="ms_sexo") if sexo_col else []

        sel_faixa = _ms_todos_form("Faixa etária", faixa_opts, current=applied["faixa"], key="ms_faixa") if len(faixa_opts) else []

        sel_munic = _ms_todos_form(
            "Município de residência",
            munic_opts,
            current=applied.get("municipios", munic_opts),
            key="ms_munic"
        )
        
        sel_grupo = _ms_todos_form("Grupo CID-10 (J00–J99)", grupo_opts, current=applied["grupo"], key="ms_grupo") if len(grupo_opts) else []

        if "CID_CAT3" in df.columns:
            if sel_grupo: 
                base_cid = df[df["CID_GRUPO_J"].astype(str).isin(sel_grupo)]
            else:
                base_cid = df
            cid_opts_dyn = base_cid["CID_CAT3"].dropna().astype(str).unique().tolist()
        elif "DIAG_PRINC" in df.columns:
            base_cid = df[df["CID_GRUPO_J"].astype(str).isin(sel_grupo)] if "CID_GRUPO_J" in df.columns else df
            cid_opts_dyn = base_cid["DIAG_PRINC"].dropna().astype(str).str[:3].unique().tolist()
        else:
            cid_opts_dyn = []

        sel_cid3 = _ms_todos_form(
            "CID-10 (3 dígitos)",
            cid_opts_dyn,
            current=applied.get("cid3", cid_all_opts),
            key="ms_cid3"
        )

        sel_hosp = _ms_todos_form("Hospital", hosp_opts, current=applied["hosp"], key="ms_hosp") if hosp_col and len(hosp_opts) else []

        submitted = st.form_submit_button("Filtrar")

    if submitted:
        st.session_state["sus_filters"] = {
            "d_ini": d_ini_sel,
            "d_fim": d_fim_sel,
            "sexo":  sel_sexo,
            "faixa": sel_faixa,
            "grupo": sel_grupo,
            "hosp":  sel_hosp,
            "cid3":  sel_cid3,  
            "municipios": sel_munic,
        }
    applied = st.session_state["sus_filters"] 

    mask = pd.Series(True, index=df.index)
    if (dt_inter is not None) and (d_ini_sel and d_fim_sel):
        mask &= dt_inter.dt.date.between(d_ini_sel, d_fim_sel)
    if sexo_col and applied["sexo"]:
        mask &= df[sexo_col].astype(str).isin(applied["sexo"])
    if "FAIXA_ETARIA" in df.columns and applied["faixa"]:
        mask &= df["FAIXA_ETARIA"].astype(str).isin(applied["faixa"])
    if "CID_GRUPO_J" in df.columns and applied["grupo"]:
        mask &= df["CID_GRUPO_J"].astype(str).isin(applied["grupo"])
    if hosp_col and applied["hosp"]:
        mask &= df[hosp_col].astype(str).isin(applied["hosp"])
    if "CID_GRUPO_J" in df.columns and applied["grupo"]:
        mask &= df["CID_GRUPO_J"].astype(str).isin(applied["grupo"])
    if "MUNIC_RES" in df.columns and applied.get("municipios"):
        mask &= df["MUNIC_RES"].astype(str).isin(applied["municipios"])
    if "CID_CAT3" in df.columns and applied.get("cid3"):
        mask &= df["CID_CAT3"].astype(str).isin(applied["cid3"])
    elif "DIAG_PRINC" in df.columns and applied.get("cid3"):
        mask &= df["DIAG_PRINC"].astype(str).str[:3].isin(applied["cid3"])
    
    dff = df[mask].copy()
    
    if "DT_INTER" in dff.columns:
        dff["DT_INTER"] = pd.to_datetime(dff["DT_INTER"], errors="coerce")

    n_total = len(df)
    n_filtrado = len(dff)
    
    d_ini = applied.get("d_ini")
    d_fim = applied.get("d_fim")

    st.header("📊 Visão Geral das Internações")

    col1, col2, col3, col4, col5 = st.columns(5)

    total_internacoes = n_filtrado
    media_idade = float(dff["IDADE"].mean()) if "IDADE" in dff.columns else np.nan
    taxa_mortalidade = float(dff["MORTE"].mean() * 100) if "MORTE" in dff.columns else np.nan
    media_permanencia = float(dff["DIAS_PERM"].mean()) if "DIAS_PERM" in dff.columns else np.nan
    periodo_txt = f"{d_ini} → {d_fim}" if d_ini and d_fim else "-"

    col1.metric("Total de Internações (filtro)", _kpi(total_internacoes))
    col2.metric("Média de Idade", f"{media_idade:.1f} anos" if not np.isnan(media_idade) else "-")
    col3.metric("Taxa de Mortalidade", f"{taxa_mortalidade:.2f}%" if not np.isnan(taxa_mortalidade) else "-")
    col4.metric("Média de Permanência", f"{media_permanencia:.1f} dias" if not np.isnan(media_permanencia) else "-")
    col5.metric("Período", periodo_txt)

    st.caption(f"Mostrando {n_filtrado:,} de {n_total:,} registros após filtros.".replace(",", "."))

    st.subheader("⏱️ Sazonalidade e Tendências")
    st.caption("Dica: use os filtros à esquerda para comparar períodos, grupos etários e diagnósticos.")

    if "DT_INTER" in dff.columns and dff["DT_INTER"].notna().any():
        # Índice datetime válido para o Grouper
        dff_daily = dff.dropna(subset=["DT_INTER"]).set_index("DT_INTER").sort_index()

        # Contagem por dia (sem exigir coluna específica)
        ts_daily = (
            dff_daily
            .groupby(pd.Grouper(freq="D"))
            .size()
            .rename("Internações por dia")
        )

        ts_ma7  = ts_daily.rolling(7,  min_periods=1).mean().rename("MM7")
        ts_ma30 = ts_daily.rolling(30, min_periods=1).mean().rename("MM30")
        
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            y_log = st.checkbox("Escala log no eixo Y", value=False)
        with c2:
            show_pandemic_line = st.checkbox("Marcar início e fim da pandemia", value=True)

        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=ts_daily.index, y=ts_daily.values, mode="lines", name="Diário", opacity=0.35))
        fig_ts.add_trace(go.Scatter(x=ts_ma7.index, y=ts_ma7.values, mode="lines", name="Média móvel (7d)"))
        fig_ts.add_trace(go.Scatter(x=ts_ma30.index, y=ts_ma30.values, mode="lines", name="Média móvel (30d)"))
        fig_ts.update_layout(xaxis_title="Data", yaxis_title="Internações", legend_title_text="", margin=dict(l=20,r=20,t=20,b=20))
        if y_log:
            fig_ts.update_yaxes(type="log")

        if show_pandemic_line:
            pandemia_inicio = pd.Timestamp("2020-03-01")
            pandemia_fim = pd.Timestamp("2022-05-22")

            
            fig_ts.add_vline(x=pandemia_inicio, line_dash="dash", line_color="#D62728", line_width=2, opacity=0.9)
            fig_ts.add_vline(x=pandemia_fim,   line_dash="dash", line_color="#D62728", line_width=2, opacity=0.9)

            
            fig_ts.add_annotation(
                x=pandemia_inicio, xref="x", y=1, yref="paper",
                text="Início (01/03/2020)", showarrow=False,
                yshift=10, align="left", font=dict(color="#D62728", size=12)
            )
            fig_ts.add_annotation(
                x=pandemia_fim, xref="x", y=1, yref="paper",
                text="Fim (22/05/2022)", showarrow=False,
                yshift=10, align="right", font=dict(color="#D62728", size=12)
            )

        st.plotly_chart(fig_ts, use_container_width=True)

        st.markdown("#### 🔥 Heatmaps de sazonalidade (Ano x Mês)")
        c1, c2 = st.columns([1,1])
        with c1:
            with st.expander("Configurações do heatmap", expanded=False):
                show_labels = st.checkbox("Mostrar rótulos numéricos", value=True)
        tabs = st.tabs(["Contagem", "% no ano"])
        with tabs[0]:
            _heatmap_counts(dff, "Contagem mensal por ano", show_text=show_labels)
        with tabs[1]:
            _heatmap_share(dff, "Participação mensal dentro do ano (%)", show_text=show_labels)

        
        if set(["ANO_MES","CID_GRUPO_J"]).issubset(dff.columns):
            tmp = dff.groupby(["ANO_MES","CID_GRUPO_J"]).size().reset_index(name="n")
            tmp["prop"] = tmp.groupby("ANO_MES")["n"].transform(lambda x: (x/x.sum()).round(3))
            series_grp = tmp.copy()
            
            try:
                series_grp["ANO_MES_TS"] = pd.PeriodIndex(series_grp["ANO_MES"], freq="M").to_timestamp()
            except Exception:
                series_grp["ANO_MES_TS"] = pd.to_datetime(series_grp["ANO_MES"], errors="coerce")
            fig_area = px.area(series_grp, x="ANO_MES_TS", y="prop", color="CID_GRUPO_J",
                               title="Proporção mensal por grupos (J00-J99)")
            fig_area.update_yaxes(tickformat=".0%")
            fig_area.update_layout(xaxis_title="Mês/Ano", yaxis_title="Proporção", legend_title="Grupo CID-10",
                                   margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_area, use_container_width=True)

        
        if "DIA_SEMANA" in dff.columns:
            by_weekday = dff.groupby("DIA_SEMANA").size().reset_index(name="qtd")
            order = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
            by_weekday["DIA_SEMANA"] = pd.Categorical(by_weekday["DIA_SEMANA"], categories=order, ordered=True)
            by_weekday = by_weekday.sort_values("DIA_SEMANA")
            fig_wd = px.bar(by_weekday, x="DIA_SEMANA", y="qtd", title="Internações por dia da semana")
            fig_wd.update_layout(xaxis_title="Dia da semana", yaxis_title="Internações", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_wd, use_container_width=True)

    else:
        st.info("Coluna DT_INTER ausente ou vazia — não é possível montar a série temporal.")

    st.subheader("🧪 Diagnósticos (CID-10)")

    if "DIAG_PRINC" in dff.columns:
        if "CID_CAT3" in dff.columns:
            top_cat = (dff["CID_CAT3"].value_counts().head(20).reset_index())
            top_cat.columns = ["CID_CAT3", "qtd"]
            fig_cat = px.bar(top_cat, x="CID_CAT3", y="qtd", title="Top 20 categorias CID-10 (3 dígitos) — DIAG_PRINC")
            fig_cat.update_layout(xaxis_title="CID (3 dígitos)", yaxis_title="Internações", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_cat, use_container_width=True)

        if "CID_GRUPO_J" in dff.columns:
            grp = dff.groupby("CID_GRUPO_J").size().reset_index(name="qtd").sort_values("qtd", ascending=False)
            fig_grp = px.bar(grp, y="CID_GRUPO_J", x="qtd", orientation="h", title="Distribuição por grupos (J00-J99)")
            fig_grp.update_layout(xaxis_title="Internações", yaxis_title="Grupo CID-10", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_grp, use_container_width=True)

        if set(["MORTE","CID_GRUPO_J","FAIXA_ETARIA"]).issubset(dff.columns) and dff["MORTE"].notna().any():
            mat = dff.pivot_table(index="FAIXA_ETARIA", columns="CID_GRUPO_J", values="MORTE", aggfunc="mean")
            mat = (mat * 100).round(1)
            fig_mtx = px.imshow(
                mat.values,
                labels=dict(x="Grupo CID-10", y="Faixa etária", color="Mortalidade (%)"),
                x=mat.columns.tolist(),
                y=[str(i) for i in mat.index.tolist()],
                aspect="auto",
                color_continuous_scale="Reds",
                text_auto=True
            )
            fig_mtx.update_layout(title="Mortalidade (%) por grupo diagnóstico x faixa etária", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_mtx, use_container_width=True)
    else:
        st.info("Coluna DIAG_PRINC não encontrada.")

    st.subheader("👤 Perfil Demográfico")

    cols = st.columns(2)
    sexo_col = "SEXO_TXT" if "SEXO_TXT" in dff.columns else ("SEXO" if "SEXO" in dff.columns else None)
    if sexo_col:
        by_sex = dff[sexo_col].value_counts().reset_index()
        by_sex.columns = ["SEXO", "qtd"]
        fig_sex = px.pie(by_sex, names="SEXO", values="qtd", title="Distribuição por sexo", hole=0.35)
        cols[0].plotly_chart(fig_sex, use_container_width=True)
    else:
        cols[0].info("Sem coluna de sexo.")

    if "IDADE" in dff.columns:
        fig_age = px.histogram(dff, x="IDADE", nbins=40, title="Distribuição de idades")
        fig_age.update_layout(xaxis_title="Idade (anos)", yaxis_title="Contagem", margin=dict(l=20,r=20,t=40,b=20))
        cols[1].plotly_chart(fig_age, use_container_width=True)
    else:
        cols[1].info("Sem coluna de idade.")

    if sexo_col and "FAIXA_ETARIA" in dff.columns:
        pyr = dff.groupby(["FAIXA_ETARIA", sexo_col]).size().reset_index(name="qtd")
        male_label = "Masculino" if "Masculino" in dff[sexo_col].unique() else str(dff[sexo_col].unique()[0]) if len(dff[sexo_col].unique())>0 else "M"
        female_label = "Feminino" if "Feminino" in dff[sexo_col].unique() else (str(dff[sexo_col].unique()[1]) if len(dff[sexo_col].unique())>1 else "F")
        pyr["qtd_plot"] = np.where(pyr[sexo_col] == male_label, -pyr["qtd"], pyr["qtd"])
        fig_pyr = go.Figure()
        for sexo in [male_label, female_label]:
            sub = pyr[pyr[sexo_col] == sexo]
            fig_pyr.add_trace(go.Bar(y=sub["FAIXA_ETARIA"].astype(str), x=sub["qtd_plot"], name=sexo, orientation="h"))
        fig_pyr.update_layout(title="Pirâmide etária (Masculino x Feminino)", barmode="overlay", bargap=0.05)
        fig_pyr.update_xaxes(title_text="Internações (escala negativa para Masculino)")
        fig_pyr.update_yaxes(title_text="Faixa etária")
        st.plotly_chart(fig_pyr, use_container_width=True)

    st.subheader("🏥 Desfechos e Utilização")

    cols2 = st.columns(2)
    if "DIAS_PERM" in dff.columns and dff["DIAS_PERM"].notna().any():
        fig_dperm = px.histogram(dff[dff["DIAS_PERM"].between(0, 60, inclusive="both")], x="DIAS_PERM", nbins=30,
                                 title="Distribuição de dias de permanência (0-60 dias)")
        fig_dperm.update_layout(xaxis_title="Dias de permanência", yaxis_title="Internações", margin=dict(l=20,r=20,t=40,b=20))
        cols2[0].plotly_chart(fig_dperm, use_container_width=True)
    else:
        cols2[0].info("Sem coluna de dias de permanência.")

    if set(["MORTE","FAIXA_ETARIA"]).issubset(dff.columns) and dff["MORTE"].notna().any():
        mort_by_age = dff.groupby("FAIXA_ETARIA")["MORTE"].mean().reset_index(name="taxa")
        fig_mage = px.bar(mort_by_age, x="FAIXA_ETARIA", y="taxa",
                          title="Taxa de mortalidade por faixa etária", text_auto=".1%")
        fig_mage.update_yaxes(tickformat=".1%")
        cols2[1].plotly_chart(fig_mage, use_container_width=True)
    elif "MORTE" in dff.columns:
        cols2[1].info("Coluna de óbito presente, mas sem valores válidos após filtros.")

    
    if set(["MORTE","DT_INTER"]).issubset(dff.columns) and dff["MORTE"].notna().any():
        mort_daily = (
            dff.dropna(subset=["DT_INTER"])
            .set_index("DT_INTER")
            .sort_index()
            .groupby(pd.Grouper(freq="D"))["MORTE"]
            .mean()
            .rename("Taxa diária")
        )
        mort_ma30 = mort_daily.rolling(30, min_periods=7).mean().rename("MM30")
        fig_mort = go.Figure()
        fig_mort.add_trace(go.Scatter(x=mort_daily.index, y=mort_daily.values, mode="lines", name="Diária", opacity=0.3))
        fig_mort.add_trace(go.Scatter(x=mort_ma30.index, y=mort_ma30.values, mode="lines", name="Média móvel (30d)"))
        fig_mort.update_layout(title="Mortalidade ao longo do tempo", yaxis_tickformat=".1%",
                               xaxis_title="Data", yaxis_title="Taxa de óbito", margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_mort, use_container_width=True)
        
    if set(["CID_CAT3","DIAS_PERM"]).issubset(dff.columns):
        top_los = (dff.groupby("CID_CAT3")
                      .agg(n=("DIAS_PERM","count"), los_medio=("DIAS_PERM","mean"))
                      .query("n >= 30")
                      .sort_values("los_medio", ascending=False)
                      .head(10)
                      .reset_index())
        if not top_los.empty:
            fig_top_los = px.bar(top_los, x="CID_CAT3", y="los_medio", hover_data=["n"],
                                 title="Top 10 CID (3 dígitos) por LOS médio (N≥30)")
            fig_top_los.update_layout(xaxis_title="CID (3 dígitos)", yaxis_title="LOS médio (dias)", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_top_los, use_container_width=True)

    st.subheader("⬇️ Exportar dados filtrados")
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV filtrado", data=csv, file_name="df_sus_filtrado.csv", mime="text/csv")

    st.caption("Elaborado para o TCC — Previsão de internações respiratórias (RJ).")