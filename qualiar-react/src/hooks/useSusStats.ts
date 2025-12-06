import type { SUSData } from "../types/data"; // caminho conforme sua estrutura
 // caminho conforme sua estrutura

export interface SusMetrics {
  total_internacoes: number;
  media_idade: number;
  taxa_mortalidade: number;
  media_permanencia: number;
  ano_min: number;
  ano_max: number;
}

export function useSusMetrics(data: SUSData[]): SusMetrics {
  const total = data.length;

  return {
    total_internacoes: total,

    media_idade: Number(
      (data.reduce((acc, item) => {
        const idade = typeof item.IDADE === "string"
          ? parseInt(item.IDADE)
          : item.IDADE;
        return acc + (idade || 0);
      }, 0) / (total || 1)).toFixed(1)
    ),

    taxa_mortalidade:
      Number(
        (
          data.filter(d => d.MORTE === 1).length /
          (total || 1)
        ).toFixed(4)
      ) * 100,

    media_permanencia:
      Number(
        (
          data.reduce((acc, item) => acc + (item.DIAS_PERM || 0), 0) /
          (total || 1)
        ).toFixed(1)
      ),

    ano_min: Math.min(
      ...data.map(d => d.ANO ?? Infinity)
    ),

    ano_max: Math.max(
      ...data.map(d => d.ANO ?? -Infinity)
    ),
  };
}
