import React, { useEffect, useState, useMemo } from "react";
import Plot from "react-plotly.js";
import Papa from "papaparse";

// ================================================
// AnaliseRio — Versão Completa
// ================================================

//--------------------------------------------------
// Config
//--------------------------------------------------
const URL_RAW =
  "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO.csv";
const URL_TREATED =
  "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv";

//--------------------------------------------------
// Types
//--------------------------------------------------
interface RioData {
  data_dia: Date;
  ano: number;
  mes: number;
  dia?: number;
  temp?: number;
  ur?: number;
  chuva?: number;
  co?: number;
  no?: number;
  no2?: number;
  nox?: number;
  so2?: number;
  o3?: number;
  pm10?: number;
  pm2_5?: number;
  AQI?: number;
  Qualidade_do_Ar?: number;
  [key: string]: any;
}

//--------------------------------------------------
// Constants
//--------------------------------------------------
const MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const MONTH_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

const AQI_BINS = [
  { min: 0, max: 40, label: "N1 - Boa" },
  { min: 41, max: 80, label: "N2 - Moderada" },
  { min: 81, max: 120, label: "N3 - Ruim" },
  { min: 121, max: 200, label: "N4 - Muito Ruim" },
  { min: 201, max: 400, label: "N5 - Péssima" },
];

const POL_BINS: { [key: string]: Array<{ min: number; max: number; label: string }> } = {
  pm10: [
    { min: 0, max: 50, label: "N1 - Boa" },
    { min: 50, max: 100, label: "N2 - Moderada" },
    { min: 100, max: 150, label: "N3 - Ruim" },
    { min: 150, max: 250, label: "N4 - Muito Ruim" },
    { min: 250, max: 600, label: "N5 - Péssima" },
  ],
  pm2_5: [
    { min: 0, max: 25, label: "N1 - Boa" },
    { min: 25, max: 50, label: "N2 - Moderada" },
    { min: 50, max: 75, label: "N3 - Ruim" },
    { min: 75, max: 125, label: "N4 - Muito Ruim" },
    { min: 125, max: 300, label: "N5 - Péssima" },
  ],
  o3: [
    { min: 0, max: 100, label: "N1 - Boa" },
    { min: 100, max: 130, label: "N2 - Moderada" },
    { min: 130, max: 160, label: "N3 - Ruim" },
    { min: 160, max: 200, label: "N4 - Muito Ruim" },
    { min: 200, max: 800, label: "N5 - Péssima" },
  ],
  co: [
    { min: 0, max: 9, label: "N1 - Boa" },
    { min: 9, max: 11, label: "N2 - Moderada" },
    { min: 11, max: 13, label: "N3 - Ruim" },
    { min: 13, max: 15, label: "N4 - Muito Ruim" },
    { min: 15, max: 50, label: "N5 - Péssima" },
  ],
  no2: [
    { min: 0, max: 200, label: "N1 - Boa" },
    { min: 200, max: 240, label: "N2 - Moderada" },
    { min: 240, max: 320, label: "N3 - Ruim" },
    { min: 320, max: 1130, label: "N4 - Muito Ruim" },
    { min: 1130, max: 3750, label: "N5 - Péssima" },
  ],
  so2: [
    { min: 0, max: 20, label: "N1 - Boa" },
    { min: 20, max: 40, label: "N2 - Moderada" },
    { min: 40, max: 365, label: "N3 - Ruim" },
    { min: 365, max: 800, label: "N4 - Muito Ruim" },
    { min: 800, max: 2620, label: "N5 - Péssima" },
  ],
};

//--------------------------------------------------
// Utils
//--------------------------------------------------
function parseDate(d: any): Date | null {
  if (!d) return null;
  const dt = new Date(d);
  return isNaN(dt.getTime()) ? null : dt;
}

function kpiInt(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "-";
  return Math.round(n).toLocaleString('pt-BR');
}

function formatNumber(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "–";
  return n.toFixed(1);
}

