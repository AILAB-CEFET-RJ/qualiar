export const MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
export const MONTH_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

export const AQI_BINS = [
  { min: 0, max: 40, label: "N1 - Boa" },
  { min: 41, max: 80, label: "N2 - Moderada" },
  { min: 81, max: 120, label: "N3 - Ruim" },
  { min: 121, max: 200, label: "N4 - Muito Ruim" },
  { min: 201, max: 400, label: "N5 - Péssima" },
];

export const POL_BINS: { [key: string]: Array<{ min: number; max: number; label: string }> } = {
  pm10: [
    { min: 0, max: 50, label: "N1 - Boa" },
    { min: 50, max: 100, label: "N2 - Moderada" },
    { min: 100, max: 150, label: "N3 - Ruim" },
    { min: 150, max: 250, label: "N4 - Muito Ruim" },
    { min: 250, max: 600, label: "N5 - Péssima" },
  ],
  pm2_5: [
    { min: 0, max: 25, label: "N1 - Boa" },
    { min: 25, max: 50, label: "N2 - Moderada" },
    { min: 50, max: 75, label: "N3 - Ruim" },
    { min: 75, max: 125, label: "N4 - Muito Ruim" },
    { min: 125, max: 300, label: "N5 - Péssima" },
  ],
  o3: [
    { min: 0, max: 100, label: "N1 - Boa" },
    { min: 100, max: 130, label: "N2 - Moderada" },
    { min: 130, max: 160, label: "N3 - Ruim" },
    { min: 160, max: 200, label: "N4 - Muito Ruim" },
    { min: 200, max: 800, label: "N5 - Péssima" },
  ],
  co: [
    { min: 0, max: 9, label: "N1 - Boa" },
    { min: 9, max: 11, label: "N2 - Moderada" },
    { min: 11, max: 13, label: "N3 - Ruim" },
    { min: 13, max: 15, label: "N4 - Muito Ruim" },
    { min: 15, max: 50, label: "N5 - Péssima" },
  ],
  no2: [
    { min: 0, max: 200, label: "N1 - Boa" },
    { min: 200, max: 240, label: "N2 - Moderada" },
    { min: 240, max: 320, label: "N3 - Ruim" },
    { min: 320, max: 1130, label: "N4 - Muito Ruim" },
    { min: 1130, max: 3750, label: "N5 - Péssima" },
  ],
  so2: [
    { min: 0, max: 20, label: "N1 - Boa" },
    { min: 20, max: 40, label: "N2 - Moderada" },
    { min: 40, max: 365, label: "N3 - Ruim" },
    { min: 365, max: 800, label: "N4 - Muito Ruim" },
    { min: 800, max: 2620, label: "N5 - Péssima" },
  ],
};

export const DATA_URLS = {
  RIO_RAW: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO.csv",
  RIO_TREATED: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv",
  ESTACOES: "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/Estacoes_Tratadas_Por_Dia/ESTACOES_UNIFICADAS_POR_DIA.csv",
};

export const NUMERIC_COLS = [
  "temp", "ur", "chuva", "co", "no", "no2", "nox", "so2", "o3", "pm10", "pm2_5", "AQI"
];