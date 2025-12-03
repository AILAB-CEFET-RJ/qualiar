import { useMemo } from "react";
import { calculateRollingAverage, normalizeData } from "../utils/math";

export interface MultiVarSeries {
  name: string;
  dates: Date[];
  values: number[];
  normalized: number[];
}

export function useMultiVarSeries<T>(
  data: T[],
  dateKey: keyof T,
  variables: string[],
  windowSize: number = 30
): MultiVarSeries[] | null {
  return useMemo(() => {
    if (!data.length || !variables.length) return null;
    
    const sortedData = [...data].sort((a, b) => {
      const dateA = a[dateKey] as Date;
      const dateB = b[dateKey] as Date;
      return dateA.getTime() - dateB.getTime();
    });
    
    const dates = sortedData.map(d => d[dateKey] as Date);
    
    return variables.map(varName => {
      const values = sortedData.map(d => d[varName as keyof T] as number || 0);
      const rollingAvg = calculateRollingAverage(values, windowSize);
      const normalized = normalizeData(rollingAvg);
      
      return {
        name: varName,
        dates,
        values,
        normalized
      };
    });
  }, [data, dateKey, variables, windowSize]);
}