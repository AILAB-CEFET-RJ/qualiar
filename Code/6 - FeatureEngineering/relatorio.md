# Relatorio de Modelagem — Random Forest para Previsao de Internacoes Respiratorias

## 1. Visao Geral

Este relatorio consolida os principais achados e conclusoes da pipeline de modelagem preditiva com Random Forest Regressor para prever o numero diario de internacoes por doencas respiratorias no Rio de Janeiro (D0), utilizando features endogenas da serie, variaveis de calendario e variaveis atmosfericas.

- **Modelo:** Random Forest Regressor
- **Features:** 29
- **Periodo total:** 2012-12-31 a 2018-12-31 (2192 dias)
- **Divisao temporal:**
  - Treino: 2012-12-31 a 2016-12-31 (1462 dias, ~67%)
  - Validacao: 2017-01-01 a 2017-12-31 (365 dias, ~17%)
  - Teste: 2018-01-01 a 2018-12-31 (365 dias, ~17%)

---

## 2. Comparacao de Estrategias de Transformacao do Alvo

Foram avaliadas tres estrategias de tratamento da variavel alvo na validacao:

| Estrategia | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| A: Alvo original | 50.91 | 64.65 | 0.5044 | 21.85% |
| **B: log1p** | **48.30** | **62.19** | **0.5414** | **21.09%** |
| C: log1p + detrend | 62.21 | 81.13 | 0.2195 | 27.92% |

### Conclusao

A **Estrategia B (log1p)** foi a melhor em todas as metricas. A transformacao logaritmica ajuda a comprimir a cauda direita da distribuicao de internacoes, melhorando a capacidade do modelo de lidar com a assimetria da serie.

A **Estrategia C (log1p + detrend)** teve o pior desempenho. A tendencia linear estimada no treino (slope = -0.0004) era muito fraca, e a subtracao dessa tendencia parece ter removido sinal util em vez de facilitar a modelagem. Isso sugere que a tendencia da serie ja e capturada adequadamente pelas features endogenas (lags e medias moveis) sem necessidade de transformacao explicita.

---

## 3. Desempenho do Random Forest vs Baselines

### Validacao

| Modelo | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| Persistencia (lag_1) | 73.72 | 93.20 | -0.03 | 31.70% |
| Media Movel 7d | 57.10 | 71.35 | 0.40 | 25.01% |
| Lag 7 (mesmo dia semana) | 61.67 | 78.01 | 0.28 | 27.15% |
| RF Default (log1p) | 48.30 | 62.19 | 0.54 | 21.09% |
| **RF Tuned (log1p)** | **47.59** | **61.53** | **0.55** | **20.75%** |

### Teste (avaliacao final)

| Modelo | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| Persistencia (lag_1) | 73.88 | 100.65 | 0.12 | 28.62% |
| Media Movel 7d | 61.18 | 78.34 | 0.47 | 24.14% |
| Lag 7 (mesmo dia semana) | 67.88 | 90.87 | 0.28 | 26.83% |
| **RF Final** | **50.82** | **68.85** | **0.59** | **19.76%** |

### Conclusao

O Random Forest superou todos os baselines de forma consistente tanto na validacao quanto no teste:

- **MAE:** reducao de ~31% em relacao a persistencia e ~17% em relacao a media movel 7d.
- **R²:** o RF explica ~59% da variancia no teste, contra ~47% da media movel e ~12% da persistencia.
- **sMAPE:** erro percentual simetrico de ~20%, melhor que todos os baselines.

O ganho do tuning de hiperparametros sobre o modelo default foi modesto (~1.5% de melhoria no MAE na validacao), indicando que o Random Forest com parametros padrao ja captura bem a estrutura do problema.

---

## 4. Hiperparametros Finais

| Hiperparametro | Valor |
|---|---|
| n_estimators | 459 |
| max_depth | 40 |
| max_features | 0.7 |
| min_samples_leaf | 3 |
| min_samples_split | 13 |

O modelo final foi retreinado com treino + validacao (1827 dias) e avaliado uma unica vez no teste.

---

## 5. Diagnostico do Modelo

### Serie temporal real vs previsto

O modelo acompanha razoavelmente bem a dinamica geral da serie no periodo de teste. As previsoes capturam os movimentos de subida e descida, mas subestimam sistematicamente os picos mais extremos, especialmente no periodo de maior carga respiratoria (abril-julho de 2018).

### Residuos

- Os residuos estao aproximadamente centrados em zero, sem tendencia clara ao longo do tempo.
- O histograma dos residuos mostra distribuicao levemente assimetrica a direita, confirmando a tendencia de subestimacao nos picos.
- Nao ha evidencia de degradacao progressiva do modelo ao longo do ano de teste.

### Erro por mes

O erro absoluto medio (MAE) varia significativamente ao longo dos meses:

- **Menor erro:** Janeiro (~30 internacoes de MAE) — periodo de verao com baixa carga respiratoria.
- **Maior erro:** Abril a Julho (~60-65 internacoes de MAE) — periodo de pico sazonal de internacoes.

Isso e esperado: durante o pico, a serie e mais volatil e os valores absolutos sao mais altos, gerando erros absolutos maiores.

### Erro por dia da semana

O MAE por dia da semana e relativamente uniforme (entre ~44 e ~60), com leve elevacao nas segundas-feiras. Nao ha um padrao semanal forte de erro.

---

## 6. Importancia das Features

### Por impureza (MDI)

As features mais importantes por reducao de impureza no Random Forest sao:

