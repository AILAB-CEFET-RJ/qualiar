import React, { useEffect, useState, useMemo } from "react";
import Plot from "react-plotly.js";
import { loadOptimizedSUSData } from "../services/optimizedDataLoader";
import "./DadosSaude.css";

interface SUSData {
  DT_INTER?: string;
  IDADE?: number;
  SEXO?: string;
  SEXO_TXT?: string;
  DIAG_PRINC?: string;
  DIAS_PERM?: number;
  MORTE?: number;
  ANO?: number;
  MES?: number;
  CID_GRUPO_J?: string;
  MUNIC_RES?: string;
  FAIXA_ETARIA?: string;
  [key: string]: any;
}

const MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

// Componente MultiSelect melhorado
const MultiSelectWithAll = ({ 
  label, 
  options, 
  selected, 
  onChange 
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
}) => {
  const allOptions = ['Todos', ...options];
  const isAllSelected = selected.length === 0 || selected.length === options.length;
  
  const handleChange = (newSelected: string[]) => {
    if (newSelected.includes('Todos') || newSelected.length === 0) {
      onChange([]);
    } else {
      onChange(newSelected.filter(opt => opt !== 'Todos'));
    }
  };
  
  return (
    <div className="filtro-group">
      <label>{label}:</label>
      <select 
        multiple 
        value={isAllSelected ? ['Todos'] : selected}
        onChange={(e) => {
          const selectedOptions = Array.from(e.target.selectedOptions, opt => opt.value);
          handleChange(selectedOptions);
        }}
        className="filtro-select"
      >
        {allOptions.map(option => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </div>
  );
};

export default function DadosSaudeAvancado() {
  const [data, setData] = useState<SUSData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros principais
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [selectedSex, setSelectedSex] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([]);
  const [selectedDiagnosisGroups, setSelectedDiagnosisGroups] = useState<string[]>([]);
  const [selectedYears, setSelectedYears] = useState<string[]>([]);

  // Configurações
  const [showLabels, setShowLabels] = useState(true);
  const [yLogScale, setYLogScale] = useState(false);
  const [showPandemicLines, setShowPandemicLines] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const susData = await loadOptimizedSUSData();
        
        const processedData = susData.map(item => ({
          ...item,
          IDADE: toNumber(item.IDADE),
          DIAS_PERM: toNumber(item.DIAS_PERM),
          MORTE: toNumber(item.MORTE),
          ANO: toNumber(item.ANO),
          MES: toNumber(item.MES),
        }));

        setData(processedData);

        // Definir range de datas inicial
        if (processedData.length > 0) {
          const dates = processedData
            .map(item => parseDate(item.DT_INTER || ''))
            .filter(date => date !== null) as Date[];
          
          if (dates.length > 0) {
            const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
            const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
            setDateRange([minDate, maxDate]);
          }
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
        setError("Erro ao carregar dados. Tente recarregar a página.");
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Dados filtrados
  const filteredData = useMemo(() => {
    if (!data.length) return [];
    
    let filtered = data;

    // Filtro por data
    if (dateRange[0] && dateRange[1]) {
      filtered = filtered.filter(item => {
        const itemDate = parseDate(item.DT_INTER || '');
        return itemDate && itemDate >= dateRange[0]! && itemDate <= dateRange[1]!;
      });
    }

    // Filtro por sexo
    if (selectedSex.length > 0) {
      const sexoCol = data[0].SEXO_TXT ? 'SEXO_TXT' : 'SEXO';
      filtered = filtered.filter(item => 
        selectedSex.includes(item[sexoCol]?.toString() || '')
      );
    }

    // Filtro por faixa etária
    if (selectedAgeGroups.length > 0) {
      filtered = filtered.filter(item => 
        selectedAgeGroups.includes(item.FAIXA_ETARIA?.toString() || '')
      );
    }

    // Filtro por grupo de diagnóstico
    if (selectedDiagnosisGroups.length > 0) {
      filtered = filtered.filter(item => 
        selectedDiagnosisGroups.includes(item.CID_GRUPO_J?.toString() || '')
      );
    }

    // Filtro por ano
    if (selectedYears.length > 0) {
      filtered = filtered.filter(item => 
        selectedYears.includes(item.ANO?.toString() || '')
      );
    }

    return filtered;
  }, [data, dateRange, selectedSex, selectedAgeGroups, selectedDiagnosisGroups, selectedYears]);

  // Opções para filtros
  const filterOptions = useMemo(() => {
    if (!data.length) return null;
    
    const sexoCol = data[0].SEXO_TXT ? 'SEXO_TXT' : 'SEXO';
    
    return {
      sexo: Array.from(new Set(data.map(d => d[sexoCol]).filter(Boolean))).map(String),
      faixaEtaria: Array.from(new Set(data.map(d => d.FAIXA_ETARIA).filter(Boolean))).map(String),
      grupos: Array.from(new Set(data.map(d => d.CID_GRUPO_J).filter(Boolean))).map(String),
      anos: Array.from(new Set(data.map(d => d.ANO).filter(Boolean))).sort((a, b) => Number(b) - Number(a)).map(String),
    };
  }, [data]);

  // Métricas principais
  const metrics = useMemo(() => {
    if (!filteredData.length) return null;
    
    const totalInternacoes = filteredData.length;
    
    const idadeValues = filteredData
      .map(item => item.IDADE)
      .filter((age): age is number => age !== undefined && !isNaN(age));
    const mediaIdade = idadeValues.length > 0 ? idadeValues.reduce((sum, age) => sum + age, 0) / idadeValues.length : NaN;
    
    const morteValues = filteredData
      .map(item => item.MORTE)
      .filter((morte): morte is number => morte !== undefined && !isNaN(morte));
    const taxaMortalidade = morteValues.length > 0 ? morteValues.reduce((sum, morte) => sum + morte, 0) / morteValues.length : NaN;
    
    const permanenciaValues = filteredData
      .map(item => item.DIAS_PERM)
      .filter((perm): perm is number => perm !== undefined && !isNaN(perm));
    const mediaPermanencia = permanenciaValues.length > 0 ? permanenciaValues.reduce((sum, perm) => sum + perm, 0) / permanenciaValues.length : NaN;
    
    return { totalInternacoes, mediaIdade, taxaMortalidade, mediaPermanencia };
  }, [filteredData]);

  // Dados para série temporal
  const timeSeriesData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const dailyCounts: { [key: string]: number } = {};
    filteredData.forEach(item => {
      if (item.DT_INTER) {
        const date = item.DT_INTER.split('T')[0];
        dailyCounts[date] = (dailyCounts[date] || 0) + 1;
      }
    });
    
    const dates = Object.keys(dailyCounts).sort();
    const counts = dates.map(date => dailyCounts[date]);
    const ma7 = calculateRollingAverage(counts, 7);
    const ma30 = calculateRollingAverage(counts, 30);
    
    return { dates: dates.map(d => new Date(d)), counts, ma7, ma30 };
  }, [filteredData]);

  // Dados para heatmaps
  const heatmapData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const countsByYearMonth: { [key: string]: number } = {};
    filteredData.forEach(item => {
      if (item.ANO && item.MES) {
        const key = `${item.ANO}-${item.MES}`;
        countsByYearMonth[key] = (countsByYearMonth[key] || 0) + 1;
      }
    });
    
    const years = Array.from(new Set(filteredData.map(d => d.ANO).filter(Boolean))).sort() as number[];
    const data: number[][] = [];
    
    years.forEach(year => {
      const row: number[] = [];
      [1,2,3,4,5,6,7,8,9,10,11,12].forEach(month => {
        const key = `${year}-${month}`;
        row.push(countsByYearMonth[key] || 0);
      });
      data.push(row);
    });
    
    return {
      years: years.map(y => y.toString()),
      data
    };
  }, [filteredData]);

  // Dados para distribuição por sexo
  const sexDistributionData = useMemo(() => {
    if (!filteredData.length) return null;
    
    const sexoCol = filteredData[0].SEXO_TXT ? 'SEXO_TXT' : 'SEXO';
    const sexCounts: { [key: string]: number } = {};
    
    filteredData.forEach(item => {
      const sex = item[sexoCol]?.toString() || 'Não informado';
      sexCounts[sex] = (sexCounts[sex] || 0) + 1;
    });
    
    return sexCounts;
  }, [filteredData]);

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
          <div className="filtro-group">
            <label>Período: </label>
            <div className="date-input-group">
              <input
                type="date"
                className="date-input"
                value={dateRange[0]?.toISOString().slice(0, 10) || ''}
                onChange={(e) => setDateRange([e.target.value ? new Date(e.target.value) : null, dateRange[1]])}
              />
              <span>até</span>
              <input
                type="date"
                className="date-input"
                value={dateRange[1]?.toISOString().slice(0, 10) || ''}
                onChange={(e) => setDateRange([dateRange[0], e.target.value ? new Date(e.target.value) : null])}
              />
            </div>
          </div>

          {filterOptions && (
            <>
              <MultiSelectWithAll
                label="Ano"
                options={filterOptions.anos}
                selected={selectedYears}
                onChange={setSelectedYears}
              />
              
              <MultiSelectWithAll
                label="Sexo"
                options={filterOptions.sexo}
                selected={selectedSex}
                onChange={setSelectedSex}
              />
              
              <MultiSelectWithAll
                label="Faixa Etária"
                options={filterOptions.faixaEtaria}
                selected={selectedAgeGroups}
                onChange={setSelectedAgeGroups}
              />
              
              <MultiSelectWithAll
                label="Grupo CID-10"
                options={filterOptions.grupos}
                selected={selectedDiagnosisGroups}
                onChange={setSelectedDiagnosisGroups}
              />
            </>
          )}
        </div>
      </div>

      {/* Métricas Completas */}
      {metrics && (
        <div className="section">
          <h2 className="section-title">📊 Visão Geral</h2>
          <div className="metricas-grid">
            <div className="metrica-card">
              <div className="metrica-valor">{metrics.totalInternacoes.toLocaleString('pt-BR')}</div>
              <div className="metrica-label">Total de Internações</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-valor">{formatNumber(metrics.mediaIdade)}</div>
              <div className="metrica-label">Idade Média</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-valor">{formatPercent(metrics.taxaMortalidade)}</div>
              <div className="metrica-label">Taxa de Mortalidade</div>
            </div>
            <div className="metrica-card">
              <div className="metrica-valor">{formatNumber(metrics.mediaPermanencia)}</div>
              <div className="metrica-label">Permanência Média</div>
            </div>
          </div>
          <div className="contador-registros">
            Mostrando {filteredData.length.toLocaleString('pt-BR')} de {data.length.toLocaleString('pt-BR')} registros
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
                  line: { width: 1 }
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div className="chart-container">
              <Plot
                data={[{
                  values: Object.values(sexDistributionData),
                  labels: Object.keys(sexDistributionData),
                  type: 'pie',
                  hole: 0.4,
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
        Versão Avançada - Funcionalidades principais implementadas
      </div>
    </div>
  );
}

// Utils
function toNumber(val: any): number {
  if (val === null || val === undefined || val === '') return NaN;
  const num = Number(val);
  return isNaN(num) ? NaN : num;
}

function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  return isNaN(date.getTime()) ? null : date;
}

function calculateRollingAverage(data: number[], window: number = 7): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - window + 1);
    const values = data.slice(start, i + 1);
    result.push(values.reduce((a, b) => a + b, 0) / values.length);
  }
  return result;
}

function formatNumber(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "–";
  return n.toFixed(1);
}

function formatPercent(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "–";
  return (n * 100).toFixed(2) + "%";
}