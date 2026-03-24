# Resumo consolidado da EDA da serie de internacoes respiratorias

Este documento consolida os principais achados interpretativos dos notebooks `1` a `6`, organiza sugestoes de features candidatas para previsao e fecha com uma pipeline sugerida de proximos passos.

O recorte considerado aqui e o periodo de `2012` a `2018`, alinhado com a disponibilidade das bases de qualidade do ar.

## 1. Principais descobertas por etapa

### 1. Caracterizacao inicial da serie

- A serie tem nivel medio alto (`452,3` internacoes/dia) e mediana menor (`420`), o que indica assimetria a direita.
- A variabilidade e relevante (`desvio padrao = 192,7`, `IQR = 240`, `CV = 0,43`, `p95 = 812`, `p99 = 1062,3`), mostrando oscilacao diaria importante.
- O valor maximo da serie foi `1358`, e os maiores volumes ficaram fortemente concentrados em `maio-junho de 2012`, com destaque adicional para `maio de 2015`.
- A serie nao se comporta como pequenas flutuacoes em torno de um patamar fixo; ela contem picos muito concentrados em janelas especificas.
- Implicacao analitica: vale considerar transformacoes como `log1p` ou `Box-Cox`, tratamento robusto de extremos e investigacao de ondas ou mudancas de regime.

### 2. Sazonalidade e calendario

- A serie apresenta sazonalidade anual forte e um efeito semanal consistente.
- As maiores medias anuais aparecem em `2012 (607,9)`, `2013 (528,7)` e `2015 (490,3)`, reforcando que o periodo inicial concentra os maiores niveis da serie.
- O pico mensal ocorre em `maio (666,7)`, com nivel ainda alto em `abril`, `junho` e `julho`.
- As semanas epidemiologicas `16 a 25` concentram as maiores medias, com pico na `semana 21 (706,9)`.
- Os dias uteis (`490,9`) ficam cerca de `38%` acima dos fins de semana (`355,7`).
- `Outono (553,4)` e `inverno (532,5)` sao os periodos de maior carga.
- Implicacao analitica: variaveis de calendario devem ser tratadas como parte estrutural da serie, e nao como efeito marginal.

### 3. Tendencia e decomposicao

- A decomposicao por `MSTL` mostrou queda estrutural ao longo do periodo, com a tendencia saindo de `633,1` para `359,8`, reducao de cerca de `43,2%`.
- O perfil anual da tendencia cai de `2012 (592,4)` ate `2017 (343,7)`, com leve recomposicao em `2018 (365,9)`.
- Ha sazonalidade semanal bem definida, com efeito positivo em `segunda (+77,9)` e `quarta (+56,3)` e efeito negativo em `sabado (-89,8)` e `domingo (-116,0)`.
- A sazonalidade anual tambem e forte, com amplitude de `410,6`, e a sazonalidade total foi o componente de maior amplitude (`491,9`).
- O residuo continua relevante (`303,0` no intervalo p5-p95), sugerindo eventos nao explicados apenas por tendencia e sazonalidade.
- A intensidade sazonal diminui ao longo do tempo, especialmente da comparacao entre `2012` e `2017-2018`.
- Implicacao analitica: a serie bruta nao e estacionaria e nao deve ser tratada como um unico regime estavel.

### 4. Dependencia temporal

- A serie bruta tem persistencia importante no curto prazo e um padrao semanal muito marcado.
- Os lags mais fortes foram `t-1 = 0,712`, `t-7 = 0,802` e `t-14 = 0,770`, com `t-30 = 0,521` e `t-365 = 0,514` ainda relevantes.
- A ACF da serie bruta decai lentamente, o que reforca a presenca de tendencia e sazonalidade.
- Quando a analise e repetida em versoes transformadas, boa parte da autocorrelacao desaparece:
- Na `diferenca de 1 dia`, a persistencia longa cai fortemente.
- Na `diferenca sazonal de 7 dias`, a persistencia residual fica muito baixa, mostrando que a sazonalidade semanal era um dos principais motores da ACF bruta.
- Na serie `detrendida (MM30)`, ainda sobra sinal em `t-7` e `t-14`, indicando memoria semanal real alem da tendencia.
- A `dessazonalizacao semanal simples` quase nao muda a estrutura da ACF, sugerindo que o efeito semanal nao e apenas um desvio fixo por dia da semana.
- Implicacao analitica: a serie bruta superestima a memoria temporal porque mistura memoria real com nao estacionariedade.

### 5. Quebras estruturais e eventos

