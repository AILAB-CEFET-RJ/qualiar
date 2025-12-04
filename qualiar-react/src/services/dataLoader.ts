import Papa from "papaparse";

// Utilitários reutilizados
function parseDateFlexible(raw: any): Date | null {
  if (raw instanceof Date) return isNaN(raw as any) ? null : raw;
  if (typeof raw !== "string") return null;
  const iso = new Date(raw);
  if (!isNaN(iso.getTime())) return iso;
  const m = raw.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/);
  if (m) {
    const [, d, mo, y] = m;
    const year = y.length === 2 ? Number("20" + y) : Number(y);
    const dt = new Date(year, Number(mo) - 1, Number(d));
    return isNaN(dt.getTime()) ? null : dt;
  }
  return null;
}

// ----------------------------------------------------
// 1. loadRioDeJaneiroQualiarData
// ----------------------------------------------------
export async function loadRioDeJaneiroQualiarData(): Promise<any[]> {
  const url =
    "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO.csv";
  const data = await fetchCSV(url);
  const parsed = data.map((r: any) => {
    const d = parseDateFlexible(r["data_dia"]);
    const ano = d?.getFullYear() ?? null;
    const mes = d ? d.getMonth() + 1 : null;
    const ano_mes = d ? `${ano}-${String(mes).padStart(2, "0")}` : null;
    return { ...r, data_dia: d ?? null, ano, mes, ano_mes };
  });
  return parsed;
}

// ----------------------------------------------------
// 2. loadRioDeJaneiroQualiarTreatedData
// ----------------------------------------------------
export async function loadRioDeJaneiroQualiarTreatedData(): Promise<any[]> {
  const url =
    "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv";
  const data = await fetchCSV(url);
  const parsed = data.map((r: any) => {
    const d = parseDateFlexible(r["data_dia"]);
    const ano = d?.getFullYear() ?? null;
    const mes = d ? d.getMonth() + 1 : null;
    const ano_mes = d ? `${ano}-${String(mes).padStart(2, "0")}` : null;
    return { ...r, data_dia: d ?? null, ano, mes, ano_mes };
  });
  return parsed;
}

// ----------------------------------------------------
// 3. loadSUSData
// ----------------------------------------------------
export async function loadSUSData(): Promise<any[]> {
  const urls = [
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte1.csv",
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte2.csv",
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte3.csv",
  ];

  const parts = await Promise.all(urls.map(fetchCSV));
  return parts.flat();
}

// ----------------------------------------------------
// 4. describeSchema (equivalente a describe_schema do Python)
// ----------------------------------------------------
export function describeSchema(rows: any[]): any[] {
  if (!rows.length) return [];
  const cols = Object.keys(rows[0]);
  const n = rows.length;
  return cols.map((c) => {
    const vals = rows.map((r) => r[c]);
    const nulls = vals.filter((v) => v === null || v === undefined || v === "").length;
    const pctNull = n ? (100 * nulls) / n : 0;
    const sample = vals
      .filter((v) => v !== null && v !== undefined && v !== "")
      .slice(0, 3)
      .map(String)
      .join(" | ");
    return { coluna: c, "%_nulos": Number(pctNull.toFixed(2)), exemplos: sample };
  });
}

// ----------------------------------------------------
// Util: leitura genérica de CSV (Promise)
// ----------------------------------------------------
async function fetchCSV(url: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: false,
      skipEmptyLines: true,
      complete: (res) => resolve(res.data as any[]),
      error: (err) => reject(err),
    });
  });
}
