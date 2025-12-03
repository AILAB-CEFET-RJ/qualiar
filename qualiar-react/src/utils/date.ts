export function parseDate(d: any): Date | null {
  if (!d) return null;
  const dt = new Date(d);
  return isNaN(dt.getTime()) ? null : dt;
}

export function parseDateFlexible(raw: any): Date | null {
  if (raw instanceof Date) return isNaN(raw as any) ? null : raw;
  if (typeof raw !== "string") return null;
  
  // Tenta ISO
  const iso = new Date(raw);
  if (!isNaN(iso.getTime())) return iso;
  
  // Tenta DD/MM/YYYY
  const m = raw.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/);
  if (m) {
    const [, d, mo, y] = m;
    const year = y.length === 2 ? Number("20" + y) : Number(y);
    const dt = new Date(year, Number(mo) - 1, Number(d));
    return isNaN(dt.getTime()) ? null : dt;
  }
  
  return null;
}