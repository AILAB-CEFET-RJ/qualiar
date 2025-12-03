import { useState, useCallback, useMemo } from "react";
// import type { RioData, SUSData } from "../types/data";

export function useDateFilter<T extends { data_dia?: Date | null }>(
  initialDateRange: [Date | null, Date | null] = [null, null]
) {
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>(initialDateRange);

  const filterByDate = useCallback((data: T[]): T[] => {
    const [startDate, endDate] = dateRange;
    if (!startDate || !endDate) return data;
    
    return data.filter(item => {
      const itemDate = item.data_dia;
      if (!itemDate) return false;
      return itemDate >= startDate && itemDate <= endDate;
    });
  }, [dateRange]);

  return { dateRange, setDateRange, filterByDate };
}

export function useMultiSelectFilter<T>(
  data: T[],
  keyExtractor: (item: T) => string,
  initialSelected: string[] = []
) {
  const [selectedValues, setSelectedValues] = useState<string[]>(initialSelected);

  const filter = useCallback((items: T[]): T[] => {
    if (selectedValues.length === 0) return items;
    return items.filter(item => selectedValues.includes(keyExtractor(item)));
  }, [selectedValues, keyExtractor]);

  const availableOptions = useMemo(() => {
    const values = new Set(data.map(keyExtractor).filter(Boolean));
    return Array.from(values).sort();
  }, [data, keyExtractor]);

  return {
    selectedValues,
    setSelectedValues,
    filter,
    availableOptions,
  };
}