- A serie nao e estacionaria ao longo do periodo e apresenta mudancas de regime relevantes.
- A comparacao entre blocos temporais mostrou queda progressiva do nivel medio: `568,4` em `2012-2013`, `464,6` em `2014-2015` e `366,6` em `2016-2018`.
- Na comparacao binaria entre fases, a media cai de `516,5` em `2012-2015` para `366,6` em `2016-2018`, reducao de cerca de `29,0%`.
- A dispersao tambem diminui, com queda de aproximadamente `30,1%` no desvio padrao e `29,7%` no percentil 95.
- As maiores ondas ficaram concentradas em `2012-06-05 (1019,7)`, `2015-05-29 (858,0)` e `2013-05-07 (768,3)`.
- O teste de `Pettitt` apontou um changepoint principal em `2015-08-01`.
- Ha evidencias de mudancas abruptas de nivel e variancia principalmente entre `2012` e `2015`, com novos sinais em `2016` e `2018`.
- Implicacao analitica: modelos que ignorarem regime, ruptura e segmentacao temporal tendem a errar o patamar da segunda metade da serie.

### 6. Anomalias e extremos

- Foram identificados `117 dias extremos (4,58% da serie)`, com predominio de `picos extremos (64)` sobre `vales extremos (53)`.
- Os maiores picos brutos se concentram em `maio-junho de 2012`, com destaque adicional para `2015-05-19`.
- A maior anomalia ajustada aparece em `2012-05-25`, com desvio de `+584,9` e `z_robusto = 11,23`.
- Tambem se destacam eventos ajustados como `2018-04-01 (+484,2)`, `2012-05-27 (+484,0)`, `2012-06-05 (+475,6)` e `2015-04-18 (+473,2)`.
- Os vales ajustados mais fortes aparecem em `2013-05-23 (-406,6)`, `2014-06-02 (-403,4)` e `2014-06-23 (-396,7)`.
- `2012` concentra `35 extremos (9,6% dos dias)`, seguido por `2014 (26; 7,1%)` e `2015 (16; 4,4%)`.
- `Abril`, `maio`, `junho` e `julho` concentram a maior parte dos extremos, com destaque para `maio (29 extremos, sendo 18 picos e 11 vales)`.
- Implicacao analitica: extremos devem ser tratados como parte da dinamica da serie, e nao removidos automaticamente como outliers.

## 2. Sintese geral da serie

- A serie combina `tendencia de queda`, `sazonalidade anual forte`, `sazonalidade semanal clara`, `quebras estruturais`, `ondas episodicas` e `extremos localizados`.
- O periodo `2012-2015` concentra os maiores niveis, as maiores ondas e varias mudancas abruptas.
- O periodo `2016-2018` opera em patamar mais baixo, mas ainda preserva sazonalidade clara e alguns repiques relevantes, como o evento ajustado de `2018-04-01`.
- A memoria temporal existe, mas parte importante dela desaparece quando removemos tendencia e sazonalidade.
- Em resumo: a serie e previsivel em parte, mas nao pode ser tratada como um processo simples, homogeneo e estacionario.

## 3. Sugestao de features candidatas para previsao

### 3.1. Features de memoria temporal

- `lag_1`, `lag_2`, `lag_3`
- `lag_7`, `lag_14`, `lag_21`, `lag_28`
- `lag_30`
- `lag_365`
- `diff_1`, `diff_7`, `diff_30`
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`
- `rolling_std_7`, `rolling_std_14`, `rolling_std_30`
- `rolling_min_7`, `rolling_max_7`
- `rolling_sum_7`, `rolling_sum_14`, `rolling_sum_30`

### 3.2. Features de calendario

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
- `sin_ano`, `cos_ano` para capturar o ciclo continuo do ano

### 3.3. Features de tendencia e regime

- `indice_tempo`
- `ano`
- `bloco_2012_2013`
- `bloco_2014_2015`
- `bloco_2016_2018`
- `fase_2012_2015`
- `fase_2016_2018`
- `dummy_pos_2015_08`
- `distancia_ao_changepoint_2015_08`
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
- `z_robusto`

### 3.5. Features externas recomendadas

- `temperatura_media`, `temperatura_minima`, `temperatura_maxima`
- `umidade_relativa`
- `precipitacao`
- indicadores de `frente_fria` ou mudanca meteorologica abrupta
- `PM2.5`, `PM10`, `NO2`, `O3`, `CO`
- indicadores de circulacao viral, se disponiveis
- proxies assistenciais, se existirem, como volume de atendimentos ou ocupacao

### 3.6. Alvos candidatos para modelagem

- `y_em_nivel` para modelos com features explicitas de calendario e regime
- `log1p(y)` para reduzir assimetria
- `diff_1(y)` para remover parte da tendencia
- `diff_7(y)` para remover a sazonalidade semanal
- `diff_1_7(y)` como candidato forte para aproximar a serie de estacionariedade

## 4. Recomendacao pratica de conjunto inicial de features

Se fosse para montar uma primeira base de modelagem agora, eu comecaria com:

- `lag_1`, `lag_7`, `lag_14`, `lag_21`, `lag_28`, `lag_30`, `lag_365`
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`
- `rolling_std_7`, `rolling_std_30`
- `dia_semana`, `fim_de_semana`, `mes`, `semana_epidemiologica`, `estacao`, `feriado`
- `bloco_2012_2013`, `bloco_2014_2015`, `bloco_2016_2018`, `dummy_pos_2015_08`
- `dummy_periodo_pico_sazonal`, `dummy_extremo_positivo`, `dummy_extremo_negativo`
- variaveis de `clima` e `poluicao` com lags de `1`, `3`, `7` e `14` dias

