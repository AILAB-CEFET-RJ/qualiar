# Resumo consolidado da EDA da série de internações respiratórias

Este documento resume os principais achados interpretativos dos notebooks de EDA, organiza sugestões de features candidatas para previsão e fecha com uma pipeline sugerida de próximos passos.

## 1. Principais descobertas por etapa

### 1. Caracterização inicial da série

- A série tem nível médio alto (`322,8` internações/dia), mas a mediana menor (`282`) indica assimetria à direita.
- A variabilidade é elevada (`desvio padrão = 202,3`, `CV = 0,63`, `p95 = 714`, `p99 = 978,5`), o que mostra que a oscilação diária é grande em relação ao próprio nível da série.
- Os maiores volumes ficaram fortemente concentrados em `maio-junho de 2012`, com um pico adicional relevante em `maio de 2015`.
- A série não se comporta como uma sequência de pequenas flutuações em torno de um patamar fixo; ela contém picos extremos importantes e janelas muito específicas de alta.
- Implicação analítica: vale considerar transformações como `log1p` ou `Box-Cox`, tratamento robusto de extremos e investigação de ondas ou mudanças de registro.

### 2. Sazonalidade e calendário

- A série apresenta sazonalidade anual forte e um efeito semanal consistente.
- O pico mensal ocorre em `maio (453,3)`, com nível ainda alto em `abril`, `junho` e `julho`.
- As semanas epidemiológicas `16 a 25` concentram as maiores médias, com pico na `semana 21 (473,1)`.
- Os dias úteis (`346,3`) ficam cerca de `31%` acima dos fins de semana (`264,3`), com segundas, terças e quartas mais altas do que sábados e domingos.
- `Outono` e `inverno` são os períodos de maior carga, indicando que a subida começa antes do inverno.
- Implicação analítica: variáveis de calendário precisam ser tratadas como estruturais, e não como detalhes secundários.

### 3. Tendência e decomposição

- A decomposição por `MSTL` mostrou queda estrutural muito forte de longo prazo, com a tendência saindo de `650,1` para `26,0`, redução de cerca de `96%`.
- Há sazonalidade semanal bem definida, com efeito positivo no início da semana e negativo no fim de semana.
- A sazonalidade anual também é forte, com amplitude alta e concentração no outono-inverno.
- O resíduo continua elevado (`255,0` no intervalo p5-p95), sugerindo eventos não explicados apenas por tendência e sazonalidade.
- A intensidade sazonal cai ao longo do tempo: a série não apenas perde nível médio, mas também perde amplitude sazonal.
- Implicação analítica: a série bruta não é estacionária e provavelmente não deve ser modelada como um único regime estável.

### 4. Dependência temporal

- A série bruta tem persistência forte no curto prazo e um padrão semanal muito marcado.
- Os lags mais fortes foram `t-1 = 0,842`, `t-7 = 0,883` e `t-14 = 0,865`, com `t-30 = 0,741` e `t-365 = 0,718` ainda relevantes.
- A ACF da série bruta decai lentamente, o que reforça a presença de tendência e sazonalidade.
- Quando a análise é repetida em versões transformadas, boa parte da autocorrelação desaparece:
  - Na `diferença de 1 dia`, a persistência longa cai fortemente.
  - Na `diferença sazonal de 7 dias`, a persistência residual fica muito baixa, mostrando que a sazonalidade semanal era um dos principais motores da ACF bruta.
  - Na série `detrendida (MM30)`, ainda sobra sinal em `t-7` e `t-14`, indicando memória semanal real além da tendência.
  - A `dessazonalização semanal simples` quase não muda a estrutura da ACF, sugerindo que o efeito semanal não é apenas um desvio fixo por dia da semana.
- Implicação analítica: a série bruta superestima a memória temporal porque mistura memória real com não estacionariedade.

### 5. Quebras estruturais e eventos

- A série não é estacionária ao longo do período e apresenta mudanças de regime relevantes.
- O nível médio cai de `434,9` no `Pré-COVID` para `221,6` no `COVID agudo` e `149,2` no `Pós-COVID`.
- Na comparação binária, a média cai de `430,4` para `172,3` internações por dia, uma redução de aproximadamente `60%`.
- As maiores ondas ficam concentradas sobretudo entre `2012` e `2015`, com novos eventos relevantes em `2018` e `2019`.
- O teste de `Pettitt` aponta um changepoint principal em `2019-07-01`.
- Há evidências de mudanças abruptas tanto de nível quanto de variância, inclusive em `2020-2022`.
- Implicação analítica: modelos que ignorarem regime, ruptura e segmentação temporal tendem a errar o patamar recente da série.

