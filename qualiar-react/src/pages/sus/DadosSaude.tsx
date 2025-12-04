import React, { useState } from "react";
import Plot from "react-plotly.js";
import { useSusData, useSusFilterOptions, useFilteredSusData } from "../../hooks/useSusData";
import { 
  useSusMetrics, 
  useSusTimeSeries, 
  useSusSexDistribution, 
  useSusHeatmapData 
} from "../../hooks/useSusStats";
import { MetricCard } from "../../components/common/MetricCard";
import { SimpleMultiSelect } from "../../components/common/SimpleMultiSelect";
import { DateRangePicker } from "../../components/common/DateRangePicker";
import { MONTH_LABELS } from "../../utils/constants";
import { formatNumber, formatPercent } from "../../utils/formatters";
import "./DadosSaude.css";

export default function DadosSaudeAvancado() {
  // Carregar dados
  const { data: allData, loading, error } = useSusData();

  // Estados de filtro
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [selectedSex, setSelectedSex] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([]);
  const [selectedDiagnosisGroups, setSelectedDiagnosisGroups] = useState<string[]>([]);
  const [selectedYears, setSelectedYears] = useState<string[]>([]);

  // Estados de configuração
  const [showLabels, setShowLabels] = useState(true);
  const [yLogScale, setYLogScale] = useState(false);
  const [showPandemicLines, setShowPandemicLines] = useState(true);

  // Inicializar date range quando dados carregarem
  React.useEffect(() => {
    if (allData.length > 0 && !dateRange[0] && !dateRange[1]) {
      const dates = allData
        .map(item => item.DT_INTER as Date)
        .filter(date => date !== null) as Date[];
      
      if (dates.length > 0) {
        const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
        const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
        setDateRange([minDate, maxDate]);
      }
    }
  }, [allData, dateRange]);

  // Opções de filtro
  const filterOptions = useSusFilterOptions(allData);

  // Dados filtrados
  const filteredData = useFilteredSusData(allData, {
    dateRange,
    selectedSex,
    selectedAgeGroups,
    selectedDiagnosisGroups,
    selectedYears
  });

  // Estatísticas usando hooks
  const metrics = useSusMetrics(filteredData);
  const timeSeriesData = useSusTimeSeries(filteredData);
  const sexDistributionData = useSusSexDistribution(filteredData);
  const heatmapData = useSusHeatmapData(filteredData);

  if (loading) return (
    <div className="loading-state">
      <div>Carregando dados do SUS...</div>
      <div style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
        Carregando funcionalidades avançadas
      </div>
    </div>
  );

  if (error) return (
    <div className="error-state">
      {error}
      <button 
        onClick={() => window.location.reload()}
        style={{ marginLeft: '10px', padding: '5px 10px' }}
      >
        Recarregar
      </button>
    </div>
  );

  return (
    <div className="dados-saude-container">
      <h1 className="dados-saude-title">🩺 SIH/SUS — Internações Respiratórias (RJ) - Versão Avançada</h1>

      {/* Filtros Avançados */}
      <div className="filtros-container">
        <h3>🔎 Filtros Principais</h3>
        <div className="filtros-grid">
          {/* Date Range Picker */}
          <DateRangePicker
            label="Período"
            dateRange={dateRange}
            onChange={setDateRange}
          />

          {/* Filtro por Ano */}
          {filterOptions.anos.length > 0 && (
            <SimpleMultiSelect
              label="Ano"
              options={filterOptions.anos}
              selected={selectedYears}
              onChange={setSelectedYears}
              size={5}
            />
          )}

          {/* Filtro por Sexo */}
          {filterOptions.sexo.length > 0 && (
            <SimpleMultiSelect
              label="Sexo"
              options={filterOptions.sexo}
              selected={selectedSex}
              onChange={setSelectedSex}
              size={4}
            />
          )}

          {/* Filtro por Faixa Etária */}
          {filterOptions.faixaEtaria.length > 0 && (
            <SimpleMultiSelect
              label="Faixa Etária"
              options={filterOptions.faixaEtaria}
              selected={selectedAgeGroups}
              onChange={setSelectedAgeGroups}
              size={5}
            />
          )}

          {/* Filtro por Grupo de Diagnóstico */}
          {filterOptions.grupos.length > 0 && (
            <SimpleMultiSelect
              label="Grupo CID-10"
              options={filterOptions.grupos}
              selected={selectedDiagnosisGroups}
              onChange={setSelectedDiagnosisGroups}
              size={6}
            />
          )}
        </div>
      </div>

      {/* Métricas Completas */}
      {metrics && (
        <div className="section">
          <h2 className="section-title">📊 Visão Geral</h2>
          <div className="metricas-grid">
            <MetricCard 
              value={metrics.totalInternacoes.toLocaleString('pt-BR')} 
              label="Total de Internações"
              icon="🏥"
            />
            <MetricCard 
              value={formatNumber(metrics.mediaIdade)} 
              label="Idade Média"
              icon="👤"
            />
            <MetricCard 
              value={formatPercent(metrics.taxaMortalidade)} 
              label="Taxa de Mortalidade"
              icon="⚰️"
            />
            <MetricCard 
              value={formatNumber(metrics.mediaPermanencia)} 
              label="Permanência Média (dias)"
              icon="⏱️"
            />
          </div>
          <div className="contador-registros">
            Mostrando {filteredData.length.toLocaleString('pt-BR')} de {allData.length.toLocaleString('pt-BR')} registros
          </div>
        </div>
      )}

      {/* Série Temporal Avançada */}
      {timeSeriesData && timeSeriesData.dates.length > 0 && (
        <div className="section">
          <h2 className="section-title">⏱️ Série Temporal de Internações</h2>
          <div className="config-group">
            <label className="config-checkbox">
              <input
                type="checkbox"
                checked={yLogScale}
                onChange={(e) => setYLogScale(e.target.checked)}
              />
              Escala logarítmica
            </label>
            <label className="config-checkbox">
              <input
                type="checkbox"
                checked={showPandemicLines}
                onChange={(e) => setShowPandemicLines(e.target.checked)}
              />
              Marcar período pandêmico
            </label>
          </div>
          
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: timeSeriesData.dates,
                  y: timeSeriesData.counts,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Diário',
                  opacity: 0.3,
                  line: { width: 1, color: '#1f77b4' }
                } as any,
                {
                  x: timeSeriesData.dates,
                  y: timeSeriesData.ma7,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'MM7',
                  line: { width: 2, color: '#ff7f0e' }
                } as any,
                {
                  x: timeSeriesData.dates,
                  y: timeSeriesData.ma30,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'MM30',
                  line: { width: 3, color: '#2ca02c' }
                } as any,
              ]}
              layout={{
                title: { text: 'Evolução Temporal das Internações' },
                xaxis: { title: { text: 'Data' } },
                yaxis: { 
                  title: { text: 'Internações por Dia' },
                  type: yLogScale ? 'log' : 'linear'
                },
                margin: { l: 60, r: 20, t: 50, b: 50 },
                hovermode: 'x unified',
                ...(showPandemicLines && {
                  shapes: [
                    {
                      type: 'rect',
                      x0: '2020-03-01',
                      x1: '2022-05-22',
                      y0: 0,
                      y1: 1,
                      yref: 'paper',
                      fillcolor: '#ffcccc',
                      opacity: 0.2,
                      line: { width: 0 }
                    }
                  ],
                  annotations: [
                    {
                      x: '2020-03-01',
                      y: 1,
                      yref: 'paper',
                      text: 'Pandemia COVID-19',
                      showarrow: false,
                      yshift: 10,
                      align: 'left',
                      font: { color: '#D62728', size: 12 }
                    }
                  ]
                })
              }}
              style={{ width: '100%', height: 500 }}
            />
          </div>
        </div>
      )}

      {/* Heatmaps de Sazonalidade */}
      {heatmapData && heatmapData.data.length > 0 && (
        <div className="section">
          <h2 className="section-title">🔥 Sazonalidade (Ano x Mês)</h2>
          <div className="config-group">
            <label className="config-checkbox">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
              />
              Mostrar valores
            </label>
          </div>
          
          <div className="heatmaps-grid">
            <div className="heatmap-container">
              <h3>Contagem Absoluta</h3>
              <Plot
                data={[{
                  z: heatmapData.data,
                  x: MONTH_LABELS,
                  y: heatmapData.years,
                  type: 'heatmap',
                  colorscale: 'Blues',
                  text: showLabels ? heatmapData.data.map(row => row.map(val => val.toString())) : undefined,
                  texttemplate: showLabels ? "%{z}" : undefined,
                } as any]}
                layout={{
                  xaxis: { title: { text: 'Mês' } },
                  yaxis: { title: { text: 'Ano' } },
                  margin: { l: 60, r: 20, t: 40, b: 50 },
                }}
                style={{ width: '100%', height: 400 }}
              />
            </div>
            
            <div className="heatmap-container">
              <h3>Participação Percentual</h3>
              <Plot
                data={[{
                  z: heatmapData.data.map(row => {
                    const total = row.reduce((sum, val) => sum + val, 0);
                    return total > 0 ? row.map(val => (val / total) * 100) : row;
                  }),
                  x: MONTH_LABELS,
                  y: heatmapData.years,
                  type: 'heatmap',
                  colorscale: 'Viridis',
                  text: showLabels ? heatmapData.data.map(row => {
                    const total = row.reduce((sum, val) => sum + val, 0);
                    return total > 0 ? row.map(val => ((val / total) * 100).toFixed(1)) : row.map(() => '0');
                  }) : undefined,
                  texttemplate: showLabels ? "%{z:.1f}%" : undefined,
                } as any]}
                layout={{
                  xaxis: { title: { text: 'Mês' } },
                  yaxis: { title: { text: 'Ano' } },
                  margin: { l: 60, r: 20, t: 40, b: 50 },
                }}
                style={{ width: '100%', height: 400 }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Distribuição por Sexo */}
      {sexDistributionData && (
        <div className="section">
          <h2 className="section-title">👥 Distribuição por Sexo</h2>
          <div className="distribution-grid">
            <div className="chart-container">
              <Plot
                data={[{
                  values: Object.values(sexDistributionData),
                  labels: Object.keys(sexDistributionData),
                  type: 'pie',
                  hole: 0.4,
                  marker: {
                    colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                  }
                } as any]}
                layout={{
                  title: { text: 'Proporção por Sexo' },
                  margin: { l: 20, r: 20, t: 40, b: 20 },
                }}
                style={{ width: '100%', height: 400 }}
              />
            </div>
            
            <div className="chart-container">
              <Plot
                data={[{
                  x: Object.values(sexDistributionData),
                  y: Object.keys(sexDistributionData),
                  type: 'bar',
                  orientation: 'h',
                  marker: {
                    color: '#1f77b4'
                  }
                } as any]}
                layout={{
                  title: { text: 'Internações por Sexo' },
                  xaxis: { title: { text: 'Número de Internações' } },
                  yaxis: { title: { text: 'Sexo' } },
                  margin: { l: 60, r: 20, t: 40, b: 50 },
                }}
                style={{ width: '100%', height: 400 }}
              />
            </div>
          </div>
        </div>
      )}

      <div className="footer">
        Versão Avançada • Dados SIH/SUS • Rio de Janeiro
      </div>
    </div>
  );
}