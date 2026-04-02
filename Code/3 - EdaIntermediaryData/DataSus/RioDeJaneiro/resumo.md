# Resumo consolidado da EDA da série de internações respiratórias

Este documento consolida os principais achados interpretativos dos notebooks `1` a `6` da EDA em `RioDeJaneiro`, com os resultados mais recentes.

Período analisado: `2012` a `2018`.

## 1. Principais descobertas por etapa

### 1.1 Caracterização inicial da série

- Média diária: `370,9`; mediana: `340`.
- Dispersão relevante: `desvio padrão = 185,7`, `IQR = 234`, `CV = 0,50`.
- Cauda alta: `p95 = 716`, `p99 = 980`, máximo observado `1218`.
- Maiores valores concentrados em `maio-junho de 2012` (topo com `1218`, `1190`, `1176`, `1162`).
- Leitura geral: assimetria à direita e picos concentrados em janelas específicas.

### 1.2 Sazonalidade e calendário

- Sazonalidade anual forte + efeito semanal consistente.
- Médias anuais (exemplos): `2012 = 557,0`, `2013 = 461,9`, `2015 = 418,2`, `2017 = 240,4`, `2018 = 265,3`.
- Padrão mensal: subida de `março (336,9)` para `abril (483,0)`, pico em `maio (554,2)`, ainda alto em `junho (497,3)` e `julho (441,1)`, mínimo em `dezembro (256,7)`.
- Diferença entre maior e menor mês: cerca de `116%`.
- Semanas epidemiológicas com maior carga: `16 a 25`, pico na semana `21 (589,5)`.
- Dia da semana: `segunda (431,5)`, `quarta (419,5)` e `terça (409,7)` acima de `sábado (290,9)` e `domingo (276,4)`.
- Dias úteis (`405,9`) cerca de `43%` acima de fins de semana (`283,6`).
- Estações: `outono (457,8)`, `inverno (437,2)`, `verão (266,0)`.

### 1.3 Tendência e decomposição (MSTL)

- Tendência caiu de `605,4` (2012-01-01) para `242,6` (2018-12-31): redução de `59,9%`.
- Tendência média anual: queda de `2012 (548,8)` até `2017 (239,5)`, com recomposição moderada em `2018 (251,3)`.
- Componente semanal: positivo em `Seg (+63,0)`, `Ter (+40,3)`, `Qua (+53,2)`; negativo em `Sab (-81,8)` e `Dom (-98,3)`.
- Amplitude p5-p95 por componente:
- `sazonal_total = 427,7`
- `sazonal_365 = 355,4`
- `tendencia = 330,4`
- `sazonal_7 = 238,5`
- `residuo = 279,8`
- Intensidade sazonal caiu ao longo dos anos:
- semanal `2012: 378,4` -> `2017: 144,1` -> `2018: 150,3`
- anual `2012: 495,7` -> `2017: 251,8` -> `2018: 255,6`

### 1.4 Dependência temporal

- Persistência curta forte e recorrência semanal marcada.
- Correlações principais:
- `t-1 = 0,741`
- `t-7 = 0,825` (ACF `0,822`)
- `t-14 = 0,797` (ACF `0,793`)
- `t-30 = 0,579` (ACF `0,573`)
- `t-365 = 0,540` (ACF `0,392`)
- ACF com decaimento lento, coerente com tendência + sazonalidade e não estacionariedade em nível.

### 1.5 Quebras estruturais e eventos

- Queda de patamar por blocos:
- `2012-2013: 509,5`
- `2014-2015: 395,1`
- `2016-2018: 262,4`
- Comparação binária:
- `2012-2015: 452,3` vs `2016-2018: 262,4` (`-42,0%`)
- Desvio padrão: `188,9` -> `110,8` (`-41,3%`)
- p95: `819,0` -> `470,5` (`-42,6%`)
- Ondas (média móvel 30d): `2012-06-05 (922,6)`, `2015-05-29 (741,8)`, `2013-05-07 (690,3)`, `2016-06-24 (483,6)`, `2018-05-29 (411,5)`.
- Mudanças abruptas de nível: destaque para `2015-05-05`, `2013-04-30`, `2015-07-09`, `2012-08-12`, `2012-06-05`.
- Mudanças de variância: destaque para `2013-04-11`, `2015-04-20`, `2012-07-12`, `2015-07-20`, `2013-09-06`.
- Pettitt mensal: *changepoint* principal em `2015-09-01` (p-valor aproximado ~0).

### 1.6 Anomalias e extremos

- Extremos totais: `140 dias` (`5,48%` da série).
- `79` picos extremos (`3,09%`) e `61` vales extremos (`2,39%`).
- Maiores picos brutos: `2012-05-14 (1218)`, `2012-05-25 (1190)`, `2012-05-28 (1176)`.
- Maiores desvios ajustados positivos:
- `2012-05-30: +627,9 (z=14,29)`
- `2012-05-25: +571,3`
- `2015-04-26: +541,1`
- Maiores desvios ajustados negativos:
- `2014-06-23: -385,8`
- `2014-04-29: -378,0`
- `2014-05-29: -363,2`
- Distribuição anual de extremos:
- `2012: 39 (10,66%)`
- `2014: 28 (7,67%)`
- `2013: 22 (6,03%)`
- `2015: 22 (6,03%)`
- `2018: 11 (3,01%)`
- `2016: 10 (2,73%)`
- `2017: 8 (2,19%)` (sem picos extremos)
- Concentração mensal em `abril-maio-junho`, com destaque para `maio (36 extremos: 23 picos, 13 vales)`.

