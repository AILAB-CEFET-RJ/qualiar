# Resumo dos resultados - Zona Sul

Este arquivo resume, de forma breve, os resultados de `copacabana.ipynb` e `um_copacabana.ipynb`.

- Estrategia comum: interpolacao temporal conservadora em lacunas curtas (ate 4 horas).
- Resultado agregado: `3886` valores imputados no total.

## Resultados por notebook

- `copacabana.ipynb`: `3539` imputacoes, com maior ganho em `so2` (`7,02%` -> `3,75%`) e melhora adicional em `co`, `o3` e `pm10`.
- `um_copacabana.ipynb`: `347` imputacoes, com destaque para `co` (`6,39%` -> `1,51%`) e reducoes em `pm2_5`, `o3`, `temp` e `ur`; `so2` melhorou, mas permaneceu com missing alto (`32,56%`).

## Conclusao breve

O tratamento aumentou a completude sem alterar de forma relevante as estatisticas centrais das series com dados observados. Ainda assim, persistem ausencias estruturais (100% missing) para parte dos poluentes, o que limita analises dessas variaveis.
