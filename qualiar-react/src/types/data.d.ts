export interface RioData {
  data_dia: Date;
  ano: number;
  mes: number;
  dia?: number;
  temp?: number;
  ur?: number;
  chuva?: number;
  co?: number;
  no?: number;
  no2?: number;
  nox?: number;
  so2?: number;
  o3?: number;
  pm10?: number;
  pm2_5?: number;
  AQI?: number;
  Qualidade_do_Ar?: number;
  [key: string]: any;
}

export interface SUSData {
  DT_INTER?: string | Date;
  IDADE?: string | number;
  SEXO?: string;
  SEXO_TXT?: string;
  DIAG_PRINC?: string;
  DIAS_PERM?: number;
  MORTE?: number;
  ANO?: number;
  MES?: number;
  CID_GRUPO_J?: string;
  MUNIC_RES?: string;
  FAIXA_ETARIA?: string;
  CID_CAT3?: string;
  [key: string]: any;
}

export interface FilterState {
  d_ini: Date | null;
  d_fim: Date | null;
  idade_min: number | null;
  idade_max: number | null;
  cids: string[];
  munics: string[];
}

export interface CorrelationResult {
  target: string;
  variavel: string;
  janela: number;
  shift: number;
  spearman: number;
}