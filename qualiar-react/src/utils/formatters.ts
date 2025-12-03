export function kpiInt(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "-";
  return Math.round(n).toLocaleString('pt-BR');
}

export function formatNumber(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "-";
  return n.toFixed(1);
}

export function formatPercent(n: number | undefined): string {
  if (n === undefined || isNaN(n)) return "-";
  return (n * 100).toFixed(2) + "%";
}

export function toNumberOrNaN(v: any): number {
  if (v === null || v === undefined || v === "") return NaN;
  const n = typeof v === "number" ? v : Number(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : NaN;
}