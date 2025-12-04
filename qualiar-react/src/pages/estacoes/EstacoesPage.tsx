import { type JSX, useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import Papa from "papaparse";
import "./EstacoesPage.css";
import { parseDateFlexible } from "../../utils/date";
import { toNumberOrNaN, uniq, groupBy } from "../../utils/data";
import { percentile, median, rollingMean} from "../../utils/math";
import {
  MapIcon,
  InfoIcon,
  StatsIcon,
  TrendIcon,
  CalendarIcon,
  CorrelationIcon,
  TestIcon,
  DownloadIcon,
  FilterIcon
} from '../../components/Icons';

// -------------------------------------------------
// Config
// -------------------------------------------------
const DATA_URL =
  "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/Estacoes_Tratadas_Por_Dia/ESTACOES_UNIFICADAS_POR_DIA.csv";

const NUM_COLS_POSSIVEIS = [
  "temp",
  "ur",
  "chuva",
  "co",
  "no",
  "no2",
  "nox",
  "so2",
  "o3",
  "pm10",
  "pm2_5",
  "AQI",
];

// -------------------------------------------------
// Utilitários
// -------------------------------------------------

function minMaxNormalize(values: (number | null)[]) {
  const finite = values.filter((v) => Number.isFinite(v as number)) as number[];
  const lo = Math.min(...finite);
  const hi = Math.max(...finite);
  return values.map((v) =>
    Number.isFinite(v as number) && hi !== lo ? ((v as number) - lo) / (hi - lo) : v === null ? null : 0.5
  );
}

function pearson(x: number[], y: number[]) {
  // remove pares com NaN
  const a: number[] = [];
  const b: number[] = [];
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const xi = x[i];
    const yi = y[i];
    if (Number.isFinite(xi) && Number.isFinite(yi)) {
      a.push(xi);
      b.push(yi);
    }
  }
  const n = a.length;
  if (n === 0) return NaN;
  const mx = a.reduce((s, v) => s + v, 0) / n;
  const my = b.reduce((s, v) => s + v, 0) / n;
  let num = 0,
    dx = 0,
    dy = 0;
  for (let i = 0; i < n; i++) {
    const vx = a[i] - mx;
    const vy = b[i] - my;
    num += vx * vy;
    dx += vx * vx;
    dy += vy * vy;
  }
  const den = Math.sqrt(dx * dy);
  return den === 0 ? NaN : num / den;
}

function corrMatrix(df: any[], cols: string[]) {
  const Z = cols.map((c) => df.map((r) => toNumberOrNaN(r[c])));
  const n = cols.length;
  const out: number[][] = Array.from({ length: n }, () => new Array(n).fill(NaN));
  for (let i = 0; i < n; i++) {
    for (let j = i; j < n; j++) {
      const r = pearson(Z[i], Z[j]);
      out[i][j] = r;
      out[j][i] = r;
    }
  }
  return out;
}

