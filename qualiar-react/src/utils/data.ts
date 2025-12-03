import type { RioData } from "../types/data";

export function mergeRawIntoTreated(raw: RioData[], treated: RioData[]): RioData[] {
  const mapRaw = new Map<string, RioData>();
  raw.forEach((r) => {
    const key = r.data_dia.toISOString().slice(0, 10);
    mapRaw.set(key, r);
  });

  return treated.map((t) => {
    const key = t.data_dia.toISOString().slice(0, 10);
    const base = { ...t };
    const r = mapRaw.get(key);

    if (r) {
      for (const col in r) {
        if (col === "data_dia") continue;
        if (base[col] === undefined) {
          base[col] = r[col];
        } else if (base[col] !== r[col]) {
          base[col + "_raw"] = r[col];
        }
      }
    }

    return base;
  });
}

export function groupBy<T, K extends string | number>(arr: T[], keyFn: (t: T) => K): Map<K, T[]> {
  const m = new Map<K, T[]>();
  for (const item of arr) {
    const k = keyFn(item);
    const g = m.get(k);
    if (g) g.push(item);
    else m.set(k, [item]);
  }
  return m;
}

export function uniq<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}

// Função que estava faltando
export function toNumberOrNaN(v: any): number {
  if (v === null || v === undefined || v === "") return NaN;
  const n = typeof v === "number" ? v : Number(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : NaN;
}