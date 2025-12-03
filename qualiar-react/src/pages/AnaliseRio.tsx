import React, { useState, useMemo } from "react";
import Plot from "react-plotly.js";
import Papa from "papaparse";

// Hooks personalizados
import { useCsvData, rioDataParser } from "../hooks/useCsvData";
import { useDateFilter } from "../hooks/useFilters";
import { useTimeSeriesStats, useCorrelationMatrix, useGroupStats } from "../hooks/useStats";
import { useHeatmapData } from "../hooks/useHeatmapData";
import { useExtremeData } from "../hooks/useExtremeData";
import { useCompleteness } from "../hooks/useCompleteness";
import { useMultiVarSeries } from "../hooks/useMultiVarSeries";

// Componentes
import { MetricCard } from "../components/common/MetricCard";
import { MultiSelect } from "../components/common/MultiSelect";

// Utilitários
import { DATA_URLS, MONTH_LABELS, AQI_BINS, POL_BINS, NUMERIC_COLS } from "../utils/constants";
import { mergeRawIntoTreated } from "../utils/data";
import { formatNumber, kpiInt } from "../utils/formatters";
import { classificaAQI, classificaPoluente } from "../utils/classifiers";

// Tipos
// Tipos
import type { RioData } from "../types/data";

export default function AnaliseRio() {
  // Estados para controles
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

  // Carregar dados
  const { data: rawData, loading: rawLoading, error: rawError } = useCsvData(
    DATA_URLS.RIO_RAW,
    rioDataParser,
    'rio-raw'
  );
  
  const { data: treatedData, loading: treatedLoading, error: treatedError } = useCsvData(
    DATA_URLS.RIO_TREATED,
    rioDataParser,
    'rio-treated'
  );

  // Merge dos dados
  const mergedData = useMemo(() => {
    if (!rawData.length || !treatedData.length) return [];
    return mergeRawIntoTreated(rawData as RioData[], treatedData as RioData[]);
  }, [rawData, treatedData]);

  // Filtros
  const { dateRange, setDateRange, filterByDate } = useDateFilter<RioData>();
  const filteredData = useMemo(() => {
    return filterByDate(mergedData);
  }, [mergedData, filterByDate]);

  // Variáveis disponíveis
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

  // Métricas principais
  const metrics = useMemo(() => {
    if (!filteredData.length) return null;
    
    const uniqueDays = new Set(filteredData.map(d => d.data_dia.toISOString().slice(0, 10))).size;
    const avgRain = filteredData.reduce((sum, d) => sum + (d.chuva || 0), 0) / filteredData.length;
    const avgTemp = filteredData.reduce((sum, d) => sum + (d.temp || 0), 0) / filteredData.length;
    const avgUR = filteredData.reduce((sum, d) => sum + (d.ur || 0), 0) / filteredData.length;
    const avgAQI = filteredData.reduce((sum, d) => sum + (d.AQI || 0), 0) / filteredData.length;
    
    return { uniqueDays, avgRain, avgTemp, avgUR, avgAQI };
  }, [filteredData]);

  // Dados para gráficos usando hooks
  const aqiTimeSeries = useTimeSeriesStats(filteredData, 'data_dia', 'AQI', 30);
  const multiVarSeries = useMultiVarSeries(filteredData, 'data_dia', selectedVars, 30);
  const heatmapData = useHeatmapData(filteredData, 'ano', 'mes', heatmapVar, heatmapAgg);
  const correlationData = useCorrelationMatrix(filteredData, correlationVars);
  const monthlyStats = useGroupStats(filteredData, 'mes', boxplotVar as keyof RioData);
  const completenessData = useCompleteness(filteredData, NUMERIC_COLS);
  const extremeDays = useExtremeData(filteredData, 'data_dia', extremeVar, extremeCount);

  // Dados para scatter plot
  const scatterData = useMemo(() => {
    if (!filteredData.length || scatterX === scatterY) return null;
    
    return filteredData
      .filter(d => d[scatterX] !== undefined && d[scatterY] !== undefined && 
               !isNaN(d[scatterX]!) && !isNaN(d[scatterY]!))
      .map(d => ({
        x: d[scatterX]!,
        y: d[scatterY]!
      }));
  }, [filteredData, scatterX, scatterY]);

  // Boxplot por mês (versão alternativa ao hook useGroupStats)
  const boxplotData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const dataByMonth: { [key: number]: number[] } = {};
    MONTH_LABELS.forEach((_, index) => {
      dataByMonth[index + 1] = [];
    });
    
    filteredData.forEach(d => {
      if (d[boxplotVar] !== undefined && !isNaN(d[boxplotVar]!)) {
        dataByMonth[d.mes].push(d[boxplotVar]!);
      }
    });
    
    return MONTH_LABELS.map((label, index) => ({
      month: label,
      values: dataByMonth[index + 1]
    }));
  }, [filteredData, boxplotVar]);

  // Loading e error states
  const loading = rawLoading || treatedLoading;
  const error = rawError || treatedError;

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
            <MetricCard 
              value={kpiInt(metrics.uniqueDays)} 
              label="Dias no período" 
            />
            <MetricCard 
              value={formatNumber(metrics.avgRain)} 
              label="Chuva média diária (mm)" 
            />
            <MetricCard 
              value={formatNumber(metrics.avgTemp)} 
              label="Temperatura média (°C)" 
            />
            <MetricCard 
              value={formatNumber(metrics.avgUR)} 
              label="UR média (%)" 
            />
            <MetricCard 
              value={formatNumber(metrics.avgAQI)} 
              label="AQI médio" 
              subLabel={classificaAQI(metrics.avgAQI) || '–'}
            />
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
                y: aqiTimeSeries.values,
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
      {multiVarSeries && (
        <div style={{ marginBottom: 24 }}>
          <h2>📈 Tendência diária (MM30) — variáveis sobrepostas</h2>
          <div style={{ marginBottom: 16, maxWidth: '400px' }}>
            <MultiSelect 
              label="Selecione variáveis"
              options={availableVariables}
              selected={selectedVars}
              onChange={setSelectedVars}
              size={8}
              withAllOption={false} // Não usar "Todos" aqui, pois queremos seleção múltipla
              style={{ marginBottom: '16px' }}
            />
            <div style={{ fontSize: '0.9em', color: '#666' }}>
              Mantenha CTRL (Cmd no Mac) pressionado para seleção múltipla
            </div>
          </div>
          <Plot
            data={multiVarSeries.map(series => ({
              x: series.dates,
              y: series.normalized,
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
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 2fr', 
            gap: '24px',
            marginBottom: '16px' 
          }}>
            <div>
              <MultiSelect 
                label="Variáveis para correlação"
                options={availableVariables}
                selected={correlationVars}
                onChange={setCorrelationVars}
                size={10}
                withAllOption={false}
              />
              <div style={{ fontSize: '0.9em', color: '#666', marginTop: '8px' }}>
                Selecione pelo menos 2 variáveis
              </div>
            </div>
            <div>
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
                style={{ width: '100%', height: 400 }}
              />
            </div>
          </div>
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