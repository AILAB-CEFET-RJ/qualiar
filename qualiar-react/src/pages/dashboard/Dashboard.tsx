import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import Papa from "papaparse";
import "./dashboard.css";

// Traduções dos poluentes
const POLUENTES_TRADUCAO: Record<string, string> = {
  pm2_5: "PM2.5 (µg/m³)",
  pm10: "PM10 (µg/m³)",
  co: "Monóxido de Carbono (CO)",
  no: "Óxido de Nitrogênio (NO)",
  no2: "Dióxido de Nitrogênio (NO₂)",
  nox: "Óxidos de Nitrogênio (NOx)",
  so2: "Dióxido de Enxofre (SO₂)",
  o3: "Ozônio (O₃)",
  chuva: "Precipitação (mm)",
  temp: "Temperatura (°C)",
  ur: "Umidade Relativa (%)",
};
 
// URLs de dados (iguais às do Python)
const SENSOR_URLS: Record<string, string> = {
  bangu: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_bangu_preenchido.csv",
  campo_grande: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_campo_grande_preenchido.csv",
  pedra_guaratiba: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_pedra_guaratiba_preenchido.csv",
  iraja: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_iraja_preenchido.csv",
  sao_cristovao: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_sao_cristovao_preenchido.csv",
  tijuca: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_tijuca_preenchido.csv",
  centro: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_centro_preenchido.csv",
  copacabana: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/Sensors/por_estacao/df_sensor_copacabana_preenchido.csv",
};

const SUS_URLS = [
  "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2018.csv",
  "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/dados_filtrados_2019.csv",
];

type SensorRow = Record<string, string | number>;

