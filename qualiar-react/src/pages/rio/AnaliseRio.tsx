import { useState, useMemo } from "react";
import Plot from "react-plotly.js";

import { useCsvData, rioDataParser } from "../../hooks/useCsvData";
import { useDateFilter } from "../../hooks/useFilters";
import { useTimeSeriesStats, useCorrelationMatrix } from "../../hooks/useStats";
import { useHeatmapData } from "../../hooks/useHeatmapData";
import { useExtremeData } from "../../hooks/useExtremeData";
import { useCompleteness } from "../../hooks/useCompleteness";
import { useMultiVarSeries } from "../../hooks/useMultiVarSeries";
import { MultiSelect } from "../../components/common/MultiSelect";
import { DATA_URLS, MONTH_LABELS, AQI_BINS, NUMERIC_COLS } from "../../utils/constants";
import { mergeRawIntoTreated } from "../../utils/data";
import { formatNumber, kpiInt } from "../../utils/formatters";
import { classificaAQI } from "../../utils/classifiers";
import type { RioData } from "../../types/data";
import { CsvExportButton, formatDateFields } from '../../components/common/CsvExportButton';
import "./AnaliseRio.css";
import { LoadingState } from "../../components/common/LoadingState";
import {
  RioIcon,
  FilterIcon,
  StatsIcon,
  TrendIcon,
  CalendarIcon,
  CorrelationIcon,
  ScatterIcon,
  TestIcon,
  ExtremeIcon
} from '../../components/Icons';

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

  if (loading) return <LoadingState message="Carregando dados..." />;
  
  if (error) return <div className="error-state-rio">{error}</div>;

  return (
    <div className="analise-rio-container">
      <h1 className="analise-rio-title">
        <RioIcon style={{ marginRight: '10px', verticalAlign: 'middle' }} />
        Rio de Janeiro — EDA Ambiental
        <span style={{ fontSize: "0.8em", color: "#666", marginLeft: "10px" }}>
          (2012 - 2024)
        </span>
      </h1>

      {/* Filtros */}
      <div className="filtros-container">
        <h3 className="filtros-title">
          <FilterIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Filtro (global da página)
        </h3>
        <div className="filtros-grid">
          <div className="filtro-group">
            <label className="filtro-label">Data inicial</label>
            <input
              type="date"
              className="filtro-input"
              value={dateRange[0]?.toISOString().slice(0, 10) || ''}
              onChange={(e) => setDateRange([e.target.value ? new Date(e.target.value) : null, dateRange[1]])}
            />
          </div>
          <div className="filtro-group">
            <label className="filtro-label">Data final</label>
            <input
              type="date"
              className="filtro-input"
              value={dateRange[1]?.toISOString().slice(0, 10) || ''}
              onChange={(e) => setDateRange([dateRange[0], e.target.value ? new Date(e.target.value) : null])}
            />
          </div>
        </div>
      </div>

      {/* Métricas principais */}
      {metrics && (
        <div className="metricas-container">
          <h2 className="section-title-rio">
            <StatsIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Visão Geral
          </h2>
          <div className="metricas-grid">
            <div className="metrica-card">
              <div className="metrica-value">{kpiInt(metrics.uniqueDays)}</div>
              <div className="metrica-label">Dias no período</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-value">{formatNumber(metrics.avgRain)}</div>
              <div className="metrica-label">Chuva média diária (mm)</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-value">{formatNumber(metrics.avgTemp)}</div>
              <div className="metrica-label">Temperatura média (°C)</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-value">{formatNumber(metrics.avgUR)}</div>
              <div className="metrica-label">UR média (%)</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-value">{formatNumber(metrics.avgAQI)}</div>
              <div className="metrica-label">AQI médio</div>
              <div className="metrica-sub-label">{classificaAQI(metrics.avgAQI) || '-'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Série temporal AQI */}
      {aqiTimeSeries && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <StatsIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Série temporal do AQI diário (com faixas de qualidade)
          </h2>
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Tendência multivariada */}
      {multiVarSeries && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <TrendIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Tendência diária (MM30) — variáveis sobrepostas
          </h2>
          <div className="controles-container">
            <div className="controle-item">
              <label className="controle-label">Selecione variáveis</label>
              <MultiSelect 
                options={availableVariables}
                selected={selectedVars}
                onChange={setSelectedVars}
                size={8}
                withAllOption={false}
                className="filtro-select" 
                label={""}             
              />
              <div className="info-auxiliar">
                Mantenha CTRL (Cmd no Mac) pressionado para seleção múltipla
              </div>
            </div>
          </div>
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Heatmaps */}
      {heatmapData && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <CalendarIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Sazonalidade (Ano x Mês)
            </h2>
          <div className="controles-container">
            <div className="controle-item">
              <label className="controle-label">Variável</label>
              <select 
                value={heatmapVar} 
                onChange={(e) => setHeatmapVar(e.target.value)}
                className="filtro-select"
              >
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div className="controle-item">
              <label className="controle-label">Agregação</label>
              <select 
                value={heatmapAgg} 
                onChange={(e) => setHeatmapAgg(e.target.value as any)}
                className="filtro-select"
              >
                <option value="mean">Média</option>
                <option value="sum">Soma</option>
                <option value="max">Máximo</option>
              </select>
            </div>
            <div className="checkbox-container">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
              />
              <span className="checkbox-label">Mostrar rótulos</span>
            </div>
          </div>
          
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Boxplot */}
      {boxplotData && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <CalendarIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Sazonalidade mensal (boxplot)
          </h2>
          <div className="controles-container">
            <div className="controle-item">
              <label className="controle-label">Variável</label>
              <select 
                value={boxplotVar} 
                onChange={(e) => setBoxplotVar(e.target.value)}
                className="filtro-select"
              >
                {availableVariables.filter(v => v !== 'AQI').map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Correlação */}
      {correlationData && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <CorrelationIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Correlação entre variáveis
          </h2>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 2fr', 
            gap: '24px',
            marginBottom: '16px' 
          }}>
            <div className="controles-container">
              <div className="controle-item">
                <label className="controle-label">Variáveis para correlação</label>
                <MultiSelect 
                  options={availableVariables}
                  selected={correlationVars}
                  onChange={setCorrelationVars}
                  size={10}
                  withAllOption={false}
                  className="filtro-select" 
                  label={""}                
                />
                <div className="info-auxiliar">
                  Selecione pelo menos 2 variáveis
                </div>
              </div>
            </div>
            <div className="chart-container-rio" style={{ height: '400px' }}>
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
                  autosize: true,
                }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Scatter plot */}
      {scatterData && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <ScatterIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Relação entre variáveis (dispersão)
          </h2>
          <div className="controles-container">
            <div className="controle-item">
              <label className="controle-label">Eixo X</label>
              <select 
                value={scatterX} 
                onChange={(e) => setScatterX(e.target.value)}
                className="filtro-select"
              >
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div className="controle-item">
              <label className="controle-label">Eixo Y</label>
              <select 
                value={scatterY} 
                onChange={(e) => setScatterY(e.target.value)}
                className="filtro-select"
              >
                {availableVariables.map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div className="checkbox-container">
              <input
                type="checkbox"
                checked={showTrend}
                onChange={(e) => setShowTrend(e.target.checked)}
              />
              <span className="checkbox-label">Linha de tendência</span>
            </div>
          </div>
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Completude */}
      {completenessData && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <TestIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Completude por variável (não nulos %)
          </h2>
          <div className="chart-container-rio" style={{ height: '500px' }}>
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
                autosize: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Dias extremos */}
      {extremeDays && (
        <div className="section-rio">
          <h2 className="section-title-rio">
            <ExtremeIcon style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Dias extremos
          </h2>
          <div className="controles-container">
            <div className="controle-item">
              <label className="controle-label">Variável</label>
              <select 
                value={extremeVar} 
                onChange={(e) => setExtremeVar(e.target.value)}
                className="filtro-select"
              >
                {availableVariables.filter(v => v !== 'AQI').map(varName => (
                  <option key={varName} value={varName}>{varName}</option>
                ))}
              </select>
            </div>
            <div className="controle-item">
              <label className="controle-label">Quantidade: {extremeCount} dias</label>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={extremeCount}
                onChange={(e) => setExtremeCount(parseInt(e.target.value))}
                className="filtro-input"
              />
            </div>
          </div>
          <div className="tabela-container">
            <table className="tabela-extremos">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>{extremeVar}</th>
                </tr>
              </thead>
              <tbody>
                {extremeDays.map((day, index) => (
                  <tr key={index}>
                    <td>{day.date}</td>
                    <td>{day.value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Exportar dados */}
      <CsvExportButton
        data={filteredData}
        filename="rio_filtrado"
        label="Exportar dados filtrados"
        buttonText="Baixar CSV"
        iconSize={24}
        iconColor="#38a169"
        transformData={(data) => formatDateFields(data, ['data_dia'])}
      />
    </div>
  );
}