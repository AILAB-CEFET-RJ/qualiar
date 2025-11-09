import { useEffect, useState, type JSX } from "react";
import Plot from "react-plotly.js";
import { loadSUSData, loadRioDeJaneiroQualiarTreatedData } from "../services/dataLoader";

export default function PoluentesDoencas(): JSX.Element {
  const [sus, setSus] = useState<any[]>([]);
  const [rio, setRio] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([loadSUSData(), loadRioDeJaneiroQualiarTreatedData()])
      .then(([d1, d2]) => {
        setSus(d1);
        setRio(d2);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Carregando dados combinados...</div>;

  return (
    <div>
      <h1>Poluentes x Doenças</h1>
      <p>
        SUS: {sus.length.toLocaleString()} registros | QualiAR tratado:{" "}
        {rio.length.toLocaleString()} registros
      </p>
      <Plot
        data={[
          {
            x: rio.map((r) => r.ano_mes),
            y: rio.map((r) => parseFloat(r["pm2_5"] || "NaN")),
            type: "bar",
            name: "PM2.5",
          },
        ]}
        layout={{
          title: { text: "PM2.5 mensal — dados tratados" },
          xaxis: { title: { text: "Ano-Mês" } },
          yaxis: { title: { text: "PM2.5" } },
        }}
        style={{ width: "100%", height: 500 }}
      />
    </div>
  );
}
