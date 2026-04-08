# Resumo dos resultados - Zona Norte

Este arquivo resume, de forma breve, os resultados de `iraja.ipynb`, `sao_cristovao.ipynb`, `tijuca.ipynb`, `um_del_castilho.ipynb`, `um_madureira.ipynb` e `um_maracana.ipynb`.

- Estratégia comum: interpolação temporal conservadora em lacunas curtas (até 4 horas).
- Resultado agregado: `24310` valores imputados no total.

## Resultados por notebook

- `iraja.ipynb`: `10845` imputações, com maior ganho em `pm10` (`6,60%` -> `4,16%`), `pm2_5` (`9,72%` -> `6,44%`) e melhora adicional em `so2`, `no`, `no2`, `nox`, `co`, `o3`, `ur` e `temp`.
- `sao_cristovao.ipynb`: `3700` imputações, com destaque para `so2` (`11,01%` -> `8,53%`) e reduções em `co`, `o3`, `pm10`, `ur` e `temp`; `no`, `no2`, `nox` e `pm2_5` permaneceram com `100%` de missing.
- `tijuca.ipynb`: `8583` imputações, com maior redução em `so2` (`13,01%` -> `8,64%`) e ganhos em `o3`, `co`, `pm10`, `no`, `no2`, `nox`, `temp` e `ur`; `pm2_5` seguiu com `100%` de missing.
- `um_del_castilho.ipynb`: `348` imputações, com melhora forte em `o3` (`2,36%` -> `0,25%`) e `co` (`2,19%` -> `0,38%`), além de reduções em `pm2_5`, `no`, `no2`, `nox`, `ur` e `temp`; `so2` e `pm10` ficaram em `100%` de missing.
- `um_madureira.ipynb`: `505` imputações, com destaque para `so2` (`14,01%` -> `9,66%`) e reduções em `co`, `pm2_5`, `o3`, `temp` e `ur`; `no`, `no2`, `nox` e `pm10` permaneceram com `100%` de missing.
- `um_maracana.ipynb`: `329` imputações, com maior ganho em `o3` (`8,90%` -> `5,66%`) e melhorias em `no`, `no2`, `nox`, `pm2_5`, `so2`, `temp`, `ur` e `co`; `pm10` permaneceu com `100%` de missing.

## Conclusão breve

O tratamento aumentou a completude sem alterar de forma relevante as estatísticas centrais das séries com dados observados. Ainda assim, persistem ausências estruturais (`100%` missing) para parte dos poluentes em diferentes estações, o que limita análises dessas variáveis.
