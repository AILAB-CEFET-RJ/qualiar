import { useMemo } from "react";

export interface ExtremeDay {
  date: string;
  value: number;
}

export function useExtremeData<T>(
  data: T[],
  dateKey: keyof T,
  valueKey: keyof T,
  count: number = 10
): ExtremeDay[] | null {
  return useMemo(() => {
    if (!data.length) return null;
    
    return [...data]
      .filter(d => {
        const val = d[valueKey];
        return val !== undefined && !isNaN(Number(val));
      })
      .sort((a, b) => {
        const valA = Number(a[valueKey]);
        const valB = Number(b[valueKey]);
        return valB - valA; // Ordena do maior para o menor
      })
      .slice(0, count)
      .map(d => ({
        date: (d[dateKey] as Date).toISOString().slice(0, 10),
        value: Number(d[valueKey])
      }));
  }, [data, dateKey, valueKey, count]);
}