# Resumo dos resultados - Zona Oeste

Este arquivo resume, de forma breve, os resultados de `bangu.ipynb`, `campo_grande.ipynb`, `pedra_guaratiba.ipynb`, `um_bangu.ipynb` e `um_recreio.ipynb`.

- Estratégia comum: interpolação temporal conservadora em lacunas curtas (até 4 horas).
- Resultado agregado: `23620` valores imputados no total.

## Resultados por notebook

- `bangu.ipynb`: `10200` imputações, com maior ganho em `no` (`6,37%` -> `3,40%`), além de reduções em `no2`, `nox` e `so2`; `pm2_5` permaneceu com `100%` de missing.
- `campo_grande.ipynb`: `10609` imputações, com destaque para `no` (`7,84%` -> `4,33%`), `no2`, `nox` e `so2`; `pm2_5` também ficou em `100%` de missing.
- `pedra_guaratiba.ipynb`: `2234` imputações, com melhora em `pm10` (`7,31%` -> `5,58%`) e `o3` (`7,02%` -> `6,15%`); `so2`, `no`, `no2`, `co`, `nox` e `pm2_5` seguiram com `100%` de missing.
- `um_bangu.ipynb`: `374` imputações, com maior redução em `so2` (`14,04%` -> `11,88%`) e ganhos adicionais em `co`, `pm2_5` e `o3`; `temp` e `ur` foram zerados, enquanto `no`, `no2`, `nox` e `pm10` permaneceram com `100%` de missing.
- `um_recreio.ipynb`: `203` imputações, com destaque para `so2` (`10,61%` -> `6,17%`) e `co` (`0,91%` -> `0,22%`); `pm2_5` melhorou pouco (`54,34%` -> `54,06%`) e `no`, `no2`, `nox` e `pm10` seguiram com `100%` de missing.

## Conclusão breve

O tratamento aumentou a completude sem alterar de forma relevante as estatísticas centrais das séries com dados observados. Ainda assim, persistem ausências estruturais (`100%` missing) para parte dos poluentes em diferentes estações, o que limita análises dessas variáveis.
