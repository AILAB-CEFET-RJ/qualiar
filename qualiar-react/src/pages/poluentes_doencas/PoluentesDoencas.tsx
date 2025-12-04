// PoluentesDoencas.tsx
import { useEffect, useState, useMemo, useCallback, type JSX } from "react";
import Plot from "react-plotly.js";
import { 
  loadSUSData, 
  loadRioDeJaneiroQualiarTreatedData 
} from "../../services/dataLoader";
import "./PoluentesDoencas.css"; // Importando o arquivo CSS

// Tipos para os dados
interface RioData {
  data_dia: Date | null;
  ano: number | null;
  mes: number | null;
  ano_mes: string | null;
  pm2_5?: string | number;
  temp?: string | number;
  no2?: string | number;
  o3?: string | number;
  [key: string]: any;
}

interface SUSData {
  DT_INTER?: string | Date;
  IDADE?: string | number;
  CID_CAT3?: string;
  DIAG_PRINC?: string;
  MUNIC_RES?: string;
  [key: string]: any;
}

interface FilterState {
  d_ini: Date | null;
  d_fim: Date | null;
  idade_min: number | null;
  idade_max: number | null;
  cids: string[];
  munics: string[];
}

interface CorrelationResult {
  target: string;
  variavel: string;
  janela: number;
  shift: number;
  spearman: number;
}

