import Papa from "papaparse";

// Cache para os dados
let susDataCache: any[] | null = null;

export async function loadOptimizedSUSData(): Promise<any[]> {
  // Retorna dados do cache se já estiverem carregados
  if (susDataCache) {
    return susDataCache;
  }

  const urls = [
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte1.csv",
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte2.csv",
    "https://media.githubusercontent.com/media/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTERNACOES_STREAMLIT_parte3.csv",
  ];

  try {
    console.log('Iniciando carregamento dos dados SUS...');
    
    // Carrega apenas uma parte inicial para teste
    const firstPart = await fetchCSV(urls[0]);
    susDataCache = firstPart.slice(0, 12000); // Limita a 5000 registros para teste
    
    console.log('Dados carregados:', susDataCache.length, 'registros');
    return susDataCache;
    
  } catch (error) {
    console.error('Erro ao carregar dados SUS:', error);
    throw error;
  }
}

// Versão que carrega dados resumidos (apenas contagens)
export async function loadSUSSummary(): Promise<{
  totalRecords: number;
  dateRange: { min: Date; max: Date };
  metrics: any;
}> {
  // Implementação simplificada para obter apenas métricas básicas
  // Isso pode ser otimizado ainda mais com endpoints de API específicos
  return {
    totalRecords: 0,
    dateRange: { min: new Date(), max: new Date() },
    metrics: {}
  };
}

async function fetchCSV(url: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: false,
      skipEmptyLines: true,
      complete: (res) => {
        console.log(`CSV carregado: ${res.data.length} registros`);
        resolve(res.data as any[]);
      },
      error: (err) => {
        console.error('Erro no Papa.parse:', err);
        reject(err);
      },
    });
  });
}