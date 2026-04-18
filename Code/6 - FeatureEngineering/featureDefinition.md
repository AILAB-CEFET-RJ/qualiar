# Feature Definition

## Objetivo

Este documento consolida a definicao final das features para a etapa de feature engineering, combinando:

- os principais achados da EDA da serie de internacoes;
- os principais achados da analise de correlacao entre variaveis atmosfericas e internacoes.

A ideia aqui e sair de um conjunto amplo de candidatos para um conjunto final mais enxuto, priorizando sinal preditivo, interpretabilidade e baixa redundancia.

## Criterios de escolha

- Manter features que capturam os sinais mais fortes e mais consistentes da serie.
- Priorizar variaveis com melhor correlacao exploratoria e com interpretacao epidemiologica razoavel.
- Evitar varias features muito parecidas da mesma familia quando uma representacao principal ja cobre o padrao.
- Deixar como secundarias as features uteis para teste de robustez, ablation ou versoes mais complexas do modelo.

## Features finais escolhidas

## 1. Features endogenas da serie de internacoes

| Grupo | Features finais | Motivo |
| --- | --- | --- |
| Memoria imediata | `lag_1`, `lag_2`, `lag_3` | Capturam persistencia curta da serie e ajudam a ajustar a inercia diaria. |
| Memoria semanal | `lag_7`, `lag_14`, `lag_21`, `lag_28` | A recorrencia semanal foi um dos sinais mais fortes da EDA, com destaque para `t-7` e `t-14`. |
| Memoria mensal e anual | `lag_30`, `lag_365` | Capturam repeticao em escala mensal e sazonalidade anual. |
| Nivel recente | `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30` | Resumem o nivel local da serie e ajudam a capturar ondas epidemiologicas. |
| Variabilidade recente | `rolling_std_7`, `rolling_std_30` | Capturam mudancas de volatilidade, importantes numa serie com quebras e extremos. |
| Calendario semanal | `dia_semana`, `fim_de_semana` | A serie mostrou efeito semanal forte, com dias uteis muito acima de fim de semana. |
| Calendario anual | `mes`, `semana_epidemiologica`, `estacao` | Capturam a sazonalidade anual e o efeito de calendario observado na EDA. |
| Periodo de pico | `dummy_periodo_pico_sazonal` | Abril a julho concentram a maior carga sazonal e ajudam a marcar o periodo mais critico. |

### 2. Features atmosfericas principais

| Variavel | Feature final | Motivo |
| --- | --- | --- |
| `o3` | `o3_ma_120d_shift_1d` | Foi um dos sinais mais fortes da analise e concentrou o efeito em janela longa, com associacao negativa. |
| `no` | `no_ma_30d_shift_1d` | Um dos sinais mais fortes entre todos os poluentes, com vantagem clara sobre alternativas proximas. |
| `co` | `co_ma_120d_shift_1d` | Sinal forte e consistente, melhor representado por acumulacao de longo prazo. |
| `so2` | `so2_ma_150d_shift_21d` | Sinal forte, mas dependente de janela muito longa e bem defasada; melhor representacao de `SO2` na analise. |
| `nox` | `nox_ma_21d_shift_1d` | Melhor sintese para `NOX`, com sinal forte e consistente. |
| `no2` | `no2_lag0` | Unico caso em que o melhor resultado geral foi o valor do mesmo dia, acima das medias moveis defasadas. |
| `pm2_5` | `pm2_5_ma_30d_shift_1d` | Melhor representacao de `PM2.5`, com sinal moderado e interpretacao de acumulacao recente. |
| `temp` | `temp_ma_14d_shift_1d` | Melhor sintese para temperatura, com associacao negativa e janela curta de acumulacao. |
| `ur` | `ur_ma_60d_shift_1d` | Melhor sintese para umidade relativa, com efeito acumulado mais longo. |

## 3. Features que ficaram fora da selecao principal

- `pm10_ma_30d_shift_1d` nao entra no conjunto principal porque foi o sinal mais fraco entre os poluentes e deve ser tratado como candidato secundario.
- `frio_e_seco` nao entra no conjunto principal porque a analise conjunta de temperatura e umidade teve poucas observacoes extremas e nao mostrou robustez suficiente.
- Features baseadas em anomalias mensais de `temp` e `ur` nao entram no conjunto principal porque as correlacoes foram muito baixas.

## Features secundarias

Estas features podem ser testadas em uma segunda rodada de modelagem, especialmente para analise de robustez, interpretabilidade ou ensembles.

### 1. Serie de internacoes

- `diff_1`, `diff_7`, `diff_30`
- `rolling_min_7`, `rolling_max_7`
- `rolling_sum_7`, `rolling_sum_14`, `rolling_sum_30`
- `bloco_2012_2013`, `bloco_2014_2015`, `bloco_2016_2018`
- `dummy_extremo_positivo`, `dummy_extremo_negativo`
- `dias_desde_ultimo_extremo`
- `sin_ano`, `cos_ano`

Motivo:
Essas variaveis podem ajudar modelos mais flexiveis, mas nao sao a melhor base inicial porque aumentam bastante a dimensionalidade ou tendem a ser parcialmente redundantes com calendario, rolling windows e dummies de regime.

### 2. Variaveis atmosfericas

- `pm10_ma_30d_shift_1d`
- `o3_lag14`
- `no_lag0`
- `co_lag0`
- `so2_lag0`
- `nox_lag0`
- `no2_ma_21d_shift_1d`
- `pm2_5_lag0`
- `pm10_lag0`

Motivo:
Essas features podem servir como representacoes alternativas mais simples ou comparativas da mesma variavel, mas ficaram abaixo das features principais ou muito proximas delas.

## Recomendacao pratica de uso

Se a modelagem comecar com uma base enxuta, a recomendacao e usar:

- todas as features endogenas da secao 1;
- todas as features atmosfericas principais da secao 2, exceto `pm10`;
- `pm10_ma_30d_shift_1d` apenas em uma segunda rodada de teste;
- as features secundarias apenas em ablations ou modelos mais complexos.

## Conclusao

O conjunto final escolhido tenta equilibrar tres coisas:

- memoria temporal da propria serie de internacoes;
- calendario e quebras estruturais;
- exposicao atmosferica com melhor sinal exploratorio e menor redundancia.

Na pratica, a base principal deve ser composta pela serie historica, pelas features de calendario e regime e pelas covariaveis atmosfericas mais fortes: `o3`, `no`, `co`, `so2`, `nox`, `no2`, `pm2_5`, `temp` e `ur`. `pm10` entra como feature secundaria, e a interacao `frio_e_seco` fica fora por enquanto.