function classificaAQI(aqiVal: number | undefined): string | null {
  if (aqiVal === undefined || isNaN(aqiVal)) return null;
  const value = Math.round(aqiVal);
  for (const bin of AQI_BINS) {
    if (value >= bin.min && value <= bin.max) {
      return bin.label;
    }
  }
  return "Fora da escala";
}

function classificaPoluente(val: number | undefined, polCol: string): string | null {
  if (val === undefined || isNaN(val)) return null;
  const pol = polCol.toLowerCase();
  const bins = POL_BINS[pol];
  if (!bins) return null;
  
  const value = Math.round(val);
  for (const bin of bins) {
    if (value >= bin.min && value <= bin.max) {
      return bin.label;
    }
  }
  return "Fora da escala";
}

function mergeRawIntoTreated(raw: RioData[], treated: RioData[]): RioData[] {
  const mapRaw = new Map<string, RioData>();
  raw.forEach((r) => {
    const key = r.data_dia.toISOString().slice(0, 10);
    mapRaw.set(key, r);
  });

  return treated.map((t) => {
    const key = t.data_dia.toISOString().slice(0, 10);
    const base = { ...t };
    const r = mapRaw.get(key);

    if (r) {
      for (const col in r) {
        if (col === "data_dia") continue;
        if (base[col] === undefined) {
          base[col] = r[col];
        } else if (base[col] !== r[col]) {
          base[col + "_raw"] = r[col];
        }
      }
    }

    return base;
  });
}

function calculateRollingAverage(data: number[], window: number = 30): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - window + 1);
    const values = data.slice(start, i + 1);
    result.push(values.reduce((a, b) => a + b, 0) / values.length);
  }
  return result;
}

function normalizeData(data: number[]): number[] {
  const min = Math.min(...data);
  const max = Math.max(...data);
  if (max === min) return data.map(() => 0.5);
  return data.map(val => (val - min) / (max - min));
}