// -------------------------------------------------
// Página Principal
// -------------------------------------------------
export default function EstacoesPage(): JSX.Element {
  const [rawRows, setRawRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros principais
  const [dateFrom, setDateFrom] = useState<string | undefined>(undefined);
  const [dateTo, setDateTo] = useState<string | undefined>(undefined);
  const [stationsSel, setStationsSel] = useState<string[]>([]);

  // Controles do mapa / gráficos
  const [mapVar, setMapVar] = useState<string | null>(null);
  const [mapAgg, setMapAgg] = useState<"média" | "mediana" | "máximo">("média");
  const [mapMaxSize, setMapMaxSize] = useState<number>(40);

  const [trendVars, setTrendVars] = useState<string[]>([]);
  const [boxVar, setBoxVar] = useState<string | null>(null);
  const [monthVar, setMonthVar] = useState<string | null>(null);

  // Carrega CSV
  useEffect(() => {
    setLoading(true);
    Papa.parse(DATA_URL, {
      download: true,
      header: true,
      dynamicTyping: false,
      skipEmptyLines: true,
      complete: (res) => {
        try {
          const rows = (res.data as any[]).map((r) => ({ ...r }));
          // Tipagem/normalização de colunas
          const withTypes = rows.map((r) => {
            const d = parseDateFlexible(r["data_dia"]);
            const lat = toNumberOrNaN(r["lat"]);
            const lon = toNumberOrNaN(r["lon"]);
            const nome_estacao = r["nome_estacao"] ?? r["estacao"] ?? r["station"] ?? "";

            const out: any = { ...r, data_dia: d ?? null, lat, lon, nome_estacao };
            // Coerção numérica para possíveis colunas numéricas
            for (const c of NUM_COLS_POSSIVEIS) {
              if (c in out) out[c] = toNumberOrNaN(out[c]);
            }
            if (d && !out["ano"]) out["ano"] = d.getFullYear();
            if (d && !out["mes"]) out["mes"] = d.getMonth() + 1;
            return out;
          });

          setRawRows(withTypes);
          setLoading(false);
          setError(null);
        } catch (e: any) {
          setError(e?.message || "Falha ao processar CSV");
          setLoading(false);
        }
      },
      error: (err) => {
        setError(err?.message || "Erro ao baixar CSV");
        setLoading(false);
      },
    });
  }, []);

  // Colunas realmente disponíveis no CSV
  const numericCols = useMemo(() => {
    const ok = NUM_COLS_POSSIVEIS.filter((c) => rawRows.some((r) => r[c] !== undefined));
    return ok;
  }, [rawRows]);

  const stations = useMemo(() => {
    return uniq(
      rawRows
        .map((r) => String(r["nome_estacao"] || ""))
        .filter((s) => s && s.trim().length > 0)
    ).sort();
  }, [rawRows]);

  // Defaults quando dados chegarem
  useEffect(() => {
    if (rawRows.length > 0) {
      const dates = rawRows.map((r) => r.data_dia).filter(Boolean) as Date[];
      const minD = new Date(Math.min(...dates.map((d) => d.getTime())));
      const maxD = new Date(Math.max(...dates.map((d) => d.getTime())));
      setDateFrom(minD.toISOString().slice(0, 10));
      setDateTo(maxD.toISOString().slice(0, 10));
      setStationsSel([...stations]);
      setMapVar(numericCols.includes("temp") ? "temp" : numericCols[0] || null);
      const defTrend = ["temp", "no2", "o3"].filter((v) => numericCols.includes(v));
      setTrendVars(defTrend.length ? defTrend : numericCols.slice(0, Math.min(3, numericCols.length)));
      setBoxVar(numericCols[0] || null);
      setMonthVar(numericCols[1] || numericCols[0] || null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawRows.length]);

  // Aplica filtros
  const filtered = useMemo(() => {
    if (!rawRows.length) return [] as any[];
    let out = rawRows.filter((r) => r.data_dia instanceof Date);
    if (dateFrom) {
      const d0 = new Date(dateFrom + "T00:00:00");
      out = out.filter((r) => (r.data_dia as Date) >= d0);
    }
    if (dateTo) {
      const d1 = new Date(dateTo + "T23:59:59");
      out = out.filter((r) => {
        const dt = r.data_dia;
        return dt instanceof Date && dt.getTime() <= d1.getTime();
      });
    }
    if (stationsSel.length) {
      const set = new Set(stationsSel);
      out = out.filter((r) => set.has(String(r.nome_estacao || "")));
    }
    return out;
  }, [rawRows, dateFrom, dateTo, stationsSel]);

  // KPIs
  const kpi = useMemo(() => {
    const n = filtered.length;
    const nStations = uniq(filtered.map((r) => r.nome_estacao)).length;
    const ptxt = dateFrom && dateTo ? `${dateFrom} → ${dateTo}` : "-";
    return { n, nStations, ptxt };
  }, [filtered, dateFrom, dateTo]);

  // -------------------
  // UI helpers
  // -------------------
  const allSelected = stationsSel.length === stations.length;
  const toggleStations = (values: string[]) => {
    if (values.includes("__ALL__")) {
      setStationsSel(stations);
    } else {
      setStationsSel(values);
    }
  };

  // -------------------
  // MAPA — agregação por estação
  // -------------------
  const mapData = useMemo(() => {
    if (!mapVar) return null;
    const byKey = groupBy(
      filtered.filter((r) => Number.isFinite(r[mapVar as string]) && Number.isFinite(r.lat) && Number.isFinite(r.lon)),
      (r) => `${r.nome_estacao}|${r.lat}|${r.lon}`
    );

    const rows: { nome_estacao: string; lat: number; lon: number; valor: number }[] = [];
    byKey.forEach((items, key) => {
      const [nome_estacao, latS, lonS] = key.split("|");
      const vals = items.map((r) => r[mapVar]);
      let agg: number = NaN;
      if (mapAgg === "média") agg = vals.reduce((s, v) => s + v, 0) / vals.length;
      else if (mapAgg === "mediana") agg = median(vals);
      else agg = Math.max(...vals);
      rows.push({ nome_estacao, lat: Number(latS), lon: Number(lonS), valor: agg });
    });

    const v = rows.map((r) => r.valor).filter((x) => Number.isFinite(x)) as number[];
    const p5 = percentile(v, 5);
    const p95 = percentile(v, 95);

    const sizes = rows.map((r) => {
      let norm = 0.5;
      if (Number.isFinite(p5) && Number.isFinite(p95) && p95 !== p5) {
        norm = Math.min(1, Math.max(0, (r.valor - (p5 as number)) / ((p95 as number) - (p5 as number))));
      }
      const minSize = Math.max(6, Math.round(mapMaxSize * 0.25));
      return minSize + norm * (mapMaxSize - minSize);
    });

    const centerLat = rows.reduce((s, r) => s + r.lat, 0) / (rows.length || 1);
    const centerLon = rows.reduce((s, r) => s + r.lon, 0) / (rows.length || 1);

    return { rows, sizes, centerLat, centerLon };
  }, [filtered, mapVar, mapAgg, mapMaxSize]);

  // -------------------
  // TENDÊNCIAS MM30 normalizadas por estação+variável
  // -------------------
  const trendsFigure = useMemo(() => {
    if (!trendVars.length) return null;
    const byStation = groupBy(filtered, (r) => String(r.nome_estacao));
    const stationsOrdered = [
      "ESTAÇÃO BANGU",
      "ESTAÇÃO CAMPO GRANDE",
      "ESTAÇÃO CENTRO",
      "ESTAÇÃO COPACABANA",
      "ESTAÇÃO IRAJÁ",
      "ESTAÇÃO PEDRA DE GUARATIBA",
      "ESTAÇÃO SÃO CRISTÓVÃO",
      "ESTAÇÃO TIJUCA",
    ].filter((e) => byStation.has(e));
    const fallback = Array.from(byStation.keys()).sort();
    const stationsUse = stationsOrdered.length ? stationsOrdered : fallback;

    const data: any[] = [];
    // grid de N linhas x 1 coluna
    const layout: any = {
      title: `Tendências (MM30 normalizado) — ${trendVars.join("; ")}`,
      grid: { rows: stationsUse.length, columns: 1, pattern: "independent" },
      margin: { l: 40, r: 20, t: 50, b: 20 },
      showlegend: true,
      legend: { orientation: "h", y: 1.08 },
    };

    stationsUse.forEach((stName, idx) => {
      const axisSuf = idx === 0 ? "" : String(idx + 1);
      const arr = (byStation.get(stName) || []).filter((r) => r.data_dia instanceof Date);
      arr.sort((a, b) => (a.data_dia as Date).getTime() - (b.data_dia as Date).getTime());

      trendVars.forEach((v, vi) => {
        const xs = arr.map((r) => r.data_dia as Date);
        const ys = arr.map((r) => toNumberOrNaN(r[v]));
        const mm = rollingMean(ys, 30);
        const norm = minMaxNormalize(mm);
        data.push({
          x: xs,
          y: norm,
          mode: "lines",
          type: "scatter",
          name: v,
          legendgroup: v,
          showlegend: idx === 0, // legend só na primeira linha
          xaxis: `x${axisSuf}`,
          yaxis: `y${axisSuf}`,
          hovertemplate: `%{x|%d/%m/%Y}<br>${stName}<br>${v}: %{y:.2f}<extra></extra>`,
        });
      });

      // título de cada linha
      const yref = idx === 0 ? "y domain" : `y${idx + 1} domain`;
      layout.annotations = layout.annotations || [];
      layout.annotations.push({
        x: 0.5,
        y: 1.07,
        xref: "x domain",
        yref,
        text: stName,
        showarrow: false,
        xanchor: "center",
        yanchor: "bottom",
        font: { size: 13 },
      });

      // remove ticks do eixo Y dessa linha
      layout[`yaxis${axisSuf}`] = { showticklabels: false, title: "" };
    });

    layout.height = Math.max(320, 180 * stationsUse.length);
    return { data, layout };
  }, [filtered, trendVars]);

  // -------------------
  // BOX por estação
  // -------------------
  const boxByStation = useMemo(() => {
    if (!boxVar) return null;
    const bySt = groupBy(
      filtered.filter((r) => Number.isFinite(r[boxVar])),
      (r) => String(r.nome_estacao)
    );
    // ordena por mediana desc
    const order = Array.from(bySt.entries())
      .map(([k, arr]) => ({ k, med: median(arr.map((r) => r[boxVar!])) }))
      .sort((a, b) => (b.med ?? 0) - (a.med ?? 0))
      .map((o) => o.k);

    const data: any[] = order.map((k) => ({
      y: (bySt.get(k) || []).map((r) => r[boxVar!]),
      name: k,
      type: "box",
      boxpoints: "outliers",
    }));

    const layout: any = {
      title: `${boxVar} — distribuição por estação`,
      margin: { l: 40, r: 20, t: 40, b: 80 },
      xaxis: { tickangle: -30 },
      yaxis: { title: boxVar },
      showlegend: false,
    };
    return { data, layout };
  }, [filtered, boxVar]);

  // -------------------
  // Sazonalidade mensal (box por mês)
  // -------------------
  const monthlyBox = useMemo(() => {
    if (!monthVar) return null;
    
    const rows = filtered.filter((r) => {
      const valor = toNumberOrNaN(r[monthVar]);
      const mesNum = Number(r["mes"]);
      
      return Number.isFinite(valor) && mesNum >= 1 && mesNum <= 12;
    });
    
    if (rows.length === 0) return null;
    
    const byMonth = groupBy(rows, (r) => Number(r["mes"]) as number);
    
    const order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const monthLabels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

    const data: any[] = order.map((m, i) => {
      const monthData = byMonth.get(m) || [];
      const valores = monthData.map((r) => {
        const val = toNumberOrNaN(r[monthVar!]);
        return Number.isFinite(val) ? val : null;
      }).filter((v): v is number => v !== null); // Filtrar apenas números válidos
      
      return {
        y: valores,
        name: monthLabels[i],
        type: "box",
        boxpoints: "outliers",
      };
    });

    const layout: any = {
      title: `${monthVar} — sazonalidade por mês (${rows.length} registros)`,
      margin: { l: 40, r: 20, t: 40, b: 40 },
      yaxis: { title: monthVar },
      showlegend: false,
      xaxis: {
        title: "Mês",
        tickvals: monthLabels,
        ticktext: monthLabels
      }
    };
    return { data, layout };
  }, [filtered, monthVar]);

  // -------------------
  // Correlação (Pearson)
  // -------------------
  const corrFig = useMemo(() => {
    const cols = numericCols.filter((c) => filtered.some((r) => Number.isFinite(r[c])));
    if (!cols.length) return null;
    const M = corrMatrix(filtered, cols).map((row) => row.map((v) => (Number.isFinite(v) ? Number(v.toFixed(2)) : null)));
    const data: any[] = [
      {
        z: M,
        x: cols,
        y: cols,
        type: "heatmap",
        zmin: -1,
        zmax: 1,
        colorscale: "RdBu",
        reversescale: true,
        text: M.map((row) => row.map((v) => (v === null ? "" : v.toFixed(2)))),
        texttemplate: "%{text}",
        hovertemplate: "%{x} × %{y}: %{z:.2f}<extra></extra>",
      },
    ];
    const layout: any = {
      title: "Matriz de correlação (Pearson)",
      margin: { l: 80, r: 20, t: 40, b: 80 },
    };
    return { data, layout };
  }, [filtered, numericCols]);

  // -------------------
  // Completude por variável
  // -------------------
  const completenessFig = useMemo(() => {
    const cols = numericCols;
    if (!cols.length) return null;
    const pct = cols.map((c) => {
      const vals = filtered.map((r) => r[c]);
      const notNull = vals.filter((v) => Number.isFinite(v)).length;
      const p = filtered.length ? (100 * notNull) / filtered.length : 0;
      return { c, p: Number(p.toFixed(1)) };
    });
    pct.sort((a, b) => b.p - a.p);

    const data: any[] = [
      {
        x: pct.map((o) => o.c),
        y: pct.map((o) => o.p),
        type: "bar",
        text: pct.map((o) => o.p + "%"),
        textposition: "auto",
      },
    ];
    const layout: any = {
      title: "Completude de dados por variável (%)",
      margin: { l: 40, r: 20, t: 40, b: 80 },
      yaxis: { title: "%" },
    };
    return { data, layout };
  }, [filtered, numericCols]);

  // -------------------
  // Exportação CSV (dados filtrados)
  // -------------------
  const onExport = () => {
    const csv = Papa.unparse(
      filtered.map((r) => ({
        ...r,
        data_dia: r.data_dia instanceof Date ? r.data_dia.toISOString().slice(0, 10) : "",
      }))
    );
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "estacoes_filtrado.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // -------------------
  // Render
  // -------------------
  return (
    <div className="estacoes-container">
      <h1 className="estacoes-title">
        <MapIcon style={{ marginRight: '10px', verticalAlign: 'middle' }} />
        Estações de Monitoramento — EDA
      </h1>

      <details className="info-summary">
        <summary>
          <InfoIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Sobre os dados
        </summary>
        <div className="info-content">
          <p>
            Colunas comuns: <b>nome_estacao</b>, <b>lat</b>, <b>lon</b>, <b>data_dia</b>, <b>ano</b>, <b>mes</b>, e variáveis
            como {NUM_COLS_POSSIVEIS.filter((c) => numericCols.includes(c)).join(", ") || "(nenhuma detectada)"}.
          </p>
          <p>
            Fonte: <code className="code">ESTACOES_UNIFICADAS_POR_DIA.csv</code> (GitHub / AILAB-CEFET-RJ).
          </p>
        </div>
      </details>

      {/* Filtros */}
      <section className="filters-section">
        <h3 className="filtros-title">
          <FilterIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Filtro (global da página)
        </h3>
        <div className="filter-group">
          <label className="filter-label">Período — início</label>
          <input 
            type="date" 
            className="filter-input"
            value={dateFrom || ""} 
            onChange={(e) => setDateFrom(e.target.value)} 
          />
        </div>
        <div className="filter-group">
          <label className="filter-label">Período — fim</label>
          <input 
            type="date" 
            className="filter-input"
            value={dateTo || ""} 
            onChange={(e) => setDateTo(e.target.value)} 
          />
        </div>
        <div style={{ gridColumn: "1 / span 2" }} className="filter-group">
          <label className="filter-label">Estações</label>
          <select
            multiple
            className="filter-select"
            value={allSelected ? ["__ALL__", ...stationsSel] : stationsSel}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions).map((o) => o.value);
              toggleStations(values);
            }}
            size={Math.min(12, Math.max(4, stations.length))}
          >
            <option value="__ALL__">Todos</option>
            {stations.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* KPIs */}
      <section className="kpi-section">
        <div className="kpi-card">
          <div className="kpi-label">Registros (filtro)</div>
          <div className="kpi-value">{kpi.n.toLocaleString("pt-BR")}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Estações ativas</div>
          <div className="kpi-value">{kpi.nStations.toLocaleString("pt-BR")}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Período</div>
          <div className="kpi-text">{kpi.ptxt}</div>
        </div>
      </section>

      {loading && (
        <div className="loading-state">
          <div className="spinner" /> Carregando dados...
        </div>
      )}
      {error && (
        <div className="error-state">
          Erro ao carregar: <b>{error}</b>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* MAPA */}
          <section className="section">
            <h2 className="section-title">
              <MapIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Mapa das Estações (RJ) — cor e tamanho por variável
            </h2>
            <div className="map-controls">
              {/* ... controles do mapa ... */}
            </div>
            {mapData && mapData.rows.length > 0 ? (
              <div className="map-container">
                <Plot
                  style={{ width: "100%", height: "100%" }}
                  config={{ displayModeBar: true, responsive: true }}
                  data={[
                    {
                      type: "scattermapbox",
                      lat: mapData.rows.map((r) => r.lat),
                      lon: mapData.rows.map((r) => r.lon),
                      mode: "markers",
                      text: mapData.rows.map((r) => r.nome_estacao),
                      marker: {
                        size: mapData.sizes,
                        color: mapData.rows.map((r) => r.valor),
                        colorscale: "Turbo",
                        cmin: Math.min(...mapData.rows.map((r) => r.valor)),
                        cmax: Math.max(...mapData.rows.map((r) => r.valor)),
                        opacity: 0.9,
                        showscale: true,
                        colorbar: { title: mapVar || "valor" },
                      },
                      hovertemplate: `<b>%{text}</b><br>${mapVar} (${mapAgg}): %{marker.color:.2f}<extra></extra>`,
                    } as any,
                  ]}
                  layout={{
                    mapbox: { style: "open-street-map", center: { lat: mapData.centerLat, lon: mapData.centerLon }, zoom: 10 },
                    margin: { l: 10, r: 10, t: 10, b: 10 },
                    autosize: true,
                  }}
                  useResizeHandler
                />
              </div>
            ) : (
              <div className="no-data-message">
                Sem valores válidos para a variável selecionada nas estações filtradas.
              </div>
            )}
          </section>

          {/* TENDÊNCIAS */}
          <section className="section">
            <h2 className="section-title">
              <TrendIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Tendências diárias por estação (MM30)
            </h2>
            <div className="trend-controls">
              <label className="filter-label">Variáveis (normalizadas por estação+variável)</label>
              <select
                multiple
                className="trend-select"
                value={trendVars}
                onChange={(e) => setTrendVars(Array.from(e.target.selectedOptions).map((o) => o.value))}
                size={Math.min(10, Math.max(3, numericCols.length))}
              >
                {numericCols.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            {trendsFigure ? (
              <div className="chart-wrapper" style={{ height: '600px' }}>
                <Plot 
                  style={{ width: "100%", height: "100%" }} 
                  config={{ responsive: true, displayModeBar: true }} 
                  data={trendsFigure.data} 
                  layout={{ ...trendsFigure.layout, autosize: true }}
                />
              </div>
            ) : (
              <div className="no-data-message">
                Selecione ao menos uma variável para exibir as tendências por estação.
              </div>
            )}
          </section>

          {/* BOX por estação */}
          <section className="section">
            <h2 className="section-title">
              <StatsIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Comparação por Estação (Boxplots)
            </h2>
            <div className="box-controls">
              <label className="filter-label">Variável</label>
              <select 
                value={boxVar || ""} 
                onChange={(e) => setBoxVar(e.target.value)} 
                className="box-select"
              >
                {numericCols.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            {boxByStation ? (
              <div className="chart-wrapper" style={{ height: '500px' }}>
                <Plot 
                  style={{ width: "100%", height: "100%" }} 
                  config={{ responsive: true, displayModeBar: true }} 
                  data={boxByStation.data} 
                  layout={{ ...boxByStation.layout, autosize: true }}
                />
              </div>
            ) : (
              <div className="no-data-message">
                Não há dados suficientes para os boxplots após os filtros.
              </div>
            )}
          </section>

          {/* Sazonalidade mensal */}
          <section className="section">
            <h2 className="section-title">
              <CalendarIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Sazonalidade Mensal (Boxplot por Mês)
            </h2>
            <div className="box-controls">
              <label className="filter-label">Variável</label>
              <select 
                value={monthVar || ""} 
                onChange={(e) => setMonthVar(e.target.value)} 
                className="box-select"
              >
                {numericCols.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            {monthlyBox && (
              <div className="chart-wrapper" style={{ height: '500px' }}>
                <Plot 
                  style={{ width: "100%", height: "100%" }} 
                  config={{ responsive: true, displayModeBar: true }} 
                  data={monthlyBox.data} 
                  layout={{ ...monthlyBox.layout, autosize: true }}
                />
              </div>
            )}
          </section>

          {/* Correlação */}
          <section className="section">
            <h2 className="section-title">
              <CorrelationIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Correlação entre Variáveis
            </h2>
            {corrFig ? (
              <div className="chart-wrapper" style={{ height: '600px' }}>
                <Plot 
                  style={{ width: "100%", height: "100%" }} 
                  config={{ responsive: true, displayModeBar: true }} 
                  data={corrFig.data} 
                  layout={{ ...corrFig.layout, autosize: true }}
                />
              </div>
            ) : (
              <div className="no-data-message">
                Não foi possível calcular correlação (faltam variáveis numéricas).
              </div>
            )}
          </section>

          {/* Completude */}
          <section className="section">
            <h2 className="section-title">
              <TestIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Completude por Variável (não nulos %)
            </h2>
            {completenessFig && (
              <div className="chart-wrapper" style={{ height: '500px' }}>
                <Plot 
                  style={{ width: "100%", height: "100%" }} 
                  config={{ responsive: true, displayModeBar: true }} 
                  data={completenessFig.data} 
                  layout={{ ...completenessFig.layout, autosize: true }}
                />
              </div>
            )}
          </section>

          {/* Exportar */}
          <section className="export-section">
            <h2 className="section-title">
              <DownloadIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Exportar dados filtrados
            </h2>
            <button onClick={onExport} className="export-button">
              Baixar CSV filtrado
            </button>
          </section>
        </>
      )}
    </div>
  );
}