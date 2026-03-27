# Resumo dos resultados - Centro

Este resumo consolida, de forma breve, os resultados dos notebooks `centro.ipynb`, `um_caju.ipynb`, `um_centro.ipynb` e `um_gamboa.ipynb`.

- Estrategia aplicada: interpolacao temporal conservadora em lacunas curtas (ate 4 horas).
- Resultado agregado: `3646` valores imputados no total.

## Resultados por notebook

- `centro.ipynb`: `1306` imputacoes, com melhora principal em `o3` (`7,61%` -> `6,96%`), `co` (`7,06%` -> `6,51%`) e `pm10` (`6,02%` -> `5,48%`).
- `um_caju.ipynb`: `1407` imputacoes (maior ganho), com reducoes fortes em `so2` (`8,72%` -> `3,94%`), `co` (`9,83%` -> `6,84%`) e `o3` (`2,63%` -> `1,22%`).
- `um_centro.ipynb`: `370` imputacoes, com destaque para `so2` (`11,92%` -> `6,18%`), `co` (`25,15%` -> `20,04%`) e `o3` (`5,93%` -> `3,70%`).
- `um_gamboa.ipynb`: `563` imputacoes, com melhora moderada em `so2`, `co`, `o3` e `pm2_5`; maior ganho relativo em `temp` e `ur` (`1,69%` -> `0,85%`).

## Conclusao breve

O tratamento aumentou a completude sem alterar de forma relevante as estatisticas centrais das series. Ainda assim, permanecem ausencias estruturais (100% missing) em parte dos poluentes, o que limita analises para essas variaveis.