Esse conjunto inicial combina memoria curta, efeito semanal, ciclo anual, regime e covariaveis externas, que sao justamente os pilares mais fortes identificados na EDA.

## 5. Pipeline sugerida de proximos passos

### 5.1. Consolidacao final da base

1. Congelar a versao da serie diaria que sera usada na modelagem.
2. Revisar datas, faltantes, duplicatas e coerencia dos extremos mais relevantes.
3. Marcar no dataset os periodos de ruptura, ondas e eventos extremos ja detectados.

### 5.2. Definicao do problema de previsao

1. Definir horizonte de previsao: `D+1`, `D+7`, `D+14` ou previsao semanal agregada.
2. Definir se o objetivo e prever a serie em nivel ou uma versao transformada.
3. Definir quais metricas serao usadas: `MAE`, `RMSE`, `sMAPE` e erro por periodo sazonal.

### 5.3. Montagem da base de features

1. Construir primeiro a base com features internas da propria serie.
2. Integrar clima, poluicao e outras covariaveis externas.
3. Gerar lags e janelas moveis tambem para as covariaveis externas.
4. Criar dummies de regime, feriado, semanas criticas e periodos de pico.

### 5.4. Escolha dos alvos candidatos

1. Testar pelo menos tres versoes do alvo: `nivel`, `log1p(y)` e `diff_1_7(y)`.
2. Comparar qual delas oferece melhor equilibrio entre interpretabilidade, estabilidade e desempenho preditivo.
3. Validar se a transformacao escolhida nao destruiu sinais importantes para o uso final.

### 5.5. Baselines obrigatorios

1. `Naive`: previsao igual ao ultimo valor observado.
2. `Seasonal naive`: previsao igual ao valor de `t-7`.
3. `Media movel`: previsao pela media dos ultimos `7` ou `14` dias.
4. Um baseline por regime recente, para nao comparar modelos sofisticados com uma referencia irrealista.

### 5.6. Modelos candidatos

1. `SARIMA` ou `SARIMAX`, principalmente se o alvo transformado ficar proximo de estacionario.
2. Regressao linear regularizada com lags e calendario.
3. `XGBoost`, `LightGBM` ou `Random Forest` com features tabulares.
4. Se fizer sentido depois, testar modelos mais complexos so apos os baselines fortes estarem bem estabelecidos.

### 5.7. Validacao temporal

1. Usar validacao temporal por janelas deslizantes ou expansivas.
2. Evitar splits aleatorios.
3. Avaliar desempenho global e tambem por subperiodo: `2012-2015` e `2016-2018`.
4. Checar se o modelo superestima o periodo recente por causa dos anos iniciais mais altos.

### 5.8. Analise de erro

1. Medir erro por mes, estacao e semana epidemiologica.
2. Medir erro em dias uteis versus fins de semana.
3. Medir erro em periodos de pico, ruptura e extremo.
4. Identificar em que tipo de situacao cada modelo falha mais.

### 5.9. Refinamento guiado por evidencia

1. Se o erro continuar alto em picos, incluir features de ondas e variaveis externas mais sensiveis ao outono-inverno.
2. Se o erro piorar apos `2015-08` ou na fase `2016-2018`, reforcar variaveis de regime e testar modelos segmentados.
3. Se a serie em nivel ficar muito instavel, priorizar transformacoes do alvo e reconstrucao para o nivel original.

### 5.10. Entrega final

1. Escolher um modelo principal e um baseline de referencia.
2. Documentar as features usadas e a transformacao do alvo.
3. Gerar graficos de previsao, erro e importancia de variaveis.
4. Preparar um fluxo simples de atualizacao periodica da base e reestimacao do modelo.

## 6. Conclusao executiva

- A serie possui sinal previsivel, mas esse sinal esta distribuido em varios componentes: memoria curta, ciclo semanal, ciclo anual, tendencia de queda, rupturas e extremos.
- O principal risco analitico e tratar a serie como estacionaria e homogenea, porque a EDA mostrou exatamente o contrario.
- O melhor caminho e montar uma base de previsao que combine `lags + calendario + regime + covariaveis externas`, com validacao temporal rigorosa.
- Entre os proximos testes, a combinacao de `lags semanais`, `features de calendario`, `dummies de ruptura` e um alvo transformado como `diff_1_7(y)` parece um ponto de partida especialmente promissor.