### 6. Anomalias e extremos

- Foram identificados `222 dias extremos (4,34% da série)`, com predomínio de `picos extremos (132)` sobre `vales extremos (90)`.
- Os maiores picos brutos se concentram em `maio-junho de 2012`, mas as maiores anomalias ajustadas aparecem em eventos como `2018-07-01`, `2015-05-19` e `2012-05-23`.
- Isso mostra que nem todo valor bruto muito alto é realmente anômalo; alguns estão próximos do valor esperado para aquele contexto.
- Os menores valores brutos se concentram no fim de `2025`, mas muitos parecem refletir o patamar estruturalmente baixo do fim da série, e não um evento raro.
- Os vales ajustados mais fortes aparecem em `2013-2014`, em meses que costumam ser intensos, sugerindo sub-registro, efeito operacional ou queda localizada.
- `Abril`, `maio` e `junho` concentram os principais picos; `dezembro` concentra mais vales.
- Implicação analítica: extremos devem ser tratados como parte da dinâmica da série, e não removidos automaticamente como outliers.

## 2. Síntese geral da série

- A série combina `tendência de queda`, `sazonalidade anual forte`, `sazonalidade semanal clara`, `quebras estruturais`, `ondas episódicas` e `extremos localizados`.
- O período `2012-2015` concentra os maiores níveis, as maiores ondas e várias mudanças abruptas.
- O período `2018-2019` concentra eventos ajustados importantes e repiques intermediários.
- A partir de `2019-2020`, a série entra em um patamar muito mais baixo, com nova configuração de nível e variabilidade.
- A memória temporal existe, mas parte importante dela desaparece quando removemos tendência e sazonalidade.
- Em resumo: a série é previsível em parte, mas não pode ser tratada como um processo simples, homogêneo e estacionário.

## 3. Sugestão de features candidatas para previsão

### 3.1. Features de memória temporal

- `lag_1`, `lag_2`, `lag_3`
- `lag_7`, `lag_14`, `lag_21`, `lag_28`
- `lag_30`
- `lag_365`
- `diff_1`, `diff_7`, `diff_30`
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`
- `rolling_std_7`, `rolling_std_14`, `rolling_std_30`
- `rolling_min_7`, `rolling_max_7`
- `rolling_sum_7`, `rolling_sum_14`, `rolling_sum_30`

### 3.2. Features de calendário

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
- `sin/cos` anual para capturar ciclo contínuo do ano

### 3.3. Features de tendência e regime

- `indice_tempo`
- `ano`
- `dummy_pos_2019_07`
- `dummy_pre_covid`, `dummy_covid_agudo`, `dummy_pos_covid`
- `segmento_regime` baseado nos changepoints detectados
- `distancia_ao_changepoint`
- `tendencia_local_mm30`

### 3.4. Features de onda, evento e anomalia

- `dummy_periodo_pico_sazonal` para `abril-julho`
- `dummy_semanas_16_25`
- `dummy_extremo_positivo`
- `dummy_extremo_negativo`
- `dias_desde_ultimo_extremo`
- `dummy_onda_epidemiologica`
- `nivel_esperado_decomposto`
- `desvio_ajustado`

### 3.5. Features externas recomendadas

- `temperatura_media`, `temperatura_minima`, `temperatura_maxima`
- `umidade_relativa`
- `precipitacao`
- `frente_fria` ou indicadores meteorológicos de mudança abrupta
- `PM2.5`, `PM10`, `NO2`, `O3`, `CO`
- indicadores de circulação viral, se disponíveis
- volume de atendimentos, ocupação hospitalar ou proxies assistenciais, se existirem

### 3.6. Alvos candidatos para modelagem

- `y_em_nivel` para modelos com features explícitas de calendário e regime
- `log1p(y)` para reduzir assimetria
- `diff_1(y)` para remover parte da tendência
- `diff_7(y)` para remover sazonalidade semanal
- `diff_1_7(y)` como candidato forte para aproximar a série de estacionariedade

## 4. Recomendação prática de conjunto inicial de features

Se fosse para montar uma primeira base de modelagem agora, eu começaria com:

- `lag_1`, `lag_7`, `lag_14`, `lag_21`, `lag_28`, `lag_30`, `lag_365`
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`
- `rolling_std_7`, `rolling_std_30`
- `dia_semana`, `fim_de_semana`, `mes`, `semana_epidemiologica`, `estacao`, `feriado`
- `dummy_pos_2019_07`, `dummy_pre_covid`, `dummy_covid_agudo`, `dummy_pos_covid`
- `dummy_periodo_pico_sazonal`, `dummy_extremo_positivo`, `dummy_extremo_negativo`
- variáveis de `clima` e `poluição` com lags de `1`, `3`, `7` e `14` dias

