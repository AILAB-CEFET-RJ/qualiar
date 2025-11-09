import { useEffect, useState, type JSX } from "react";
import Plot from "react-plotly.js";
import { loadRioDeJaneiroQualiarData } from "../services/dataLoader";

export default function AnaliseRio(): JSX.Element {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRioDeJaneiroQualiarData()
      .then((data) => setRows(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Carregando dados do Rio de Janeiro...</div>;
  if (!rows.length) return <div>Nenhum dado carregado.</div>;

  const anos = rows.map((r) => r.ano);
  const o3 = rows.map((r) => parseFloat(r["o3"] || "NaN"));

  return (
    <div>
      <h1>Qualidade do Ar — Rio de Janeiro</h1>
      <p>{rows.length.toLocaleString()} registros carregados.</p>
      <Plot
            data={[
                { x: anos, y: o3, type: "scatter", mode: "lines", name: "O₃" },
            ]}
            layout={{
                title: { text: "Concentração média de O₃ por registro (simplificado)" },
                xaxis: { title: { text: "Ano" } },
                yaxis: { title: { text: "O₃ (μg/m³)" } },
            }}
            style={{ width: "100%", height: 500 }}
        />
    </div>
  );
}
