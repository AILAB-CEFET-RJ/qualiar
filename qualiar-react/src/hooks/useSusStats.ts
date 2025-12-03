import { useMemo } from "react";
import type { SUSData } from "../types/data";
import { calculateRollingAverage } from "../utils/math";

export interface SusMetrics {
  totalInternacoes: number;
  mediaIdade: number;
  taxaMortalidade: number;
  mediaPermanencia: number;
}

export function useSusMetrics(data: SUSData[]): SusMetrics | null {
  return useMemo(() => {
    if (!data.length) return null;
    
    const totalInternacoes = data.length;
    
    const idadeValues = data
      .map(item => item.IDADE)
      .filter((age): age is number => typeof age === 'number' && !isNaN(age));
    const mediaIdade = idadeValues.length > 0 
      ? idadeValues.reduce((sum, age) => sum + age, 0) / idadeValues.length 
      : NaN;
    
    const morteValues = data
      .map(item => item.MORTE)
      .filter((morte): morte is number => typeof morte === 'number' && !isNaN(morte));
    const taxaMortalidade = morteValues.length > 0 
      ? morteValues.reduce((sum, morte) => sum + morte, 0) / morteValues.length 
      : NaN;
    
    const permanenciaValues = data
      .map(item => item.DIAS_PERM)
      .filter((perm): perm is number => typeof perm === 'number' && !isNaN(perm));
    const mediaPermanencia = permanenciaValues.length > 0 
      ? permanenciaValues.reduce((sum, perm) => sum + perm, 0) / permanenciaValues.length 
      : NaN;
    
    return { totalInternacoes, mediaIdade, taxaMortalidade, mediaPermanencia };
  }, [data]);
}

export function useSusTimeSeries(data: SUSData[]) {
  return useMemo(() => {
    if (!data.length) return null;
    
    const dailyCounts: { [key: string]: number } = {};
    data.forEach(item => {
      if (item.DT_INTER) {
        const date = (item.DT_INTER as Date).toISOString().split('T')[0];
        dailyCounts[date] = (dailyCounts[date] || 0) + 1;
      }
    });
    
    const dates = Object.keys(dailyCounts).sort();
    const counts = dates.map(date => dailyCounts[date]);
    const ma7 = calculateRollingAverage(counts, 7);
    const ma30 = calculateRollingAverage(counts, 30);
    
    return { 
      dates: dates.map(d => new Date(d)), 
      counts, 
      ma7, 
      ma30 
    };
  }, [data]);
}

export function useSusSexDistribution(data: SUSData[]) {
  return useMemo(() => {
    if (!data.length) return null;
    
    const sexoCol = data[0].SEXO_TXT ? 'SEXO_TXT' : 'SEXO';
    const sexCounts: { [key: string]: number } = {};
    
    data.forEach(item => {
      const sex = item[sexoCol]?.toString() || 'Não informado';
      sexCounts[sex] = (sexCounts[sex] || 0) + 1;
    });
    
    return sexCounts;
  }, [data]);
}

export function useSusHeatmapData(data: SUSData[]) {
  return useMemo(() => {
    if (!data.length) return null;
    
    const countsByYearMonth: { [key: string]: number } = {};
    data.forEach(item => {
      if (item.ANO && item.MES) {
        const key = `${item.ANO}-${item.MES}`;
        countsByYearMonth[key] = (countsByYearMonth[key] || 0) + 1;
      }
    });
    
    const years = Array.from(new Set(data.map(d => d.ANO).filter(Boolean))).sort() as number[];
    const heatmapData: number[][] = [];
    
    years.forEach(year => {
      const row: number[] = [];
      [1,2,3,4,5,6,7,8,9,10,11,12].forEach(month => {
        const key = `${year}-${month}`;
        row.push(countsByYearMonth[key] || 0);
      });
      heatmapData.push(row);
    });
    
    return {
      years: years.map(y => y.toString()),
      data: heatmapData
    };
  }, [data]);
}