//--------------------------------------------------
// Componente principal
//--------------------------------------------------
export default function AnaliseRio() {
  const [rawRows, setRawRows] = useState<RioData[]>([]);
  const [treatedRows, setTreatedRows] = useState<RioData[]>([]);
  const [merged, setMerged] = useState<RioData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [selectedVars, setSelectedVars] = useState<string[]>(["temp", "no2", "o3"]);
  const [heatmapVar, setHeatmapVar] = useState<string>("temp");
  const [heatmapAgg, setHeatmapAgg] = useState<"mean" | "sum" | "max">("mean");
  const [showLabels, setShowLabels] = useState(true);
  const [boxplotVar, setBoxplotVar] = useState<string>("no2");
  const [correlationVars, setCorrelationVars] = useState<string[]>(["temp", "ur", "chuva", "no2", "o3", "pm2_5", "pm10", "AQI"]);
  const [scatterX, setScatterX] = useState<string>("temp");
  const [scatterY, setScatterY] = useState<string>("ur");
  const [showTrend, setShowTrend] = useState(false);
  const [extremeVar, setExtremeVar] = useState<string>("temp");
  const [extremeCount, setExtremeCount] = useState<number>(10);

  //--------------------------------------------------
  // Carregar dados
  //--------------------------------------------------
  useEffect(() => {
    Promise.all([
      new Promise<RioData[]>((resolve) => {
        Papa.parse(URL_RAW, {
          download: true,
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: (res) => {
            const rows = res.data as any[];
            const fixed = rows.map((r) => ({
              ...r,
              data_dia: parseDate(r.data_dia) || new Date(),
              ano: r.ano || (parseDate(r.data_dia)?.getFullYear() || new Date().getFullYear()),
              mes: r.mes || ((parseDate(r.data_dia)?.getMonth() || 0) + 1),
            })).filter(r => r.data_dia);
            resolve(fixed);
          },
          error: () => resolve([]),
        });
      }),
      new Promise<RioData[]>((resolve) => {
        Papa.parse(URL_TREATED, {
          download: true,
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: (res) => {
            const rows = res.data as any[];
            const fixed = rows.map((r) => ({
              ...r,
              data_dia: parseDate(r.data_dia) || new Date(),
              ano: r.ano || (parseDate(r.data_dia)?.getFullYear() || new Date().getFullYear()),
              mes: r.mes || ((parseDate(r.data_dia)?.getMonth() || 0) + 1),
            })).filter(r => r.data_dia);
            resolve(fixed);
          },
          error: () => resolve([]),
        });
      }),
    ]).then(([raw, treated]) => {
      setRawRows(raw);
      setTreatedRows(treated);
      
      if (raw.length && treated.length) {
        const data = mergeRawIntoTreated(raw, treated);
        setMerged(data);
        
        // Set initial date range
        const minDate = new Date(Math.min(...data.map(d => d.data_dia.getTime())));
        const maxDate = new Date(Math.max(...data.map(d => d.data_dia.getTime())));
        setDateRange([minDate, maxDate]);
      }
      
      setLoading(false);
    }).catch((err) => {
      setError("Erro ao carregar dados: " + err.message);
      setLoading(false);
    });
  }, []);

  //--------------------------------------------------
  // Dados filtrados
  //--------------------------------------------------
  const filteredData = useMemo(() => {
    if (!merged.length) return [];
    const [startDate, endDate] = dateRange;
    if (!startDate || !endDate) return merged;
    
    return merged.filter(item => {
      const itemDate = item.data_dia;
      return itemDate >= startDate && itemDate <= endDate;
    });
  }, [merged, dateRange]);

  //--------------------------------------------------
  // Métricas principais
  //--------------------------------------------------
  const metrics = useMemo(() => {
    if (!filteredData.length) return null;
    
    const uniqueDays = new Set(filteredData.map(d => d.data_dia.toISOString().slice(0, 10))).size;
    const avgRain = filteredData.reduce((sum, d) => sum + (d.chuva || 0), 0) / filteredData.length;
    const avgTemp = filteredData.reduce((sum, d) => sum + (d.temp || 0), 0) / filteredData.length;
    const avgUR = filteredData.reduce((sum, d) => sum + (d.ur || 0), 0) / filteredData.length;
    const avgAQI = filteredData.reduce((sum, d) => sum + (d.AQI || 0), 0) / filteredData.length;
    
    return { uniqueDays, avgRain, avgTemp, avgUR, avgAQI };
  }, [filteredData]);

  //--------------------------------------------------
  // Dados para séries temporais
  //--------------------------------------------------
  const aqiTimeSeries = useMemo(() => {
    if (!filteredData.length || !filteredData.some(d => d.AQI)) return null;
    
    const sortedData = [...filteredData].sort((a, b) => a.data_dia.getTime() - b.data_dia.getTime());
    const dates = sortedData.map(d => d.data_dia);
    const aqiValues = sortedData.map(d => d.AQI || 0);
    const rollingAvg = calculateRollingAverage(aqiValues, 30);
    
    return { dates, aqiValues, rollingAvg };
  }, [filteredData]);

  const multiVarTimeSeries = useMemo(() => {
    if (!filteredData.length || !selectedVars.length) return null;
    
    const sortedData = [...filteredData].sort((a, b) => a.data_dia.getTime() - b.data_dia.getTime());
    const dates = sortedData.map(d => d.data_dia);
    
    const series = selectedVars.map(varName => {
      const values = sortedData.map(d => d[varName] || 0);
      const rollingAvg = calculateRollingAverage(values, 30);
      const normalized = normalizeData(rollingAvg);
      
      return {
        name: varName,
        values: normalized,
        dates
      };
    });
    
    return series;
  }, [filteredData, selectedVars]);

  //--------------------------------------------------
  // Dados para heatmaps
  //--------------------------------------------------
  const heatmapData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const years = Array.from(new Set(filteredData.map(d => d.ano))).sort();
    const data: number[][] = [];
    
    years.forEach(year => {
      const row: number[] = [];
      MONTH_ORDER.forEach(month => {
        const monthData = filteredData.filter(d => d.ano === year && d.mes === month);
        if (monthData.length === 0) {
          row.push(NaN);
          return;
        }
        
        let value: number;
        switch (heatmapAgg) {
          case "sum":
            value = monthData.reduce((sum, d) => sum + (d[heatmapVar] || 0), 0);
            break;
          case "max":
            value = Math.max(...monthData.map(d => d[heatmapVar] || 0));
            break;
          case "mean":
          default:
            value = monthData.reduce((sum, d) => sum + (d[heatmapVar] || 0), 0) / monthData.length;
        }
        
        row.push(value);
      });
      data.push(row);
    });
    
    return {
      years: years.map(y => y.toString()),
      data
    };
  }, [filteredData, heatmapVar, heatmapAgg]);

  //--------------------------------------------------
  // Dados para boxplot
  //--------------------------------------------------
  const boxplotData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const dataByMonth: { [key: number]: number[] } = {};
    MONTH_ORDER.forEach(month => {
      dataByMonth[month] = [];
    });
    
    filteredData.forEach(d => {
      if (d[boxplotVar] !== undefined && !isNaN(d[boxplotVar]!)) {
        dataByMonth[d.mes].push(d[boxplotVar]!);
      }
    });
    
    return MONTH_ORDER.map(month => ({
      month: MONTH_LABELS[month - 1],
      values: dataByMonth[month]
    }));
  }, [filteredData, boxplotVar]);

  //--------------------------------------------------
  // Dados para correlação
  //--------------------------------------------------
  const correlationData = useMemo(() => {
    if (!filteredData.length || correlationVars.length < 2) return null;
    
    const matrix: number[][] = [];
    
    correlationVars.forEach((var1, i) => {
      const row: number[] = [];
      correlationVars.forEach((var2, j) => {
        if (i === j) {
          row.push(1);
          return;
        }
        
        const values1 = filteredData.map(d => d[var1] || 0).filter(v => !isNaN(v));
        const values2 = filteredData.map(d => d[var2] || 0).filter(v => !isNaN(v));
        
        if (values1.length === 0 || values2.length === 0) {
          row.push(0);
          return;
        }
        
        // Simple correlation calculation
        const mean1 = values1.reduce((a, b) => a + b) / values1.length;
        const mean2 = values2.reduce((a, b) => a + b) / values2.length;
        
        const numerator = values1.reduce((sum, val, idx) => sum + (val - mean1) * (values2[idx] - mean2), 0);
        const denominator = Math.sqrt(
          values1.reduce((sum, val) => sum + Math.pow(val - mean1, 2), 0) *
          values2.reduce((sum, val) => sum + Math.pow(val - mean2, 2), 0)
        );
        
        row.push(denominator === 0 ? 0 : numerator / denominator);
      });
      matrix.push(row);
    });
    
    return {
      vars: correlationVars,
      matrix
    };
  }, [filteredData, correlationVars]);

  //--------------------------------------------------
  // Dados para scatter plot
  //--------------------------------------------------
  const scatterData = useMemo(() => {
    if (!filteredData.length || scatterX === scatterY) return null;
    
    const points = filteredData
      .filter(d => d[scatterX] !== undefined && d[scatterY] !== undefined && !isNaN(d[scatterX]!) && !isNaN(d[scatterY]!))
      .map(d => ({
        x: d[scatterX]!,
        y: d[scatterY]!
      }));
    
    return points;
  }, [filteredData, scatterX, scatterY]);

  //--------------------------------------------------
  // Completude dos dados
  //--------------------------------------------------
  const completenessData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const numericCols = ["chuva", "temp", "ur", "co", "no", "no2", "nox", "so2", "o3", "pm10", "pm2_5", "AQI"];
    const availableCols = numericCols.filter(col => filteredData.some(d => d[col] !== undefined));
    
    return availableCols.map(col => {
      const nonNullCount = filteredData.filter(d => d[col] !== undefined && !isNaN(d[col]!)).length;
      const percentage = (nonNullCount / filteredData.length) * 100;
      return {
        variable: col,
        percentage: Math.round(percentage * 10) / 10
      };
    }).sort((a, b) => b.percentage - a.percentage);
  }, [filteredData]);

  //--------------------------------------------------
  // Dias extremos
  //--------------------------------------------------
  const extremeDays = useMemo(() => {
    if (!filteredData.length) return null;
    
    return [...filteredData]
      .filter(d => d[extremeVar] !== undefined && !isNaN(d[extremeVar]!))
      .sort((a, b) => (b[extremeVar]!) - (a[extremeVar]!))
      .slice(0, extremeCount)
      .map(d => ({
        date: d.data_dia.toISOString().slice(0, 10),
        value: d[extremeVar]!
      }));
  }, [filteredData, extremeVar, extremeCount]);

  //--------------------------------------------------
  // Variáveis disponíveis
  //--------------------------------------------------
  const availableVariables = useMemo(() => {
    if (!filteredData.length) return [];
    const sample = filteredData[0];
    return Object.keys(sample).filter(key => 
      typeof sample[key] === 'number' && 
      !key.includes('_raw') && 
      key !== 'ano' && 
      key !== 'mes' && 
      key !== 'dia'
    );
  }, [filteredData]);

  //--------------------------------------------------
  // Render
  //--------------------------------------------------
  if (loading) return <div style={{ padding: 24 }}>Carregando dados...</div>;
  if (error) return <div style={{ padding: 24, color: "#900" }}>{error}</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 12 }}>🌆 Rio de Janeiro — EDA Ambiental (2012–2024)</h1>

      {/* Filtros */}
      <div style={{ marginBottom: 24, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
        <h3>🔎 Filtro (global da página)</h3>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div>
            <label>Período: </label>
            <input
              type="date"
              value={dateRange[0]?.toISOString().slice(0, 10) || ''}
              onChange={(e) => setDateRange([e.target.value ? new Date(e.target.value) : null, dateRange[1]])}
            />
            <span> até </span>
            <input
              type="date"
              value={dateRange[1]?.toISOString().slice(0, 10) || ''}
              onChange={(e) => setDateRange([dateRange[0], e.target.value ? new Date(e.target.value) : null])}
            />
          </div>
        </div>
      </div>

      {/* Métricas principais */}
      {metrics && (
        <div style={{ marginBottom: 24 }}>
          <h2>📊 Visão Geral</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 16 }}>
            <div style={{ padding: 16, backgroundColor: '#f8f9fa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{kpiInt(metrics.uniqueDays)}</div>
              <div>Dias no período</div>
            </div>
            <div style={{ padding: 16, backgroundColor: '#f8f9fa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{formatNumber(metrics.avgRain)}</div>
              <div>Chuva média diária (mm)</div>
            </div>
            <div style={{ padding: 16, backgroundColor: '#f8f9fa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{formatNumber(metrics.avgTemp)}</div>
              <div>Temperatura média (°C)</div>
            </div>
            <div style={{ padding: 16, backgroundColor: '#f8f9fa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{formatNumber(metrics.avgUR)}</div>
              <div>UR média (%)</div>
            </div>
            <div style={{ padding: 16, backgroundColor: '#f8f9fa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{formatNumber(metrics.avgAQI)}</div>
              <div>AQI médio</div>
              <div style={{ fontSize: '0.8em', color: '#666' }}>
                {classificaAQI(metrics.avgAQI) || '–'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Série temporal AQI */}
      {aqiTimeSeries && (
        <div style={{ marginBottom: 24 }}>
          <h2>Série temporal do AQI diário (com faixas de qualidade)</h2>
          <Plot
            data={[
              {
                x: aqiTimeSeries.dates,
                y: aqiTimeSeries.aqiValues,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'AQI diário',
                line: { width: 1.5, color: '#34495e' },
                marker: { size: 3 },
                opacity: 0.8,
              } as any,
              {
                x: aqiTimeSeries.dates,
                y: aqiTimeSeries.rollingAvg,
                type: 'scatter',
                mode: 'lines',
                name: 'AQI (MM30)',
                line: { width: 3 },
              } as any
            ]}
            layout={{
              title: { text: 'Série temporal do AQI' },
              xaxis: { title: { text: 'Data' } },
              yaxis: { title: { text: 'AQI' } },
              shapes: AQI_BINS.map(bin => ({
                type: 'rect',
                x0: aqiTimeSeries.dates[0],
                x1: aqiTimeSeries.dates[aqiTimeSeries.dates.length - 1],
                y0: bin.min,
                y1: bin.max,
                fillcolor: ['#1f77b4', '#f1c40f', '#e67e22', '#e74c3c', '#8e44ad'][AQI_BINS.indexOf(bin)],
                opacity: 0.16,
                layer: 'below',
                line: { width: 0 }
              })),
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Tendência multivariada */}
      {multiVarTimeSeries && (
        <div style={{ marginBottom: 24 }}>
          <h2>📈 Tendência diária (MM30) — variáveis sobrepostas</h2>
          <div style={{ marginBottom: 16 }}>
            <label>Variáveis: </label>
            <select 
              multiple
              value={selectedVars}
              onChange={(e) => {
                const options = Array.from(e.target.selectedOptions, option => option.value);
                setSelectedVars(options);
              }}
              style={{ minWidth: 200, minHeight: 100 }}
            >
              {availableVariables.map(varName => (
                <option key={varName} value={varName}>{varName}</option>
              ))}
            </select>
          </div>
          <Plot
            data={multiVarTimeSeries.map(series => ({
              x: series.dates,
              y: series.values,
              type: 'scatter',
              mode: 'lines',
              name: series.name,
            }))}
            layout={{
              title: { text: `Tendência (MM30) — ${selectedVars.join('; ')} (escala normalizada)` },
              xaxis: { title: { text: 'Data' } },
              yaxis: { title: { text: 'Normalizado [0–1]' } },
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Heatmaps */}
      {heatmapData && (
        <div style={{ marginBottom: 24 }}>
          <h2>🔥 Sazonalidade (Ano x Mês)</h2>
          <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
            <div>
              <label>Variável: </label>
              <select value={heatmapVar} onChange={(e) => setHeatmapVar(e.target.value)}>
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Agregação: </label>
              <select value={heatmapAgg} onChange={(e) => setHeatmapAgg(e.target.value as any)}>
                <option value="mean">Média</option>
                <option value="sum">Soma</option>
                <option value="max">Máximo</option>
              </select>
            </div>
            <div>
              <label>
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                />
                Mostrar rótulos
              </label>
            </div>
          </div>
          
          <Plot
            data={[{
              z: heatmapData.data,
              x: MONTH_LABELS,
              y: heatmapData.years,
              type: 'heatmap',
              colorscale: 'Viridis',
              text: showLabels ? heatmapData.data.map(row => row.map(val => val?.toFixed(1))) : undefined,
              hoverinfo: 'x+y+z'
            } as any]}
            layout={{
              title: { text: `${heatmapVar} — ${heatmapAgg} por Ano x Mês` },
              xaxis: { title: { text: 'Mês' } },
              yaxis: { title: { text: 'Ano' } },
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Boxplot */}
      {boxplotData && (
        <div style={{ marginBottom: 24 }}>
          <h2>📅 Sazonalidade mensal (boxplot)</h2>
          <div style={{ marginBottom: 16 }}>
            <label>Variável: </label>
            <select value={boxplotVar} onChange={(e) => setBoxplotVar(e.target.value)}>
              {availableVariables.filter(v => v !== 'AQI').map(varName => (
                <option key={varName} value={varName}>{varName}</option>
              ))}
            </select>
          </div>
          <Plot
            data={[{
              y: boxplotData.flatMap(month => month.values),
              x: boxplotData.flatMap(month => Array(month.values.length).fill(month.month)),
              type: 'box',
              boxpoints: 'outliers'
            } as any]}
            layout={{
              title: { text: `${boxplotVar} — distribuição por mês` },
              xaxis: { 
                title: { text: 'Mês' }, 
                categoryorder: 'array', 
                categoryarray: MONTH_LABELS 
              },
              yaxis: { title: { text: boxplotVar } },
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Correlação */}
      {correlationData && (
        <div style={{ marginBottom: 24 }}>
          <h2>🔗 Correlação entre variáveis</h2>
          <div style={{ marginBottom: 16 }}>
            <label>Variáveis: </label>
            <select 
              multiple
              value={correlationVars}
              onChange={(e) => {
                const options = Array.from(e.target.selectedOptions, option => option.value);
                setCorrelationVars(options);
              }}
              style={{ minWidth: 200, minHeight: 100 }}
            >
              {availableVariables.map(varName => (
                <option key={varName} value={varName}>{varName}</option>
              ))}
            </select>
          </div>
          <Plot
            data={[{
              z: correlationData.matrix,
              x: correlationData.vars,
              y: correlationData.vars,
              type: 'heatmap',
              colorscale: 'RdBu',
              zmin: -1,
              zmax: 1,
              text: correlationData.matrix.map(row => row.map(val => val.toFixed(2))),
              hoverinfo: 'x+y+z'
            } as any]}
            layout={{
              title: { text: 'Matriz de correlação (Pearson)' },
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Scatter plot */}
      {scatterData && (
        <div style={{ marginBottom: 24 }}>
          <h2>🔁 Relação entre variáveis (dispersão)</h2>
          <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
            <div>
              <label>Eixo X: </label>
              <select value={scatterX} onChange={(e) => setScatterX(e.target.value)}>
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Eixo Y: </label>
              <select value={scatterY} onChange={(e) => setScatterY(e.target.value)}>
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div>
              <label>
                <input
                  type="checkbox"
                  checked={showTrend}
                  onChange={(e) => setShowTrend(e.target.checked)}
                />
                Linha de tendência
              </label>
            </div>
          </div>
          <Plot
            data={[{
              x: scatterData.map(p => p.x),
              y: scatterData.map(p => p.y),
              type: 'scatter',
              mode: 'markers',
              marker: { size: 6 },
              ...(showTrend && {
                mode: 'markers+lines',
                line: { shape: 'linear', dash: 'dash' }
              })
            } as any]}
            layout={{
              title: { text: `${scatterX} x ${scatterY}` },
              xaxis: { title: { text: scatterX } },
              yaxis: { title: { text: scatterY } },
              margin: { l: 60, r: 20, t: 50, b: 50 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Completude */}
      {completenessData && (
        <div style={{ marginBottom: 24 }}>
          <h2>🧪 Completude por variável (não nulos %)</h2>
          <Plot
            data={[{
              x: completenessData.map(d => d.variable),
              y: completenessData.map(d => d.percentage),
              type: 'bar',
              text: completenessData.map(d => d.percentage.toFixed(1)),
              textposition: 'auto'
            } as any]}
            layout={{
              title: { text: 'Completude de dados (%)' },
              xaxis: { title: { text: '' } },
              yaxis: { title: { text: '%' }, range: [0, 100] },
              margin: { l: 60, r: 20, t: 50, b: 100 },
            }}
            style={{ width: '100%', height: 500 }}
          />
        </div>
      )}

      {/* Dias extremos */}
      {extremeDays && (
        <div style={{ marginBottom: 24 }}>
          <h2>🚩 Dias extremos</h2>
          <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
            <div>
              <label>Variável: </label>
              <select value={extremeVar} onChange={(e) => setExtremeVar(e.target.value)}>
                {availableVariables.filter(v => v !== 'AQI').map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Quantidade: </label>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={extremeCount}
                onChange={(e) => setExtremeCount(parseInt(e.target.value))}
              />
              <span>{extremeCount} dias</span>
            </div>
          </div>
          <div style={{ maxHeight: 400, overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Data</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>{extremeVar}</th>
                </tr>
              </thead>
              <tbody>
                {extremeDays.map((day, index) => (
                  <tr key={index}>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{day.date}</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{day.value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Exportar dados */}
      <div style={{ marginBottom: 24 }}>
        <h2>⬇️ Exportar dados filtrados</h2>
        <button
          onClick={() => {
            const csv = Papa.unparse(filteredData);
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'rio_filtrado.csv';
            a.click();
            URL.revokeObjectURL(url);
          }}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Baixar CSV filtrado
        </button>
      </div>
    </div>
  );
}