export function calculateRollingAverage(data: number[], window: number = 30): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - window + 1);
    const values = data.slice(start, i + 1);
    result.push(values.reduce((a, b) => a + b, 0) / values.length);
  }
  return result;
}

// Nova função: rollingMean que aceita valores nulos
export function rollingMean(values: (number | null)[], window: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  let sum = 0;
  let count = 0;
  const q: number[] = []; // guarda valores válidos
  
  for (let i = 0; i < values.length; i++) {
    const val = values[i];
    if (val !== null && !isNaN(val)) {
      q.push(val);
      sum += val;
      count += 1;
    } else {
      q.push(NaN);
    }
    
    if (q.length > window) {
      const removed = q.shift()!;
      if (!isNaN(removed)) {
        sum -= removed;
        count -= 1;
      }
    }
    
    out[i] = count > 0 ? sum / count : null;
  }
  return out;
}

export function normalizeData(data: number[]): number[] {
  const min = Math.min(...data);
  const max = Math.max(...data);
  if (max === min) return data.map(() => 0.5);
  return data.map(val => (val - min) / (max - min));
}

// Nova função: minMaxNormalize que aceita valores nulos
export function minMaxNormalize(values: (number | null)[]): (number | null)[] {
  const finite = values.filter((v) => v !== null && !isNaN(v!)) as number[];
  
  if (finite.length === 0) {
    return values.map(() => null);
  }
  
  const lo = Math.min(...finite);
  const hi = Math.max(...finite);
  
  if (hi === lo) {
    return values.map((v) => 
      v !== null && !isNaN(v!) ? 0.5 : v
    );
  }
  
  return values.map((v) =>
    v !== null && !isNaN(v!) ? (v - lo) / (hi - lo) : v
  );
}

export function pearsonCorrelation(x: number[], y: number[]): number {
  const n = x.length;
  if (n !== y.length || n < 2) return 0;
  
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
  const sumX2 = x.reduce((sum, val) => sum + val * val, 0);
  const sumY2 = y.reduce((sum, val) => sum + val * val, 0);
  
  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
  
  return denominator === 0 ? 0 : numerator / denominator;
}

export function spearmanCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length || x.length < 2) return 0;
  
  const rankX = x.map((val, idx) => ({ val, idx }))
    .sort((a, b) => a.val - b.val)
    .map((item, rank) => ({ idx: item.idx, rank: rank + 1 }));
  
  const rankY = y.map((val, idx) => ({ val, idx }))
    .sort((a, b) => a.val - b.val)
    .map((item, rank) => ({ idx: item.idx, rank: rank + 1 }));
  
  const sortedRankX = rankX.sort((a, b) => a.idx - b.idx).map(r => r.rank);
  const sortedRankY = rankY.sort((a, b) => a.idx - b.idx).map(r => r.rank);
  
  return pearsonCorrelation(sortedRankX, sortedRankY);
}

export function percentile(values: number[], p: number): number {
  const v = values.filter((x) => !isNaN(x)).sort((a, b) => a - b);
  if (v.length === 0) return NaN;
  const idx = (p / 100) * (v.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return v[lo];
  return v[lo] + (v[hi] - v[lo]) * (idx - lo);
}

export function median(values: number[]): number {
  return percentile(values, 50);
}

// Nova função: calcula matriz de correlação
export function correlationMatrix(data: any[], columns: string[]): number[][] {
  const Z = columns.map((c) => data.map((r) => {
    const val = r[c];
    return val !== null && val !== undefined && !isNaN(val) ? Number(val) : NaN;
  }));
  
  const n = columns.length;
  const matrix: number[][] = Array.from({ length: n }, () => new Array(n).fill(NaN));
  
  for (let i = 0; i < n; i++) {
    for (let j = i; j < n; j++) {
      // Filtra pares onde ambos valores são válidos
      const pairedValues = Z[i].map((val, idx) => ({ x: val, y: Z[j][idx] }))
        .filter(pair => !isNaN(pair.x) && !isNaN(pair.y));
      
      const xVals = pairedValues.map(p => p.x);
      const yVals = pairedValues.map(p => p.y);
      
      if (xVals.length >= 2) {
        const r = pearsonCorrelation(xVals, yVals);
        matrix[i][j] = isNaN(r) ? 0 : r;
        matrix[j][i] = matrix[i][j];
      } else {
        matrix[i][j] = 0;
        matrix[j][i] = 0;
      }
    }
  }
  
  return matrix;
}