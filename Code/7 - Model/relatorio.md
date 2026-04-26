# Relatorio de Modelagem — Random Forest para Previsao de Internacoes Respiratorias

## 1. Visao Geral

Este relatorio consolida os principais achados e conclusoes da pipeline de modelagem preditiva com Random Forest Regressor para prever o numero diario de internacoes por doencas respiratorias no Rio de Janeiro (D0), utilizando features endogenas da serie, variaveis de calendario e variaveis atmosfericas.

- **Modelo:** Random Forest Regressor
- **Features:** 38
- **Periodo total:** 2012-06-19 a 2018-12-31
- **Divisao temporal:**
  - Treino: 2012-06-19 a 2016-12-31 (~70%)
  - Validacao: 2017-01-01 a 2017-12-31 (365 dias, ~15%)
  - Teste: 2018-01-01 a 2018-12-31 (365 dias, ~15%)

---

## 2. Comparacao de Estrategias de Transformacao do Alvo

Foram avaliadas tres estrategias de tratamento da variavel alvo:

| Estrategia | Descricao |
|---|---|
| **A** | Alvo original |
| **B** | `log1p(y)` |
| **C** | `log1p(y)` + detrend (tendencia linear estimada no treino) |

### Resultado no Teste — Modelos Base 

| Estrategia | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| **B: log1p** | **6.33** | **8.59** | **0.5827** | **19.74%** |
| C: log1p + detrend | 8.26 | 10.96 | 0.3213 | 26.72% |

### Conclusao

A **Estrategia B (log1p)** e superior em todas as metricas. A transformacao logaritmica comprime a cauda direita da distribuicao de internacoes, melhorando a capacidade do modelo de lidar com a assimetria da serie.

A **Estrategia C (log1p + detrend)** tem desempenho inferior na forma base, ficando abaixo dos baselines de media movel. A tendencia linear estimada no treino (slope = -0.000160, intercept = 3.5999) e fraca, e sua subtracao remove sinal util sem contrapartida. A tendencia da serie ja e capturada pelas features endogenas (lags, medias moveis e STL), tornando o detrend explicito redundante. A correcao via MOS melhora C significativamente (ver Secao 5).

---

## 3. Desempenho do Random Forest vs Baselines

### Teste (avaliacao final — escala original)

| Modelo | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| Persistencia (lag_1) | 9.27 | 12.61 | 0.1015 | 28.54% |
| Lag 7 (mesmo dia semana) | 8.50 | 11.38 | 0.2686 | 26.74% |
| RF Final C (Log1p+Detrend) | 8.26 | 10.96 | 0.3213 | 26.72% |
| Media Movel 7d | 7.69 | 9.82 | 0.4546 | 24.12% |
| **RF Final B (Log1p)** | **6.33** | **8.59** | **0.5827** | **19.74%** |

### Conclusao

O **Modelo B** supera todos os baselines e a Estrategia C:

- **MAE:** reducao de ~32% em relacao a persistencia e ~18% em relacao a media movel 7d.
- **R²:** o RF-B explica ~58% da variancia no teste, contra ~45% da media movel 7d e ~10% da persistencia.
- **sMAPE:** erro percentual simetrico de ~20%, o menor entre todos os modelos avaliados.

A Estrategia C (base) fica aquem da media movel 7d. Com pos-processamento MOS, melhora para MAE = 7.41 e supera os baselines de persistencia e lag-7 (ver Secao 5).

---

## 4. Hiperparametros Finais

Os hiperparametros foram otimizados via **Optuna (TPE Bayesiano)** com walk-forward cross-validation (3 folds, gap=7, test_size=365).

### Estrategia B (modelo final recomendado)

| Hiperparametro | Valor |
|---|---|
| n_estimators | 280 |
| max_depth | 30 |
| max_features | 0.5 |
| min_samples_leaf | 5 |
| min_samples_split | 12 |

### Estrategia C

| Hiperparametro | Valor |
|---|---|
| n_estimators | 661 |
| max_depth | 30 |
| max_features | 0.5 |
| min_samples_leaf | 14 |
| min_samples_split | 18 |

Ambos os modelos foram retreinados com treino + validacao (2012-06-19 a 2017-12-31) e avaliados uma unica vez no teste (2018).

---
## 5. Diagnostico do Modelo (Estrategia B)

### Serie temporal real vs previsto

O modelo B acompanha razoavelmente bem a dinamica geral da serie no periodo de teste. As previsoes capturam os movimentos de subida e descida, mas tendem a subestimar os picos mais extremos, especialmente no periodo de maior carga respiratoria (abril-julho de 2018).

### Residuos