export default function Dashboard() {
  const [sensorData, setSensorData] = useState<SensorRow[]>([]);
  const [susData, setSusData] = useState<SensorRow[]>([]);
  const [pagina, setPagina] = useState<"sensores" | "saude" | "correlacao">("sensores");

  const [estacaoSel, setEstacaoSel] = useState<string>("Geral");
  const [poluentesSel, setPoluentesSel] = useState<string[]>(["pm2_5", "temp"]);
  const [anosSel, setAnosSel] = useState<number[]>([]);
  const [mesesSel, setMesesSel] = useState<number[]>([1]);

  const [loading, setLoading] = useState(true);

  // ---------------------------------------------------
  // 1. Carregar dados de sensores e SUS
  // ---------------------------------------------------
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const sensorPromises = Object.values(SENSOR_URLS).map((url) =>
          fetch(url).then((r) => r.text()).then((t) => Papa.parse(t, { header: true, dynamicTyping: true }).data)
        );
        const susPromises = SUS_URLS.map((url) =>
          fetch(url).then((r) => r.text()).then((t) => Papa.parse(t, { header: true, dynamicTyping: true }).data)
        );

        const allSensors = (await Promise.all(sensorPromises)).flat() as SensorRow[];
        const allSUS = (await Promise.all(susPromises)).flat() as SensorRow[];

        setSensorData(allSensors);
        setSusData(allSUS);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const estacoes = useMemo(() => {
    const unique = Array.from(new Set(sensorData.map((r) => r["nome_estacao"] as string))).filter(Boolean);
    return ["Geral", ...unique];
  }, [sensorData]);

  const anosDisponiveis = useMemo(() => {
    const anos = Array.from(new Set(sensorData.map((r) => Number(r["ano"])))).filter((a) => !isNaN(a));
    return anos.sort((a, b) => a - b);
  }, [sensorData]);

  const meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
  ];

  // ---------------------------------------------------
  // 2. Filtragem
  // ---------------------------------------------------
  const filtrado = useMemo(() => {
    if (!sensorData.length) return [];
    return sensorData.filter((r) => {
      const e = r["nome_estacao"];
      const a = Number(r["ano"]);
      const m = Number(r["mes"]);
      const matchEst = estacaoSel === "Geral" || e === estacaoSel;
      const matchAno = anosSel.length === 0 || anosSel.includes(a);
      const matchMes = mesesSel.length === 0 || mesesSel.includes(m);
      return matchEst && matchAno && matchMes;
    });
  }, [sensorData, estacaoSel, anosSel, mesesSel]);

  // ---------------------------------------------------
  // 3. Página: Correlação Poluentes x Doenças
  // ---------------------------------------------------
  const correlacao = useMemo(() => {
    if (!filtrado.length || !susData.length) return null;

    const dfSensor = filtrado.filter((r) => r["ano"] && r["mes"]);
    const dfSUS = susData.filter((r) => r["ANO_CMPT"] && r["MES_CMPT"]);

    const merged: Record<string, number[]> = {};
    const variaveis = [
      "pm2_5", "pm10", "co", "o3", "no", "no2", "nox", "so2", "chuva", "temp", "ur",
    ];

    variaveis.forEach((v) => {
      merged[v] = dfSensor.map((r) => Number(r[v]));
    });
    merged["internacoes"] = dfSUS.map((r) => Number(r["num_internacoes"] || 0));

    // cálculo simples de correlação
    const pearson = (x: number[], y: number[]) => {
      const n = Math.min(x.length, y.length);
      const a = x.slice(0, n);
      const b = y.slice(0, n);
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
      return den === 0 ? 0 : num / den;
    };

    const matriz: number[][] = variaveis.map((v1) =>
      variaveis.map((v2) => pearson(merged[v1], merged[v2]))
    );

    return { matriz, variaveis };
  }, [filtrado, susData]);

  // ---------------------------------------------------
  // 4. Render
  // ---------------------------------------------------
  if (loading) {
    return <div className="dashboard-loading">Carregando dados...</div>;
  }

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <h2>Menu de Navegação</h2>
        <ul>
          <li className={pagina === "sensores" ? "active" : ""} onClick={() => setPagina("sensores")}>Análise de Sensores</li>
          <li className={pagina === "saude" ? "active" : ""} onClick={() => setPagina("saude")}>Dados de Saúde</li>
          <li className={pagina === "correlacao" ? "active" : ""} onClick={() => setPagina("correlacao")}>Poluentes x Doenças</li>
        </ul>
      </aside>

      <main className="main-content">
        {pagina === "sensores" && (
          <>
            <h1>Análise de Dados de Sensores Ambientais</h1>

            <div className="filters">
              <label>Estação:</label>
              <select value={estacaoSel} onChange={(e) => setEstacaoSel(e.target.value)}>
                {estacoes.map((e) => (
                  <option key={e}>{e}</option>
                ))}
              </select>

              <label>Variáveis:</label>
              <select
                multiple
                value={poluentesSel}
                onChange={(e) => setPoluentesSel(Array.from(e.target.selectedOptions).map((o) => o.value))}
              >
                {Object.keys(POLUENTES_TRADUCAO).map((p) => (
                  <option key={p} value={p}>
                    {POLUENTES_TRADUCAO[p]}
                  </option>
                ))}
              </select>

              <label>Anos:</label>
              <select
                multiple
                value={anosSel.map(String)}
                onChange={(e) => setAnosSel(Array.from(e.target.selectedOptions).map((o) => Number(o.value)))}
              >
                {anosDisponiveis.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>

              <label>Meses:</label>
              <select
                multiple
                value={mesesSel.map(String)}
                onChange={(e) => setMesesSel(Array.from(e.target.selectedOptions).map((o) => Number(o.value)))}
              >
                {meses.map((m, i) => (
                  <option key={i + 1} value={i + 1}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {poluentesSel.map((p) => (
              <Plot
                key={p}
                data={[
                  {
                    x: filtrado.map((r) => r["data_formatada"]),
                    y: filtrado.map((r) => Number(r[p])),
                    type: "scatter",
                    mode: "lines+markers",
                    name: POLUENTES_TRADUCAO[p],
                  },
                ]}
                layout={{
                  title: { text: POLUENTES_TRADUCAO[p] },
                  xaxis: { title: { text: "Data" } },
                  yaxis: { title: { text: POLUENTES_TRADUCAO[p] } },
                  margin: { t: 40, b: 50, l: 50, r: 10 },
                }}
                style={{ width: "100%", height: 400 }}
              />
            ))}
          </>
        )}

        {pagina === "correlacao" && correlacao && (
          <>
            <h1>Correlação: Poluentes x Doenças Respiratórias</h1>
            <Plot
              data={[
                {
                  z: correlacao.matriz,
                  x: correlacao.variaveis,
                  y: correlacao.variaveis,
                  type: "heatmap",
                  colorscale: "RdBu",
                  reversescale: true,
                  zmin: -1,
                  zmax: 1,
                },
              ]}
              layout={{
                title: { text: "Matriz de Correlação" },
                margin: { l: 80, r: 40, t: 40, b: 80 },
              }}
              style={{ width: "100%", height: 600 }}
            />
          </>
        )}
      </main>
    </div>
  );
}