export default function PoluentesDoencas(): JSX.Element {
  const [sus, setSus] = useState<SUSData[]>([]);
  const [rio, setRio] = useState<RioData[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    d_ini: null,
    d_fim: null,
    idade_min: null,
    idade_max: null,
    cids: [],
    munics: [],
  });

  // Carregar dados
  useEffect(() => {
    Promise.all([loadSUSData(), loadRioDeJaneiroQualiarTreatedData()])
      .then(([d1, d2]) => {
        setSus(d1);
        setRio(d2);
      })
      .finally(() => setLoading(false));
  }, []);

  // Processar e transformar dados do SUS
  const processedSusData = useMemo(() => {
    return sus.map(item => {
      const dt_inter = item.DT_INTER ? new Date(item.DT_INTER) : null;
      const idade = item.IDADE ? Number(item.IDADE) : NaN;
      const cid_cat3 = item.CID_CAT3 || (item.DIAG_PRINC ? String(item.DIAG_PRINC).slice(0, 3) : undefined);
      
      return {
        ...item,
        DT_INTER: dt_inter,
        IDADE: isNaN(idade) ? undefined : idade,
        CID_CAT3: cid_cat3,
        MUNIC_RES: item.MUNIC_RES || undefined,
        data_dia: dt_inter ? new Date(dt_inter.getFullYear(), dt_inter.getMonth(), dt_inter.getDate()) : null,
      };
    });
  }, [sus]);

  // Filtrar dados do SUS
  const filteredSusData = useMemo(() => {
    return processedSusData.filter(item => {
      // Filtro por data
      if (filters.d_ini && filters.d_fim && item.data_dia) {
        const date = item.data_dia;
        if (date < filters.d_ini || date > filters.d_fim) return false;
      }

      // Filtro por idade
      if (filters.idade_min !== null && filters.idade_max !== null && item.IDADE !== undefined) {
        if (item.IDADE < filters.idade_min || item.IDADE > filters.idade_max) return false;
      }

      // Filtro por CID
      if (filters.cids.length > 0 && item.CID_CAT3) {
        if (!filters.cids.includes(item.CID_CAT3)) return false;
      }

      // Filtro por município
      if (filters.munics.length > 0 && item.MUNIC_RES) {
        if (!filters.munics.includes(item.MUNIC_RES)) return false;
      }

      return true;
    });
  }, [processedSusData, filters]);

  // Agregar internações por dia
  const internacoesPorDia = useMemo(() => {
    const grupos = new Map<string, number>();
    
    filteredSusData.forEach(item => {
      if (!item.data_dia) return;
      
      const key = item.data_dia.toISOString().split('T')[0];
      grupos.set(key, (grupos.get(key) || 0) + 1);
    });

    return Array.from(grupos.entries()).map(([data, internacoes]) => ({
      data_dia: new Date(data),
      internacoes
    })).sort((a, b) => a.data_dia.getTime() - b.data_dia.getTime());
  }, [filteredSusData]);

  // Mesclar com dados ambientais
  const mergedData = useMemo(() => {
    const rioMap = new Map<string, RioData>();
    rio.forEach(item => {
      if (item.data_dia) {
        const key = item.data_dia.toISOString().split('T')[0];
        rioMap.set(key, item);
      }
    });

    return internacoesPorDia.map(internacao => {
      const key = internacao.data_dia.toISOString().split('T')[0];
      const envData = rioMap.get(key);
      
      return {
        ...internacao,
        ...envData,
        pm2_5: envData?.pm2_5 ? parseFloat(String(envData.pm2_5)) : NaN,
        temp: envData?.temp ? parseFloat(String(envData.temp)) : NaN,
        no2: envData?.no2 ? parseFloat(String(envData.no2)) : NaN,
        o3: envData?.o3 ? parseFloat(String(envData.o3)) : NaN,
      };
    });
  }, [internacoesPorDia, rio]);

  // Função para calcular médias móveis
  const calcularMediaMovel = useCallback((dados: number[], janela: number): number[] => {
    const result: number[] = [];
    for (let i = 0; i < dados.length; i++) {
      const inicio = Math.max(0, i - janela + 1);
      const slice = dados.slice(inicio, i + 1);
      result.push(slice.reduce((a, b) => a + b, 0) / slice.length);
    }
    return result;
  }, []);

  // Calcular correlação
  const calcularCorrelacao = useCallback((x: number[], y: number[], method: 'pearson' | 'spearman' = 'pearson') => {
    if (x.length !== y.length || x.length < 2) return 0;
    
    if (method === 'spearman') {
      const rankX = x.map((val, idx) => ({ val, idx }))
        .sort((a, b) => a.val - b.val)
        .map((item, rank) => ({ idx: item.idx, rank: rank + 1 }));
      
      const rankY = y.map((val, idx) => ({ val, idx }))
        .sort((a, b) => a.val - b.val)
        .map((item, rank) => ({ idx: item.idx, rank: rank + 1 }));
      
      const sortedRankX = rankX.sort((a, b) => a.idx - b.idx).map(r => r.rank);
      const sortedRankY = rankY.sort((a, b) => a.idx - b.idx).map(r => r.rank);
      
      x = sortedRankX;
      y = sortedRankY;
    }
    
    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
    const sumX2 = x.reduce((sum, val) => sum + val * val, 0);
    const sumY2 = y.reduce((sum, val) => sum + val * val, 0);
    
    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    
    return denominator === 0 ? 0 : numerator / denominator;
  }, []);

  // Buscar melhores combinações (janela + lag)
  const melhoresCombinacoes = useMemo(() => {
    const resultados: CorrelationResult[] = [];
    const janelas = [3, 7, 14, 21, 30, 60, 90, 120, 150];
    const shifts = Array.from({ length: 16 }, (_, i) => i); // 0..15
    const pollutants = ['temp', 'no2', 'o3', 'pm2_5', 'co', 'so2', 'pm10'];
    
    // Preparar dados
    const internacoesD1 = mergedData.map(d => d.internacoes);
    const internacoesD7 = [...internacoesD1.slice(7), ...Array(7).fill(NaN)];
    
    pollutants.forEach(pollutant => {
      const valores = mergedData.map(d => (d as any)[pollutant] || NaN);
      
      janelas.forEach(janela => {
        const mm = calcularMediaMovel(valores, janela);
        
        shifts.forEach(shift => {
          // Correlação para D+1
          const xD1 = mm.slice(shift, -1);
          const yD1 = internacoesD1.slice(1);
          const minLength = Math.min(xD1.length, yD1.length);
          
          if (minLength >= 5) {
            const corrD1 = calcularCorrelacao(
              xD1.slice(0, minLength),
              yD1.slice(0, minLength),
              'spearman'
            );
            
            if (!isNaN(corrD1)) {
              resultados.push({
                target: 'internacoes_d1',
                variavel: pollutant,
                janela,
                shift,
                spearman: corrD1
              });
            }
          }
          
          // Correlação para D+7
          const xD7 = mm.slice(shift, -7);
          const yD7 = internacoesD7.slice(7);
          const minLengthD7 = Math.min(xD7.length, yD7.length);
          
          if (minLengthD7 >= 5) {
            const corrD7 = calcularCorrelacao(
              xD7.slice(0, minLengthD7),
              yD7.slice(0, minLengthD7),
              'spearman'
            );
            
            if (!isNaN(corrD7)) {
              resultados.push({
                target: 'internacoes_d7',
                variavel: pollutant,
                janela,
                shift,
                spearman: corrD7
              });
            }
          }
        });
      });
    });
    
    return resultados;
  }, [mergedData, calcularMediaMovel, calcularCorrelacao]);

  // Agrupar melhores por variável
  const melhoresPorVariavel = useMemo(() => {
    const grupos = new Map<string, CorrelationResult>();
    
    melhoresCombinacoes.forEach(resultado => {
      const key = `${resultado.target}_${resultado.variavel}`;
      const atual = grupos.get(key);
      
      if (!atual || Math.abs(resultado.spearman) > Math.abs(atual.spearman)) {
        grupos.set(key, resultado);
      }
    });
    
    return Array.from(grupos.values());
  }, [melhoresCombinacoes]);

  if (loading) return <div className="loading">Carregando dados combinados...</div>;

  return (
    <div className="poluentes-container">
      <h1 className="main-title">📈 Poluentes x Doenças Respiratórias — Rio de Janeiro</h1>
      
      <div className="info-box">
        <h2 className="section-title">ℹ️ Sobre esta página</h2>
        <p className="info-text">
          Cruzamos <strong>internações por doenças respiratórias (SUS)</strong> com <strong>variáveis ambientais (QualiAR)</strong>.
          <br />
          1) Filtre o <strong>SUS</strong> (período, idade, CID-10, município);<br />
          2) Agregamos as <strong>internações por dia</strong>;<br />
          3) Unimos com a série ambiental diária;<br />
          4) Exploramos <strong>correlações</strong> (lag 0 e por defasagens).
        </p>
      </div>

      {/* Estatísticas */}
      <div className="stats-box">
        <p>
          <strong>SUS:</strong> {sus.length.toLocaleString()} registros |{" "}
          <strong>QualiAR tratado:</strong> {rio.length.toLocaleString()} registros
        </p>
        <p>
          <strong>Após filtros:</strong> {filteredSusData.length.toLocaleString()} registros SUS |{" "}
          <strong>Dias com dados:</strong> {mergedData.length}
        </p>
      </div>

      {/* Gráfico PM2.5 */}
      <div className="chart-section">
        <h2 className="section-title">PM2.5 Mensal</h2>
        <Plot
          data={[
            {
              x: rio.map(r => r.ano_mes || ""),
              y: rio.map(r => {
                const val = parseFloat(String(r.pm2_5 ?? "NaN"));
                return isNaN(val) ? null : val;
              }),
              type: "bar",
              name: "PM2.5",
              marker: {
                color: rio.map(r => {
                  const val = parseFloat(String(r.pm2_5 ?? "NaN"));
                  return isNaN(val) ? 'gray' : 
                    val > 25 ? '#ff6b6b' : 
                    val > 15 ? '#ffd93d' : '#6bcf7f';
                })
              }
            },
          ]}
          layout={{
            title: { text: "PM2.5 mensal — dados tratados" },
            xaxis: { title: { text: "Ano-Mês" }, tickangle: -45 },
            yaxis: { title: { text: "PM2.5 (µg/m³)" } },
            hovermode: "closest"
          }}
          style={{ width: "100%", height: 500 }}
        />
      </div>

      {/* Série Temporal */}
      {mergedData.length > 0 && (
        <div className="chart-section">
          <h2 className="section-title">📈 Série Temporal: Internações x Variáveis Ambientais</h2>
          <Plot
            data={[
              {
                x: mergedData.map(d => d.data_dia),
                y: mergedData.map(d => d.internacoes),
                type: 'scatter',
                mode: 'lines',
                name: 'Internações',
                yaxis: 'y1',
                line: { width: 2 }
              },
              {
                x: mergedData.map(d => d.data_dia),
                y: mergedData.map(d => (isNaN(d.temp as number) ? null : d.temp)),
                type: 'scatter',
                mode: 'lines',
                name: 'Temperatura',
                yaxis: 'y2',
                line: { dash: 'solid' }
              },
              {
                x: mergedData.map(d => d.data_dia),
                y: mergedData.map(d => (isNaN(d.pm2_5 as number) ? null : d.pm2_5)),
                type: 'scatter',
                mode: 'lines',
                name: 'PM2.5',
                yaxis: 'y3',
                line: { dash: 'solid' }
              }
            ]}
            layout={{
              title: { text: 'Internações x Temperatura x PM2.5' },
              xaxis: { title: { text: 'Data' } },
              yaxis: { title: { text: 'Internações' }, side: 'left' },
              yaxis2: { title: { text: 'Temperatura (°C)' }, overlaying: 'y', side: 'right' },
              yaxis3: { title: { text: 'PM2.5 (µg/m³)' }, overlaying: 'y', side: 'right', position: 0.95 },
              hovermode: 'x unified',
              showlegend: true,
              legend: { x: 0, y: 1.2 }
            }}
            style={{ width: "100%", height: 500 }}
          />
        </div>
      )}

      {/* Correlações */}
      {melhoresPorVariavel.length > 0 && (
        <div className="chart-section">
          <h2 className="section-title">📊 Melhores Correlações (Janela + Lag)</h2>
          
          {['internacoes_d1', 'internacoes_d7'].map(target => {
            const dadosTarget = melhoresPorVariavel.filter(d => d.target === target);
            if (dadosTarget.length === 0) return null;
            
            return (
              <div key={target} className="correlation-chart">
                <h3 className="subsection-title">
                  {target === 'internacoes_d1' ? 'Internações D+1' : 'Internações D+7'}
                </h3>
                <Plot
                  data={[{
                    x: dadosTarget.map(d => `${d.variavel}<br>MM${d.janela} | lag=${d.shift}`),
                    y: dadosTarget.map(d => d.spearman),
                    type: 'bar',
                    marker: {
                      color: dadosTarget.map(d => d.spearman),
                      colorscale: 'RdBu',
                      cmin: -1,
                      cmax: 1
                    },
                    text: dadosTarget.map(d => d.spearman.toFixed(3)),
                    textposition: 'outside'
                  }]}
                  layout={{
                    title: {
                      text: `Melhor janela + lag por variável — Spearman (${
                        target === 'internacoes_d1' ? 'D+1' : 'D+7'
                      })`
                    },
                    xaxis: { title: { text: 'Variável | Melhor (MM, lag)' }, tickangle: -45 },
                    yaxis: { title: { text: 'Correlação (Spearman)' }, range: [-1.1, 1.1] },
                    shapes: [{
                      type: 'line',
                      x0: -0.5,
                      x1: dadosTarget.length - 0.5,
                      y0: 0,
                      y1: 0,
                      line: { color: '#7f8c8d', dash: 'dash' }
                    }]
                  }}
                  style={{ width: "100%", height: 400 }}
                />
              </div>
            );
          })}
        </div>
      )}

      {/* Tabela de melhores combinações */}
      {melhoresPorVariavel.length > 0 && (
        <div className="table-section">
          <h2 className="section-title">📋 Tabela — Melhores Combinações por Variável</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alvo</th>
                  <th>Variável</th>
                  <th>Janela (dias)</th>
                  <th>Lag (dias)</th>
                  <th>Correlação (Spearman)</th>
                </tr>
              </thead>
              <tbody>
                {melhoresPorVariavel
                  .sort((a, b) => Math.abs(b.spearman) - Math.abs(a.spearman))
                  .map((item, index) => (
                    <tr key={index}>
                      <td>
                        {item.target === 'internacoes_d1' ? 'D+1' : 'D+7'}
                      </td>
                      <td className="monospace">{item.variavel}</td>
                      <td className="text-center">{item.janela}</td>
                      <td className="text-center">{item.shift}</td>
                      <td className={`text-center ${
                        item.spearman > 0 ? 'positive-value' : 
                        item.spearman < 0 ? 'negative-value' : 
                        'neutral-value'
                      }`}>
                        {item.spearman.toFixed(3)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}