- Os residuos estao aproximadamente centrados em zero, sem tendencia clara ao longo do tempo.
- O histograma dos residuos mostra distribuicao levemente assimetrica a direita, confirmando a tendencia de subestimacao nos picos.
- Nao ha evidencia de degradacao progressiva do modelo ao longo do ano de teste.

### Erro por mes

O erro absoluto medio (MAE) varia ao longo dos meses:

- **Menor erro:** Janeiro — periodo de verao com baixa carga respiratoria e serie mais estavel.
- **Maior erro:** Abril a Julho — periodo de pico sazonal de internacoes, com maior volatilidade e valores absolutos mais altos.

### Erro por dia da semana

O MAE por dia da semana e relativamente uniforme, com leve elevacao nas segundas-feiras, possivelmente associada ao efeito de acumulacao de internacoes do fim de semana.

---

## 6. Importancia das Features — Estrategia B

### Por impureza (MDI) — Top 10

| Posicao | Feature | MDI |
|---|---|---|
| 1 | lag_7 | 0.2914 |
| 2 | rolling_mean_7 | 0.1535 |
| 3 | rolling_mean_14 | 0.1408 |
| 4 | lag_14 | 0.0803 |
| 5 | dia_semana_sin | 0.0419 |
| 6 | rolling_mean_30 | 0.0346 |
| 7 | fim_de_semana | 0.0328 |
| 8 | rolling_max_7 | 0.0240 |
| 9 | lag_21 | 0.0131 |
| 10 | pm2_5_ma_30d_shift_1d | 0.0124 |

**Conclusao:** O modelo B depende fortemente da memoria semanal (lag_7) e do nivel recente da serie (rolling_mean_7, rolling_mean_14, rolling_mean_30). As quatro primeiras features concentram ~65% da importancia total. O `rolling_max_7` aparece entre os top 10 (feature adicionada nesta versao), indicando que o valor maximo recente captura informacao adicional relevante.

### Por permutacao (Permutation Importance) — Top positivos (9 de 38)

| Posicao | Feature | Permutation |
|---|---|---|
| 1 | lag_3 | +0.002120 |
| 2 | dias_desde_pico | +0.001458 |
| 3 | diff_7 | +0.001169 |
| 4 | lag_21 | +0.000918 |
| 5 | lag_28 | +0.000646 |
| 6 | no2_lag0 | +0.000405 |
| 7 | rolling_mean_14 | +0.000263 |
| 8 | rolling_max_7 | +0.000152 |
| 9 | accel_ratio | +0.000088 |

As novas features de "momentum" (`dias_desde_pico`, `diff_7`, `accel_ratio`) e o `lag_3` possuem informacao *unica* nao coberta pelas demais. Em particular, `dias_desde_pico` — que mede quantos dias se passaram desde o ultimo pico sazonal — surge como a segunda feature mais relevante na permutacao, evidenciando que a posicao relativa ao pico sazonal tem valor preditivo independente dos lags simples. O `no2_lag0` permanece como a unica covariavel atmosferica com permutation importance positiva significativa.

### Importancia por grupo — Estrategia B (MDI acumulado)

| Grupo | MDI |
|---|---|
| Lags da serie | 0.4277 |
| Medias/Desvios moveis | 0.3698 |
| Calendario ciclico | 0.0612 |
| Poluentes | 0.0591 |
| Calendario/Sazonalidade | 0.0339 |
| Outros (momentum) | 0.0198 |
| STL Sazonalidade | 0.0174 |
| Temperatura | 0.0061 |
| Umidade | 0.0051 |

---

## 7. Importancia das Features — Estrategia C

### Por permutacao (Permutation Importance) — Top positivos (6 de 38)

| Posicao | Feature | Permutation |
|---|---|---|
| 1 | lag_3 | +0.000780 |
| 2 | lag_21 | +0.000572 |
| 3 | diff_7 | +0.000441 |
| 4 | mes_cos | +0.000189 |
| 5 | stl365_resid_vol30 | +0.000170 |
| 6 | ur_ma_60d_shift_1d | +0.000032 |

Na Estrategia C, apenas 6 features tem permutation importance positiva (vs 9 em B), e os valores sao menores. O modelo passa a depender mais de sinais sazonais (`mes_cos`, `stl365_resid_vol30`) e menos de momentum de curto prazo, consistente com a remocao da tendencia — o modelo busca reconstruir o nivel da serie via ciclos de longo prazo. O `dummy_periodo_pico_sazonal`, proeminente na versao anterior da Estrategia C, foi substituido por `stl365_resid_vol30` (volatilidade do residuo STL) como sinal sazonal relevante.

---

## 8. Interpretacao das Importancias Negativas na Permutacao

Um resultado recorrente em ambas as estrategias e que diversas features endogenas (lags e medias moveis) apresentam permutation importance negativa. Isso **nao** significa que essas features sao inuteis — pelo contrario, sao as mais utilizadas pelo modelo (MDI > 0.80 somadas na Estrategia B).