| Posicao | Feature | MDI |
|---|---|---|
| 1 | lag_7 | 0.2969 |
| 2 | rolling_mean_7 | 0.2604 |
| 3 | rolling_mean_14 | 0.1298 |
| 4 | lag_14 | 0.0485 |
| 5 | dia_semana | 0.0369 |
| 6 | fim_de_semana | 0.0318 |
| 7 | rolling_std_30 | 0.0198 |
| 8 | rolling_mean_30 | 0.0192 |
| 9 | lag_1 | 0.0148 |
| 10 | lag_365 | 0.0122 |

**Conclusao:** O modelo depende fortemente da memoria semanal (lag_7) e do nivel recente da serie (rolling_mean_7 e rolling_mean_14). Juntas, as tres primeiras features concentram quase 70% da importancia total. O efeito calendario (dia_semana e fim_de_semana) tambem e relevante.

### Por permutacao (Permutation Importance)

| Posicao | Feature | Permutation |
|---|---|---|
| 1 | so2_ma_150d_shift_21d | +0.0041 |
| 2 | lag_3 | +0.0033 |
| 3 | no2_lag0 | +0.0031 |
| 4 | lag_28 | +0.0027 |
| 5 | lag_14 | +0.0020 |
| 6 | rolling_mean_30 | +0.0017 |
| 7 | rolling_std_7 | +0.0017 |

A permutation importance mostra um cenario diferente do MDI. As variaveis atmosfericas (SO2 e NO2) aparecem no topo, sugerindo que, embora contribuam com pouca importancia por impureza, sao as features com informacao mais *unica* — isto e, menos redundante com outras variaveis.

### Importancia por grupo

| Grupo | MDI | Permutation |
|---|---|---|
| Medias/Desvios moveis | 0.4364 | -0.0254 |
| Lags da serie | 0.4157 | -0.0115 |
| Calendario/Sazonalidade | 0.0759 | -0.0013 |
| Poluentes | 0.0586 | +0.0022 |
| Temperatura | 0.0068 | -0.0093 |
| Umidade | 0.0067 | +0.0008 |

### Interpretacao das importancias negativas na permutacao

Um resultado relevante e que a maioria das features endogenas (lags e medias moveis) apresenta permutation importance negativa. Isso **nao** significa que essas features sao inuteis — pelo contrario, sao as mais usadas pelo modelo (MDI > 0.85 somadas).

O fenomeno ocorre porque essas features sao **altamente correlacionadas entre si**. Quando uma delas (e.g., rolling_mean_14) e permutada, o modelo consegue compensar usando rolling_mean_7, lag_7 ou lag_14, que carregam informacao similar. Permutar uma feature redundante pode ate reduzir ruido, resultando em importancia negativa.

Ja os **poluentes** (SO2, NO2), embora com MDI baixo (~6%), apresentam permutation importance positiva. Isso indica que eles trazem informacao complementar que nenhuma outra feature do modelo consegue suprir.

---

## 7. Principais Achados

1. **A transformacao log1p no alvo melhora o desempenho.** Comprimir a escala da variavel alvo ajuda o Random Forest a lidar com a assimetria da distribuicao de internacoes. O detrend explicito nao agregou valor.

2. **O Random Forest supera todos os baselines simples**, com MAE de ~51 internacoes no teste, contra ~61 da media movel 7d e ~74 da persistencia.

3. **O modelo e fortemente guiado pela memoria recente da serie.** As tres features mais importantes por MDI (lag_7, rolling_mean_7, rolling_mean_14) concentram ~69% da importancia, confirmando que a recorrencia semanal e o padrao mais forte da serie.

4. **Os poluentes trazem informacao unica e complementar.** Apesar de baixo MDI, SO2 (media movel 150d, shift 21d) e NO2 (valor no dia) sao as features com maior permutation importance positiva. Isso corrobora os achados da EDA sobre a relevancia dos poluentes como covariaveis.

5. **O modelo tem mais dificuldade no periodo de pico respiratorio (abril-julho).** Os erros sao quase o dobro dos meses de verao, o que e coerente com a maior volatilidade e valores mais altos da serie nesse periodo.

6. **O modelo subestima picos extremos.** O Random Forest, por ser baseado em medias de arvores, tende a suavizar previsoes e tem dificuldade natural em prever valores muito acima ou abaixo da distribuicao do treino.

7. **O tuning de hiperparametros trouxe ganho marginal.** A melhoria de ~1.5% no MAE sugere que o modelo ja era razoavelmente bem ajustado com parametros padrao.

---

## 8. Limitacoes e Proximos Passos

### Limitacoes

- **Subestimacao de picos:** limitacao inerente ao Random Forest, que preve medias de folhas. Abordagens como Gradient Boosting ou modelos quantilicos podem tratar melhor os extremos.
- **R² de 0.59:** o modelo explica pouco mais da metade da variancia, indicando que fatores nao capturados (surtos, feriados prolongados, eventos epidemiologicos) tambem influenciam a serie.
- **Redundancia entre features endogenas:** a alta multicolinearidade entre lags e medias moveis dificulta a interpretacao individual de cada feature pelo modelo.

### Proximos passos sugeridos

- Testar modelos baseados em boosting (XGBoost, LightGBM) para melhor captura de picos.
- Avaliar abordagens de selecao de features para reduzir redundancia.
- Incluir features secundarias (diff, rolling_sum, dummies de regime) conforme featureDefinition.md.
- Considerar modelos hibridos que combinem componentes autorregressivos com covariaveis atmosfericas.
- Avaliar intervalos de predicao (prediction intervals) para quantificar incerteza.
