import { useMemo } from "react";

export interface CompletenessItem {
  variable: string;
  percentage: number;
}

export function useCompleteness(
  data: any[],
  numericColumns: string[]
): CompletenessItem[] | null {
  return useMemo(() => {
    if (!data.length) return null;
    
    const availableCols = numericColumns.filter(col => 
      data.some(d => d[col] !== undefined)
    );
    
    return availableCols.map(col => {
      const nonNullCount = data.filter(d => 
        d[col] !== undefined && !isNaN(d[col])
      ).length;
      const percentage = (nonNullCount / data.length) * 100;
      return {
        variable: col,
        percentage: Math.round(percentage * 10) / 10
      };
    }).sort((a, b) => b.percentage - a.percentage);
  }, [data, numericColumns]);
}