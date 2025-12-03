import { useState, useEffect } from "react";
import Papa from "papaparse";
import type { RioData, SUSData } from "../types/data";
import { parseDate, parseDateFlexible } from "../utils/date";
import { toNumberOrNaN } from "../utils/formatters";

// Cache para evitar múltiplos downloads
const csvCache = new Map<string, any[]>();

export function useCsvData<T>(
  url: string, 
  parser: (row: any) => T,
  cacheKey: string
): { data: T[]; loading: boolean; error: string | null } {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Verificar cache primeiro
    if (csvCache.has(cacheKey)) {
      setData(csvCache.get(cacheKey) as T[]);
      setLoading(false);
      return;
    }

    setLoading(true);
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (res) => {
        try {
          const parsedData = (res.data as any[]).map(parser);
          csvCache.set(cacheKey, parsedData);
          setData(parsedData);
          setError(null);
        } catch (err) {
          setError(`Erro ao processar dados: ${err}`);
        } finally {
          setLoading(false);
        }
      },
      error: (err) => {
        setError(`Erro ao carregar CSV: ${err.message}`);
        setLoading(false);
      },
    });
  }, [url, parser, cacheKey]);

  return { data, loading, error };
}

// Parsers específicos para reutilização
export const rioDataParser = (r: any): RioData => ({
  ...r,
  data_dia: parseDate(r.data_dia) || new Date(),
  ano: r.ano || (parseDate(r.data_dia)?.getFullYear() || new Date().getFullYear()),
  mes: r.mes || ((parseDate(r.data_dia)?.getMonth() || 0) + 1),
  temp: toNumberOrNaN(r.temp),
  ur: toNumberOrNaN(r.ur),
  chuva: toNumberOrNaN(r.chuva),
  co: toNumberOrNaN(r.co),
  no: toNumberOrNaN(r.no),
  no2: toNumberOrNaN(r.no2),
  nox: toNumberOrNaN(r.nox),
  so2: toNumberOrNaN(r.so2),
  o3: toNumberOrNaN(r.o3),
  pm10: toNumberOrNaN(r.pm10),
  pm2_5: toNumberOrNaN(r.pm2_5),
  AQI: toNumberOrNaN(r.AQI),
});

export const susDataParser = (r: any): SUSData => ({
  ...r,
  DT_INTER: parseDateFlexible(r.DT_INTER),
  IDADE: toNumberOrNaN(r.IDADE),
  DIAS_PERM: toNumberOrNaN(r.DIAS_PERM),
  MORTE: toNumberOrNaN(r.MORTE),
});