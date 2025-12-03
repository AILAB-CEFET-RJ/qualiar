import { AQI_BINS, POL_BINS } from "./constants";

export function classificaAQI(aqiVal: number | undefined): string | null {
  if (aqiVal === undefined || isNaN(aqiVal)) return null;
  const value = Math.round(aqiVal);
  for (const bin of AQI_BINS) {
    if (value >= bin.min && value <= bin.max) {
      return bin.label;
    }
  }
  return "Fora da escala";
}

export function classificaPoluente(val: number | undefined, polCol: string): string | null {
  if (val === undefined || isNaN(val)) return null;
  const pol = polCol.toLowerCase();
  const bins = POL_BINS[pol];
  if (!bins) return null;
  
  const value = Math.round(val);
  for (const bin of bins) {
    if (value >= bin.min && value <= bin.max) {
      return bin.label;
    }
  }
  return "Fora da escala";
}