Esse conjunto inicial combina memória curta, efeito semanal, ciclo anual, regime e covariáveis externas, que são justamente os pilares mais fortes identificados na EDA.

## 5. Pipeline sugerida de próximos passos

### 5.1. Consolidação final da base

1. Congelar a versão da série diária que será usada na modelagem.
2. Revisar datas, faltantes, duplicatas e coerência dos extremos mais relevantes.
3. Marcar no dataset os períodos de ruptura, ondas e eventos extremos já detectados.

### 5.2. Definição do problema de previsão

1. Definir horizonte de previsão: `D+1`, `D+7`, `D+14` ou previsão semanal agregada.
2. Definir se o objetivo é prever a série em nível ou uma versão transformada.
3. Definir quais métricas serão usadas: `MAE`, `RMSE`, `MAPE` com cautela, `sMAPE`, erro por período sazonal.

### 5.3. Montagem da base de features

1. Construir primeiro a base com features internas da própria série.
2. Integrar clima, poluição e outras covariáveis externas.
3. Gerar lags e janelas móveis também para as covariáveis externas.
4. Criar dummies de regime, feriado, semanas críticas e períodos de pico.

### 5.4. Escolha dos alvos candidatos

1. Testar pelo menos três versões do alvo: `nível`, `log1p(y)` e `diff_1_7(y)`.
2. Comparar qual delas oferece melhor equilíbrio entre interpretabilidade, estabilidade e desempenho preditivo.
3. Validar se a transformação escolhida não destruiu sinais importantes para o uso final.

### 5.5. Baselines obrigatórios

1. `Naive`: previsão igual ao último valor observado.
2. `Seasonal naive`: previsão igual ao valor de `t-7`.
3. `Média móvel`: previsão pela média dos últimos `7` ou `14` dias.
4. Um baseline por regime recente, para não comparar modelos sofisticados com uma referência irrealista.

### 5.6. Modelos candidatos

1. `SARIMA` ou `SARIMAX`, principalmente se o alvo transformado ficar próximo de estacionário.
2. Regressão linear regularizada com lags e calendário.
3. `XGBoost`, `LightGBM` ou `Random Forest` com features tabulares.
4. Se fizer sentido depois, testar modelos mais complexos só após os baselines fortes estarem bem estabelecidos.

### 5.7. Validação temporal

1. Usar validação temporal por janelas deslizantes ou expansivas.
2. Evitar splits aleatórios.
3. Avaliar desempenho global e também por subperíodo: `2012-2015`, `2016-2019`, `2020+`.
4. Checar se o modelo superestima o período recente por causa dos anos iniciais mais altos.

### 5.8. Análise de erro

1. Medir erro por mês, estação e semana epidemiológica.
2. Medir erro em dias úteis versus fins de semana.
3. Medir erro em períodos de pico, ruptura e extremo.
4. Identificar em que tipo de situação cada modelo falha mais.

### 5.9. Refinamento guiado por evidência

1. Se o erro continuar alto em picos, incluir features de ondas e variáveis externas mais sensíveis ao outono-inverno.
2. Se o erro piorar após 2019, reforçar variáveis de regime e treinar modelos separados por período.
3. Se a série em nível ficar muito instável, priorizar transformações do alvo e reconstrução para o nível original.

### 5.10. Entrega final

1. Escolher um modelo principal e um baseline de referência.
2. Documentar as features usadas e a transformação do alvo.
3. Gerar gráficos de previsão, erro e importância de variáveis.
4. Preparar um fluxo simples de atualização periódica da base e reestimação do modelo.

## 6. Conclusão executiva

- A série possui sinal previsível, mas esse sinal está distribuído em vários componentes: memória curta, ciclo semanal, ciclo anual, tendência de queda, rupturas e extremos.
- O principal risco analítico é tratar a série como estacionária e homogênea, porque a EDA mostrou exatamente o contrário.
- O melhor caminho é montar uma base de previsão que combine `lags + calendário + regime + covariáveis externas`, com validação temporal rigorosa.
- Entre os próximos testes, a combinação de `lags semanais`, `features de calendário`, `dummies de ruptura` e um alvo transformado como `diff_1_7(y)` parece um ponto de partida especialmente promissor.