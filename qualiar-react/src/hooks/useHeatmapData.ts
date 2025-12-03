import { useMemo } from "react";
import { MONTH_LABELS, MONTH_ORDER } from "../utils/constants";

export interface HeatmapData {
  years: string[];
  data: number[][];
}

export function useHeatmapData<T>(
  data: T[],
  yearKey: keyof T,
  monthKey: keyof T,
  variableKey: keyof T,
  aggregation: "mean" | "sum" | "max" = "mean"
): HeatmapData | null {
  return useMemo(() => {
    if (!data.length) return null;
    
    const years = Array.from(new Set(data.map(d => d[yearKey]))).sort() as string[];
    const heatmapData: number[][] = [];
    
    years.forEach(year => {
      const row: number[] = [];
      MONTH_ORDER.forEach(month => {
        const monthData = data.filter(d => 
          d[yearKey] === year && d[monthKey] === month
        );
        
        if (monthData.length === 0) {
          row.push(NaN);
          return;
        }
        
        let value: number;
        const values = monthData.map(d => Number(d[variableKey]) || 0);
        
        switch (aggregation) {
          case "sum":
            value = values.reduce((sum, val) => sum + val, 0);
            break;
          case "max":
            value = Math.max(...values);
            break;
          case "mean":
          default:
            value = values.reduce((sum, val) => sum + val, 0) / monthData.length;
        }
        
        row.push(value);
      });
      heatmapData.push(row);
    });
    
    return {
      years,
      data: heatmapData
    };
  }, [data, yearKey, monthKey, variableKey, aggregation]);
}