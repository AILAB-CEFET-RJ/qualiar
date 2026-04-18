# Resumo Consolidado: Internacoes x Poluentes e Variaveis Atmosfericas

## Objetivo

Este arquivo consolida os principais achados exploratorios dos notebooks de correlacao entre internacoes respiratorias, poluentes atmosfericos e variaveis meteorologicas, alem da sugestao final de features para as proximas etapas de modelagem.

## Leitura geral dos resultados

- Os sinais mais fortes apareceram em `O3`, `NO`, `CO`, `SO2` e `NOX`.
- `PM2.5` apresentou sinal moderado.
- `NO2` apresentou sinal moderado, com melhor resultado no valor do mesmo dia.
- `PM10` foi o sinal mais fraco entre os poluentes analisados.
- Nas variaveis meteorologicas, `umidade relativa` mostrou sinal mais forte que `temperatura`.
- Em varios casos, medias moveis defasadas superaram lags simples, sugerindo efeito acumulado de exposicao.

## Principais resultados por variavel

### Poluentes

| Variavel | Melhor sinal encontrado | Pearson | Spearman | Leitura resumida |
| --- | --- | ---: | ---: | --- |
| `o3` | `o3_ma_120d_shift_1d` | -0.4614 | -0.5440 | Sinal forte e negativo, concentrado em janela longa |
| `no` | `no_ma_30d_shift_1d` | 0.4856 | 0.5381 | Um dos sinais mais fortes, com acumulacao recente |
| `co` | `co_ma_120d_shift_1d` | 0.4016 | 0.4571 | Sinal forte e consistente em janela longa |
| `so2` | `so2_ma_150d_shift_21d` | 0.4404 | 0.3772 | Sinal forte, mas concentrado em janela longa e bem defasada |
| `nox` | `nox_ma_21d_shift_1d` | 0.3873 | 0.4315 | Sinal forte, com vantagem pequena sobre alternativas proximas |
| `no2` | `no2_lag0` | 0.2664 | 0.2907 | Melhor representacao foi o valor do mesmo dia |
| `pm2_5` | `pm2_5_ma_30d_shift_1d` | 0.2130 | 0.3130 | Sinal moderado, melhor em acumulacao recente |
| `pm10` | `pm10_ma_30d_shift_1d` | 0.1471 | 0.2425 | Sinal moderado para fraco |

### Variaveis meteorologicas

| Variavel | Melhor sinal encontrado | Pearson | Leitura resumida |
| --- | --- | ---: | --- |
| `temp` | `temp_ma_14d_shift_1d` | -0.304 | Temperatura mais baixa associada a mais internacoes |
| `ur` | `ur_ma_60d_shift_1d` | 0.394 | Umidade com efeito acumulado mais longo |

Observacoes meteorologicas:

- As correlacoes com anomalias mensais foram baixas para `temp` e `ur`.
- A interacao `frio_e_seco` nao parece robusta o suficiente para virar feature agora, porque houve pouquissimas observacoes nessa combinacao extrema.

## Sugestao final de features

### Features principais recomendadas

- `o3_ma_120d_shift_1d`
- `no_ma_30d_shift_1d`
- `co_ma_120d_shift_1d`
- `so2_ma_150d_shift_21d`
- `nox_ma_21d_shift_1d`
- `no2_lag0`
- `pm2_5_ma_30d_shift_1d`
- `pm10_ma_30d_shift_1d`
- `temp_ma_14d_shift_1d`
- `ur_ma_60d_shift_1d`

### Features complementares opcionais

Estas features so fazem sentido se quisermos manter uma segunda representacao simples da mesma variavel para comparacao, interpretabilidade ou teste de robustez:

- `o3_lag14`
- `no_lag0`
- `co_lag0`
- `so2_lag0`
- `nox_lag0`
- `no2_ma_21d_shift_1d`
- `pm2_5_lag0`
- `pm10_lag0`

## Priorizacao pratica para modelagem

### Prioridade alta

- `o3_ma_120d_shift_1d`
- `no_ma_30d_shift_1d`
- `co_ma_120d_shift_1d`
- `so2_ma_150d_shift_21d`
- `nox_ma_21d_shift_1d`
- `ur_ma_60d_shift_1d`

### Prioridade media

- `no2_lag0`
- `pm2_5_ma_30d_shift_1d`
- `temp_ma_14d_shift_1d`

### Prioridade secundaria

- `pm10_ma_30d_shift_1d`

## Conclusao

Se a modelagem precisar partir de um conjunto enxuto de variaveis, a melhor estrategia e comecar pelas features principais de maior prioridade, evitando redundancia entre medias moveis muito parecidas da mesma variavel. Em especial, `NO`, `O3`, `CO`, `SO2`, `NOX` e `umidade relativa` parecem hoje os candidatos mais fortes. `PM10` deve entrar apenas como candidato secundario, e a interacao `frio_e_seco` pode ficar fora por enquanto.
