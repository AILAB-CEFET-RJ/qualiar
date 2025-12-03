import { useState, useEffect } from "react";
import { loadOptimizedSUSData } from "../services/optimizedDataLoader";
import type { SUSData } from "../types/data";
import { parseDateFlexible } from "../utils/date";
import { toNumberOrNaN } from "../utils/formatters";

export function useSusData() {
  const [data, setData] = useState<SUSData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const susData = await loadOptimizedSUSData();
        
        const processedData = susData.map(item => ({
          ...item,
          DT_INTER: item.DT_INTER ? parseDateFlexible(item.DT_INTER) : null,
          IDADE: toNumberOrNaN(item.IDADE),
          DIAS_PERM: toNumberOrNaN(item.DIAS_PERM),
          MORTE: toNumberOrNaN(item.MORTE),
          ANO: toNumberOrNaN(item.ANO),
          MES: toNumberOrNaN(item.MES),
        }));

        setData(processedData);
        setError(null);
      } catch (err) {
        console.error('Erro ao carregar dados SUS:', err);
        setError("Erro ao carregar dados. Tente recarregar a página.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return { data, loading, error };
}

export function useSusFilterOptions(data: SUSData[]) {
  return {
    sexo: Array.from(new Set(data.map(d => d.SEXO_TXT || d.SEXO).filter(Boolean))).map(String),
    faixaEtaria: Array.from(new Set(data.map(d => d.FAIXA_ETARIA).filter(Boolean))).map(String),
    grupos: Array.from(new Set(data.map(d => d.CID_GRUPO_J).filter(Boolean))).map(String),
    anos: Array.from(new Set(data.map(d => d.ANO).filter(Boolean))).sort((a, b) => Number(b) - Number(a)).map(String),
  };
}

export function useFilteredSusData(
  data: SUSData[],
  filters: {
    dateRange: [Date | null, Date | null];
    selectedSex: string[];
    selectedAgeGroups: string[];
    selectedDiagnosisGroups: string[];
    selectedYears: string[];
  }
) {
  return data.filter(item => {
    // Filtro por data
    if (filters.dateRange[0] && filters.dateRange[1] && item.DT_INTER) {
      const itemDate = item.DT_INTER as Date;
      if (itemDate < filters.dateRange[0] || itemDate > filters.dateRange[1]) return false;
    }

    // Filtro por sexo
    if (filters.selectedSex.length > 0) {
      const sexoCol = item.SEXO_TXT ? 'SEXO_TXT' : 'SEXO';
      const sex = item[sexoCol]?.toString() || '';
      if (!filters.selectedSex.includes(sex)) return false;
    }

    // Filtro por faixa etária
    if (filters.selectedAgeGroups.length > 0) {
      const faixa = item.FAIXA_ETARIA?.toString() || '';
      if (!filters.selectedAgeGroups.includes(faixa)) return false;
    }

    // Filtro por grupo de diagnóstico
    if (filters.selectedDiagnosisGroups.length > 0) {
      const grupo = item.CID_GRUPO_J?.toString() || '';
      if (!filters.selectedDiagnosisGroups.includes(grupo)) return false;
    }

    // Filtro por ano
    if (filters.selectedYears.length > 0) {
      const ano = item.ANO?.toString() || '';
      if (!filters.selectedYears.includes(ano)) return false;
    }

    return true;
  });
}