import { useMemo } from "react";
import { calculateRollingAverage, pearsonCorrelation } from "../utils/math";
import { groupBy } from "../utils/data";

export function useTimeSeriesStats(
  data: any[],
  dateKey: string,
  valueKey: string,
  windowSize: number = 30
) {
  return useMemo(() => {
    if (!data.length || !data.some(d => d[valueKey])) return null;
    
    const sortedData = [...data]
      .filter(d => d[dateKey] && d[valueKey] !== undefined)
      .sort((a, b) => new Date(a[dateKey]).getTime() - new Date(b[dateKey]).getTime());
    
    const dates = sortedData.map(d => d[dateKey]);
    const values = sortedData.map(d => d[valueKey] || 0);
    const rollingAvg = calculateRollingAverage(values, windowSize);
    
    return { dates, values, rollingAvg };
  }, [data, dateKey, valueKey, windowSize]);
}

export function useCorrelationMatrix(
  data: any[],
  variables: string[]
) {
  return useMemo(() => {
    if (!data.length || variables.length < 2) return null;
    
    const matrix: number[][] = [];
    
    variables.forEach((var1, i) => {
      const row: number[] = [];
      variables.forEach((var2, j) => {
        if (i === j) {
          row.push(1);
          return;
        }
        
        const values1 = data.map(d => d[var1] || 0).filter(v => !isNaN(v));
        const values2 = data.map(d => d[var2] || 0).filter(v => !isNaN(v));
        
        if (values1.length === 0 || values2.length === 0) {
          row.push(0);
          return;
        }
        
        const correlation = pearsonCorrelation(values1, values2);
        row.push(isNaN(correlation) ? 0 : correlation);
      });
      matrix.push(row);
    });
    
    return { vars: variables, matrix };
  }, [data, variables]);
}

export function useGroupStats<T>(
  data: T[],
  groupKey: keyof T,
  valueKey: keyof T
) {
  return useMemo(() => {
    if (!data.length) return null;
    
    const groups = groupBy(data, (item) => String(item[groupKey]));
    const stats: Array<{ group: string; values: number[]; mean: number; median: number; count: number }> = [];
    
    groups.forEach((items, group) => {
      const values = items
        .map(item => Number(item[valueKey]))
        .filter(v => !isNaN(v));
      
      if (values.length > 0) {
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const median = values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
        stats.push({
          group,
          values,
          mean,
          median,
          count: values.length
        });
      }
    });
    
    return stats.sort((a, b) => b.mean - a.mean);
  }, [data, groupKey, valueKey]);
}