## 2. Síntese geral da série

- A série combina `queda estrutural`, `sazonalidade anual`, `sazonalidade semanal`, `quebras de regime`, `ondas episódicas` e `extremos localizados`.
- O período `2012-2015` concentra maior nível médio, maior volatilidade e maior intensidade de eventos.
- O período `2016-2018` opera em patamar mais baixo e menos volátil, mas ainda com repiques relevantes.
- Parte da autocorrelação observada na série bruta reflete estrutura (tendência + calendário), não apenas memória temporal pura.
- Conclusão: há sinal previsível, mas a série não deve ser tratada como processo homogêneo e estacionário.

## 3. Features candidatas para previsão

### 3.1 Memória temporal

- `lag_1`, `lag_2`, `lag_3`
- `lag_7`, `lag_14`, `lag_21`, `lag_28`
- `lag_30`, `lag_365`
- `diff_1`, `diff_7`, `diff_30`
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`
- `rolling_std_7`, `rolling_std_14`, `rolling_std_30`
- `rolling_min_7`, `rolling_max_7`
- `rolling_sum_7`, `rolling_sum_14`, `rolling_sum_30`

### 3.2 Calendário e sazonalidade

- `dia_semana`
- `fim_de_semana`
- `mes`
- `trimestre`
- `semana_epidemiologica`
- `estacao`
- `feriado`
- `vespera_feriado`
- `pos_feriado`
- `dias_uteis_no_mes`
- `sin_ano`, `cos_ano`

### 3.3 Regime e quebra estrutural

- `indice_tempo`
- `ano`
- `bloco_2012_2013`
- `bloco_2014_2015`
- `bloco_2016_2018`
- `fase_2012_2015`
- `fase_2016_2018`
- `dummy_pos_2015_09`
- `distancia_ao_changepoint_2015_09`

### 3.4 Ondas e anomalias

- `dummy_periodo_pico_sazonal` (abril-julho)
- `dummy_semanas_16_25`
- `dummy_extremo_positivo`
- `dummy_extremo_negativo`
- `dias_desde_ultimo_extremo`
- `dummy_onda_epidemiologica`
- `valor_esperado_decomposto`
- `desvio_ajustado`
- `z_robusto`

### 3.5 Covariáveis externas recomendadas

- Clima: temperatura (média/min/max), umidade, precipitação, frentes frias
- Poluição: `PM2.5`, `PM10`, `NO2`, `O3`, `CO`
- Indicadores de circulação viral (se disponíveis)
- Proxies assistenciais/operacionais (se disponíveis)

## 4. Recomendação prática de base inicial

Conjunto inicial sugerido:

- Lags: `1, 7, 14, 21, 28, 30, 365`
- Janelas: `rolling_mean_7/14/30`, `rolling_std_7/30`
- Calendário: `dia_semana`, `fim_de_semana`, `mes`, `semana_epidemiologica`, `estacao`, `feriado`
- Regime: `bloco_2012_2013`, `bloco_2014_2015`, `bloco_2016_2018`, `dummy_pos_2015_09`
- Eventos: `dummy_periodo_pico_sazonal`, `dummy_extremo_positivo`, `dummy_extremo_negativo`
- Clima/poluição com lags `1`, `3`, `7`, `14`

## 5. Pipeline recomendada (próximos passos)

### 5.1 Consolidação final da base

1. Congelar a versão da série diária para modelagem.
2. Revisar faltantes, duplicatas e consistência das datas extremas.
3. Marcar rupturas, ondas e extremos no dataset final.

### 5.2 Definição do problema

1. Definir horizonte (`D+1`, `D+7`, `D+14` ou semanal agregado).
2. Definir alvo (`nivel`, `log1p(y)`, `diff_1_7(y)`).
3. Definir métricas (`MAE`, `RMSE`, `sMAPE`) e avaliação por subperíodo.

### 5.3 Baselines obrigatórios

1. Naive (`y_t = y_{t-1}`)
2. Seasonal naive (`y_t = y_{t-7}`)
3. Média móvel (`7` e `14` dias)
4. Baseline por regime recente (`2016-2018`)

### 5.4 Modelos candidatos

1. Regressão com lags e calendário (regularizada)
2. SARIMA/SARIMAX
3. XGBoost/LightGBM/Random Forest

### 5.5 Validação temporal

1. Splits temporais expansivos/deslizantes
2. Sem split aleatório
3. Avaliação global e por fase (`2012-2015` vs `2016-2018`)

### 5.6 Análise de erro dirigida

1. Erro por mês/estação/semana epidemiológica
2. Erro por dia útil vs fim de semana
3. Erro em períodos de onda e extremos

## 6. Conclusão executiva

- A série é parcialmente previsível, mas com dinâmica complexa (memória curta + ciclos + regime + extremos).
- O maior risco é modelar como processo único e estacionário.
- Melhor estratégia: combinar `lags + calendário + regime + covariáveis externas` com validação temporal rigorosa.
- Ponto de partida forte: features semanais, dummies de ruptura (`2015-09`) e alvo transformado (`log1p` ou `diff_1_7`) para teste comparativo.