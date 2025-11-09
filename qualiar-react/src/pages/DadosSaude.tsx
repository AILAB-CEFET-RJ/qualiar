import { useEffect, useState, type JSX } from "react";
import { loadSUSData, describeSchema } from "../services/dataLoader";

export default function DadosSaude(): JSX.Element {
  const [rows, setRows] = useState<any[]>([]);
  const [schema, setSchema] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSUSData()
      .then((data) => {
        setRows(data);
        setSchema(describeSchema(data));
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Carregando dados do SUS...</div>;

  return (
    <div>
      <h1>Dados de Saúde (SUS)</h1>
      <p>Total de registros: {rows.length.toLocaleString()}</p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#f3f4f6" }}>
            <th>Coluna</th>
            <th>% Nulos</th>
            <th>Exemplos</th>
          </tr>
        </thead>
        <tbody>
          {schema.slice(0, 30).map((r) => (
            <tr key={r.coluna}>
              <td>{r.coluna}</td>
              <td>{r["%_nulos"]}%</td>
              <td>{r.exemplos}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