O fenomeno ocorre porque essas features sao **altamente correlacionadas entre si**. Quando uma delas (e.g., rolling_mean_14) e permutada aleatoriamente, o modelo consegue compensar parcialmente usando rolling_mean_7, lag_7 ou lag_14, que carregam informacao similar. Permutar uma feature redundante pode ate reduzir ruido, resultando em importancia negativa.

Isso nao e evidencia de leakage nem de problema de modelagem, mas de multicolinearidade estrutural entre lags de uma serie autocorrelacionada. A selecao de features baseada em limiar de permutacao deve ser usada com cautela nesse contexto (ver Secao 6).

---

## 9. Principais Achados

1. **A transformacao log1p no alvo melhora o desempenho.** Comprimir a escala da variavel alvo ajuda o Random Forest a lidar com a assimetria da distribuicao de internacoes. O detrend explicito (Estrategia C) nao agrega valor na forma base.

2. **O Modelo B supera todos os baselines simples**, com MAE de 6.33 internacoes no teste, contra 7.69 da media movel 7d e 9.27 da persistencia. Reducao de ~32% em relacao a persistencia.

3. **O modelo e fortemente guiado pela memoria recente da serie.** As quatro features de maior MDI (lag_7, rolling_mean_7, rolling_mean_14, lag_14) concentram ~65% da importancia total.

4. **As novas features de momentum (diff_7, dias_desde_pico, accel_ratio, rolling_max_7) agregam valor unico.** Aparecem entre os top 9 na permutation importance do modelo B, indicando que a taxa de variacao e a posicao relativa ao pico sazonal contem informacao nao coberta pelos lags simples.

5. **O `no2_lag0` permanece como a covariavel atmosferica com sinal mais unico.** E a unica feature de qualidade do ar com permutation importance positiva significativa no Modelo B, corroborando os achados da EDA.

6. **A correcao MOS melhora a Estrategia C significativamente** (MAE 8.26 → 7.41, reducao de ~10%), mas piora a Estrategia B (6.33 → 6.98). O modelo C tem vies de previsao mais pronunciado que o MOS corrige parcialmente; o modelo B ja esta bem calibrado.

7. **A calibracao por multiplicadores sazonais nao agrega valor.** Variacao de fracao de centesimo de MAE em ambas as estrategias, indicando que o modelo ja captura a sazonalidade pelas features de calendario e STL.

8. **A selecao de features baseada em permutation importance positiva nao melhora o modelo.** O conjunto de 12 features selecionadas tem desempenho inferior ao modelo completo com 38 features: as features redundantes, apesar de individualmente substituiveis, contribuem em conjunto.

9. **O modelo tem mais dificuldade no periodo de pico respiratorio (abril-julho).** Os erros sao maiores nesse periodo, coerente com a maior volatilidade e valores absolutos mais altos da serie.

10. **O modelo subestima picos extremos.** O Random Forest, por ser baseado em medias de arvores, tende a suavizar previsoes e tem dificuldade com valores muito acima da distribuicao do treino.

---

## 10. Limitacoes e Proximos Passos

### Limitacoes

- **Subestimacao de picos:** limitacao inerente ao Random Forest, que preve medias de folhas. Abordagens como Gradient Boosting ou modelos quantilicos podem tratar melhor os extremos.
- **R² de ~0.58:** o modelo explica pouco mais da metade da variancia, indicando que fatores nao capturados (surtos, feriados prolongados, eventos epidemiologicos) tambem influenciam a serie.
- **Multicolinearidade entre features endogenas:** dificulta a interpretacao individual de cada feature pela permutation importance e limita a utilidade de selecao por esse criterio.
- **`no2_lag0` com premissa operacional:** essa feature assume disponibilidade da medicao de NO2 no mesmo dia da previsao, o que pode nao valer em todos os cenarios de uso.
- **MOS nao e robusto para B:** a correcao linear piora o modelo B ja bem calibrado. Para uso em producao, o RF B sem pos-processamento e a opcao mais segura.

### Proximos passos sugeridos

- Testar modelos baseados em boosting (XGBoost, LightGBM) para melhor captura de picos e comparar com o RF B atual.
- Avaliar correcao MOS especifica por periodo sazonal (MOS mensal ou por estacao) para verificar se o vies e heterogeneo ao longo do ano.
- Considerar modelos quantilicos ou de ensemble para gerar intervalos de predicao e quantificar incerteza.
- Explorar lags de NO2 adicionais (lag-1 a lag-7) em substituicao ao no2_lag0, removendo a premissa de disponibilidade no mesmo dia.
- Avaliar modelos hibridos que combinem componentes autorregressivos com covariaveis atmosfericas para melhor captura de picos extremos.
