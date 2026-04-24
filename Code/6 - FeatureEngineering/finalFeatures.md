# Features Finais do Modelo — Internações Respiratórias × Qualidade do Ar

**Dataset gerado por:** `featureEngineering.ipynb`  
**Saída:** `Data/GoldData/modelDataset.parquet`  
**Período final (após merge):** 2012–2018 (com histórico endógeno desde 2008)  
**Total de features:** 26

---

## Princípio Anti-Leakage

> **Definição:** uma feature tem *data leakage* se o seu valor em $t$ (dia D0) contém, direta ou indiretamente, informação sobre o valor alvo $y[t]$ (número de internações no próprio D0).

O modelo deve simular uma previsão realista: no momento em que se prevê $y[t]$, apenas dados de $t-1$ para trás estão disponíveis (com a exceção documentada de `no2_lag0`). A tabela abaixo resume a verificação para cada grupo de features.

| Grupo | Dado mais recente usado | Risco de leakage? |
|---|---|---|
| Lags endógenos | $y[t-1]$ a $y[t-365]$ | ✅ Nenhum |
| Janelas móveis | $y[t-1]$ a $y[t-w]$ | ✅ Nenhum |
| Calendário | data de $t$ (determinístico) | ✅ Nenhum |
| STL rolling | $y[t-1]$ a $y[t-\text{window}]$ | ✅ Nenhum (corrigido) |
| Atmosféricas (shift ≥ 1) | $x[t-s]$ a $x[t-s-w]$ | ✅ Nenhum |
| `no2_lag0` | $x_{\text{NO}_2}[t]$ | ⚠️ Premissa documentada |

---

## 1. Features Endógenas — Lags da Série de Internações

### Definição

Cada `lag_k` captura o número de internações observado $k$ dias antes de D0:

$$\text{lag\_k}[t] = y[t - k]$$

### Features criadas

| Feature | $k$ | Motivação |
|---|---|---|
| `lag_1` | 1 | Persistência imediata — o dia anterior é o preditor mais próximo |
| `lag_2` | 2 | Inercia de curto prazo |
| `lag_3` | 3 | Inercia de curto prazo |
| `lag_7` | 7 | Recorrência semanal — sinal mais forte identificado na EDA |
| `lag_14` | 14 | Memória de 2 semanas — segundo sinal semanal mais forte |
| `lag_21` | 21 | Memória de 3 semanas |
| `lag_28` | 28 | Memória de 4 semanas |
| `lag_30` | 30 | Escala mensal |
| `lag_365` | 365 | Sazonalidade anual — mesmo dia do ano anterior |

### Por que não há leakage?

O operador `.shift(k)` com $k \geq 1$ garante que o índice $t$ recebe o valor do índice $t - k$:

```python
# Exemplo para lag_1:
df_intern['lag_1'] = df_intern['num_internacoes'].shift(1)
# df_intern.iloc[t]['lag_1']  ==  df_intern.iloc[t-1]['num_internacoes']
# portanto: lag_1[t] = y[t-1]  — nunca y[t]
```

**Exemplo numérico:**

| data | num_internacoes | lag_1 | lag_7 | lag_365 |
|---|---|---|---|---|
| 2012-01-01 | 142 | 138 | 131 | 129 |
| 2012-01-02 | 138 | **142** | 127 | 135 |
| 2012-01-03 | 155 | **138** | 143 | 141 |

O valor de `lag_1` em `2012-01-02` é `142` (= internações em `2012-01-01`), nunca o valor do próprio dia `138`.

---

## 2. Features Endógenas — Janelas Móveis

### Definição

Estatísticas calculadas sobre uma janela de $w$ dias **terminando em $t-1$** (nunca em $t$). A defasagem de 1 dia é imposta com `.shift(1)` **antes** do `.rolling()`:

$$\text{rolling\_mean\_w}[t] = \frac{1}{w} \sum_{j=1}^{w} y[t - j]$$

$$\text{rolling\_std\_w}[t] = \sqrt{\frac{1}{w} \sum_{j=1}^{w} \left(y[t-j] - \overline{y}_{t-1:t-w}\right)^2}$$

### Features criadas

| Feature | $w$ | Tipo | Motivação |
|---|---|---|---|
| `rolling_mean_7` | 7 | Média | Nível local da última semana |
| `rolling_mean_14` | 14 | Média | Nível de 2 semanas |
| `rolling_mean_30` | 30 | Média | Tendência de curtíssimo prazo |
| `rolling_std_7` | 7 | Desvio padrão | Volatilidade recente da série |
| `rolling_std_30` | 30 | Desvio padrão | Volatilidade de médio prazo |

### Por que não há leakage?

```python
# Série deslocada 1 dia antes de calcular o rolling:
serie_shifted = df_intern['num_internacoes'].shift(1)

# O rolling opera sobre serie_shifted, cujo elemento t contém y[t-1]
df_intern['rolling_mean_7'] = serie_shifted.rolling(7).mean()

# Equivalente a:
#   rolling_mean_7[t] = mean(y[t-1], y[t-2], ..., y[t-7])
# O valor y[t] nunca entra na janela.
```

**Verificação da ordem das operações:**

```
Sem shift:   rolling(7).mean() sobre [..., y[t-2], y[t-1], y[t]]  ← y[t] incluído! LEAKAGE
Com shift 1: rolling(7).mean() sobre [..., y[t-3], y[t-2], y[t-1]] ← y[t] excluído ✅
```

---

## 3. Features de Calendário — Codificação Cíclica

### Motivação

Variáveis periódicas como mês (1–12) e dia da semana (0–6) têm uma descontinuidade artificial quando representadas como inteiros: a distância entre dezembro (12) e janeiro (1) deveria ser 1, não 11. A codificação cíclica resolve isso projetando cada valor em um círculo unitário.

### Definição

Para uma variável periódica $x$ com período $T$:

$$x_{\sin} = \sin\!\left(\frac{2\pi \cdot x}{T}\right) \qquad x_{\cos} = \cos\!\left(\frac{2\pi \cdot x}{T}\right)$$

Ambas as componentes são necessárias para que o modelo possa reconstruir o ângulo original sem ambiguidade.

### Features criadas

| Feature par | Variável original | Período $T$ | Faixa dos valores |
|---|---|---|---|
| `mes_sin`, `mes_cos` | mês (1–12) | 12 | $[-1, +1]$ |
| `dia_semana_sin`, `dia_semana_cos` | dia da semana (0–6) | 7 | $[-1, +1]$ |
| `semana_epi_sin`, `semana_epi_cos` | semana ISO (1–52) | 52 | $[-1, +1]$ |

**Exemplo — mês:**

| mês | mes_sin | mes_cos | Interpretação |
|---|---|---|---|
| Jan (1) | $\sin(30°) \approx 0.500$ | $\cos(30°) \approx 0.866$ | — |
| Jul (7) | $\sin(210°) \approx -0.500$ | $\cos(210°) \approx -0.866$ | oposto a jan |
| Dez (12) | $\sin(360°) = 0.000$ | $\cos(360°) = 1.000$ | contíguo a jan ✅ |

A distância euclidiana entre dezembro e janeiro no espaço `(sin, cos)` é:

$$d = \sqrt{(0 - 0.5)^2 + (1 - 0.866)^2} \approx 0.52$$

Enquanto a distância entre julho e agosto é comparável:

$$d = \sqrt{(-0.5 - (-0.866))^2 + (-0.866 - (-0.5))^2} \approx 0.52$$

Isso garante que a continuidade cíclica real seja capturada pelo modelo.

### Features categóricas de calendário

| Feature | Construção | Motivação |
|---|---|---|
| `fim_de_semana` | `dayofweek >= 5` → 0/1 | Sábado e domingo têm volumes muito menores (efeito administrativo) |
| `estacao` | mapeamento mês → 0/1/2/3 (hemisfério sul) | Inverno e primavera marcam os picos respiratórios no Rio |
| `dummy_periodo_pico_sazonal` | meses 4–7 → 0/1 | Abril a julho concentram os maiores volumes anuais da série |

### Por que não há leakage?

Todas as features de calendário são calculadas exclusivamente a partir da data de $t$, que é uma informação determinística e conhecida antecipadamente:

```python
df_intern['mes']  = df_intern['data'].dt.month    # propriedade da data
df_intern['mes_sin'] = np.sin(2 * np.pi * df_intern['mes'] / 12)
# Nenhum acesso a y[t] — apenas à data em si
```

---

## 4. Features de Sazonalidade — Decomposição STL Rolling

### Motivação

A decomposição STL (*Seasonal and Trend decomposition using Loess*) separa uma série temporal em três componentes:

$$y[t] = T[t] + S[t] + R[t]$$

onde $T$ é a tendência, $S$ é o componente sazonal e $R$ é o resíduo. Extrair o componente sazonal via STL, em vez de usar apenas o mês ou dia da semana, captura variações na **amplitude** e **forma** do ciclo anual ao longo dos anos.

### Parâmetros utilizados

| Parâmetro | Valor | Descrição |
|---|---|---|
| `period` | 365 | Periodicidade anual |
| `seasonal` | 13 | Largura LOESS sazonal (ímpar) |
| `trend` | 547 | Largura LOESS de tendência (≈ 1,5 × 365) |
| `robust` | True | Reduz influência de outliers no ajuste |
| `window` | 1 095 dias | Janela móvel (≈ 3 anos de histórico) |
| `min_history` | 730 dias | Mínimo de dados para rodar STL (≈ 2 anos) |

### Definição formal

Para cada dia $t$ (D0), o STL é ajustado sobre a janela histórica estrita:

$$\mathcal{W}(t) = \{y[\tau] : \max(0,\, t - \text{window}) \leq \tau \leq t - 1\}$$

Note que $t$ é **excluído** da janela. O ajuste resulta nas sequências $\hat{T}$, $\hat{S}$, $\hat{R}$ definidas sobre $\mathcal{W}(t)$.

### Features extraídas

| Feature | Definição | Interpretação |
|---|---|---|
| `stl365_seasonal` | $\hat{S}[\text{último ponto de } \mathcal{W}(t)]$ | Pulso sazonal em $t-1$ — proxy do padrão cíclico esperado em D0 |
| `stl365_resid_vol30` | $\text{std}\!\left(\hat{R}[\text{últimos 30 pontos de } \mathcal{W}(t)]\right)$ | Instabilidade residual recente — alta quando há picos ou anomalias |
| `stl365_season_amp` | $\max(\hat{S}_{\text{últ. 365}}) - \min(\hat{S}_{\text{últ. 365}})$ | Amplitude do ciclo anual — mede a intensidade sazonal atual |

### Por que não há leakage? (ponto crítico)

O trecho central do loop STL é:

```python
for i in range(n):
    start = max(0, i - window)
    seg = series.iloc[start : i]   # <-- 'i' excluído (Python slicing: [start, i))
    #                         ^
    #               series.iloc[start : i+1] seria leakage!
    #               series.iloc[start : i  ] é correto ✅
    
    if len(seg) < min_history:
        continue
    
    result = STL(seg, ...).fit()
    stl_seasonal[i] = result.seasonal.iloc[-1]   # último ponto = t-1
```

**Por que `iloc[start:i+1]` seria leakage?**

Em Python, `series.iloc[a:b]` inclui os índices `a, a+1, ..., b-1`. Portanto:

- `series.iloc[start : i]` → janela $\{y[start], \ldots, y[i-1]\}$ = $\{y[t-\text{window}], \ldots, y[t-1]\}$ ✅
- `series.iloc[start : i+1]` → janela $\{y[start], \ldots, y[i]\}$ = inclui $y[t]$ ❌

O componente sazonal do STL é sensível ao último valor da série ajustada: incluir $y[t]$ (o alvo) no ajuste contamina `stl365_seasonal[t]` com informação do próprio alvo — um caso típico de leakage indireto.

**Verificação numérica da janela:**

```
i = 1000 (= dia 2012-09-27 na série completa desde 2008)
start = max(0, 1000 - 1095) = 0
seg = series.iloc[0:1000]   # índices 0..999 → y[2008-01-01] a y[2012-09-26]
                             # y[2012-09-27] (i=1000) não entra ✅
stl365_seasonal[1000] = resultado STL ajustado sobre [2008-01-01, 2012-09-26]
                         → componente sazonal no último dia (2012-09-26) = proxy de t-1
```

---

## 5. Features Atmosféricas

### Estrutura geral

As features atmosféricas são construídas sobre `df_air` (qualidade do ar, 2012–2018) com a fórmula geral:

$$\text{poll\_ma\_wd\_shift\_sd}[t] = \frac{1}{w} \sum_{j=s}^{s+w-1} x_{\text{poll}}[t - j]$$

onde $s$ é o deslocamento (*shift*) em dias e $w$ é a largura da janela (*window*). Isso garante que a janela cubra **$[t-s, \, t-s-w+1]$** — toda no passado.

### Features criadas

| Feature | Poluente | $s$ (shift) | $w$ (janela) | Janela de dados usada |
|---|---|---|---|---|
| `o3_ma_120d_shift_1d` | O₃ | 1 | 120 | $[t-1,\; t-120]$ |
| `no_ma_30d_shift_1d` | NO | 1 | 30 | $[t-1,\; t-30]$ |
| `co_ma_120d_shift_1d` | CO | 1 | 120 | $[t-1,\; t-120]$ |
| `so2_ma_150d_shift_21d` | SO₂ | 21 | 150 | $[t-21,\; t-170]$ |
| `nox_ma_21d_shift_1d` | NOₓ | 1 | 21 | $[t-1,\; t-21]$ |
| `pm2_5_ma_30d_shift_1d` | PM₂.₅ | 1 | 30 | $[t-1,\; t-30]$ |
| `temp_ma_14d_shift_1d` | Temperatura | 1 | 14 | $[t-1,\; t-14]$ |
| `ur_ma_60d_shift_1d` | Umidade relativa | 1 | 60 | $[t-1,\; t-60]$ |

### Implementação e verificação de anti-leakage

```python
# Padrão: shift ANTES do rolling — o shift garante que o elemento [t] recebe x[t-1]
df_air['o3_ma_120d_shift_1d'] = df_air['o3'].shift(1).rolling(120).mean()

# Equivalência matemática:
#   o3.shift(1)[t] = o3[t-1]
#   .rolling(120).mean()[t] = mean(o3[t-1], o3[t-2], ..., o3[t-120])
#   → janela [t-1, t-120] — todo no passado ✅

# SO2 tem shift maior (21 dias): captura efeito de acumulação com latência
df_air['so2_ma_150d_shift_21d'] = df_air['so2'].shift(21).rolling(150).mean()
#   → janela [t-21, t-170] — começa 21 dias atrás, retrocede 150 dias ✅
```

**Exemplo numérico — `no_ma_30d_shift_1d` para `t = 2014-06-01`:**

```
dados usados: NO de 2014-05-02 até 2014-05-31  (30 dias, termina em t-1)
valor da feature = média desses 30 dias
y[2014-06-01] não é usado em nenhum momento ✅
```

### `no2_lag0` — Exceção documentada

```python
NO2_USES_D0 = True

if NO2_USES_D0:
    df_air['no2_lag0'] = df_air['no2'].copy()    # usa x[t] diretamente
else:
    df_air['no2_lag0'] = df_air['no2'].shift(1)  # fallback sem leakage
```

Esta é a **única feature** que utiliza o valor do próprio dia D0. A justificativa epidemiológica é que, na análise exploratória, NO₂ no dia D0 foi o melhor representante para `no2` (acima de qualquer média móvel defasada).

**Essa premissa é válida se e somente se:**

1. A leitura do sensor de NO₂ está disponível **antes** do momento da previsão;
2. A previsão é feita no **final do dia** (após a leitura consolidada);
3. O sistema operacional garante acesso à telemetria em tempo real.

**Se a previsão for feita no início do dia** (prever D0 antes de qualquer leitura), `NO2_USES_D0` deve ser definido como `False`, e o modelo usará `no2.shift(1)` = valor de D0 - 1.

---

## 6. Resumo Consolidado

### Todas as 26 features

| # | Feature | Grupo | Dado mais recente | Leakage? |
|---|---|---|---|---|
| 1 | `lag_1` | Lag endógeno | $y[t-1]$ | ✅ Não |
| 2 | `lag_2` | Lag endógeno | $y[t-2]$ | ✅ Não |
| 3 | `lag_3` | Lag endógeno | $y[t-3]$ | ✅ Não |
| 4 | `lag_7` | Lag endógeno | $y[t-7]$ | ✅ Não |
| 5 | `lag_14` | Lag endógeno | $y[t-14]$ | ✅ Não |
| 6 | `lag_21` | Lag endógeno | $y[t-21]$ | ✅ Não |
| 7 | `lag_28` | Lag endógeno | $y[t-28]$ | ✅ Não |
| 8 | `lag_30` | Lag endógeno | $y[t-30]$ | ✅ Não |
| 9 | `lag_365` | Lag endógeno | $y[t-365]$ | ✅ Não |
| 10 | `rolling_mean_7` | Janela móvel | $y[t-1]$ a $y[t-7]$ | ✅ Não |
| 11 | `rolling_mean_14` | Janela móvel | $y[t-1]$ a $y[t-14]$ | ✅ Não |
| 12 | `rolling_mean_30` | Janela móvel | $y[t-1]$ a $y[t-30]$ | ✅ Não |
| 13 | `rolling_std_7` | Janela móvel | $y[t-1]$ a $y[t-7]$ | ✅ Não |
| 14 | `rolling_std_30` | Janela móvel | $y[t-1]$ a $y[t-30]$ | ✅ Não |
| 15 | `mes_sin` | Calendário cíclico | data de $t$ | ✅ Não |
| 16 | `mes_cos` | Calendário cíclico | data de $t$ | ✅ Não |
| 17 | `dia_semana_sin` | Calendário cíclico | data de $t$ | ✅ Não |
| 18 | `dia_semana_cos` | Calendário cíclico | data de $t$ | ✅ Não |
| 19 | `semana_epi_sin` | Calendário cíclico | data de $t$ | ✅ Não |
| 20 | `semana_epi_cos` | Calendário cíclico | data de $t$ | ✅ Não |
| 21 | `fim_de_semana` | Calendário categórico | data de $t$ | ✅ Não |
| 22 | `estacao` | Calendário categórico | data de $t$ | ✅ Não |
| 23 | `dummy_periodo_pico_sazonal` | Calendário categórico | data de $t$ | ✅ Não |
| 24 | `stl365_seasonal` | STL rolling | $y[t-1]$ (último de $\mathcal{W}(t)$) | ✅ Não |
| 25 | `stl365_resid_vol30` | STL rolling | $y[t-1]$ a $y[t-30]$ | ✅ Não |
| 26 | `stl365_season_amp` | STL rolling | $y[t-1]$ a $y[t-365]$ | ✅ Não |
| 27 | `o3_ma_120d_shift_1d` | Atmosférica | $x_{\text{O}_3}[t-1]$ a $x[t-120]$ | ✅ Não |
| 28 | `no_ma_30d_shift_1d` | Atmosférica | $x_{\text{NO}}[t-1]$ a $x[t-30]$ | ✅ Não |
| 29 | `co_ma_120d_shift_1d` | Atmosférica | $x_{\text{CO}}[t-1]$ a $x[t-120]$ | ✅ Não |
| 30 | `so2_ma_150d_shift_21d` | Atmosférica | $x_{\text{SO}_2}[t-21]$ a $x[t-170]$ | ✅ Não |
| 31 | `nox_ma_21d_shift_1d` | Atmosférica | $x_{\text{NO}_x}[t-1]$ a $x[t-21]$ | ✅ Não |
| 32 | `no2_lag0` | Atmosférica | $x_{\text{NO}_2}[t]$ | ⚠️ Premissa |
| 33 | `pm2_5_ma_30d_shift_1d` | Atmosférica | $x_{\text{PM}_{2.5}}[t-1]$ a $x[t-30]$ | ✅ Não |
| 34 | `temp_ma_14d_shift_1d` | Atmosférica | $x_{\text{temp}}[t-1]$ a $x[t-14]$ | ✅ Não |
| 35 | `ur_ma_60d_shift_1d` | Atmosférica | $x_{\text{UR}}[t-1]$ a $x[t-60]$ | ✅ Não |

> **Nota:** o dataset final tem 26 features — `estacao` e `dummy_periodo_pico_sazonal` são incluídas como inteiros simples (0/1 e 0–3), mas as 6 features cíclicas substituem as versões inteiras de `mes`, `dia_semana` e `semana_epidemiologica`, que não entram no dataset final.

### Linha do tempo de dados usados por cada feature em D0

```
         t-365  t-170  t-120  t-60  t-30  t-21  t-14  t-7  t-1   t
           |      |      |      |     |     |     |    |    |     |
lag_365    ●                                                        (y em t-365)
lag_30                              ●                               (y em t-30)
lag_7                                              ●                (y em t-7)
lag_1                                                    ●          (y em t-1)
roll_7                                             ●----●           (média y[t-7..t-1])
roll_30                             ●-----------●                   (média y[t-30..t-1])
stl_seasonal     ●==================●                               (STL sobre 3 anos → t-1)
so2              ●=================●                                (shift 21d, janela 150d)
o3, co                  ●==========●                               (shift 1d, janela 120d)
ur                            ●====●                               (shift 1d, janela 60d)
temp                                              ●-●              (shift 1d, janela 14d)
no2_lag0                                                       ●   (t mesmo — premissa ⚠️)
calendário                                                     ●   (data de t — sem y[t])
```

---

## 7. Verificação Empírica no Notebook

A célula de consistência (`featureEngineering.ipynb`, seção "Verificações de consistência") valida automaticamente:

```python
# Anti-leakage check 1: lag_1 deve ser correlacionado com target, mas não idêntico
corr_lag1 = df_final['target'].corr(df_final['lag_1'])
fracao_iguais = (df_final['target'] == df_final['lag_1']).mean()

# Resultado esperado:
#   corr_lag1 > 0.8  → lag_1 é informativo
#   fracao_iguais ≈ 0  → lag_1 != target (não é o mesmo valor)

# Anti-leakage check 2: rolling_mean_7 deve ter correlação moderada
corr_rm7 = df_final['target'].corr(df_final['rolling_mean_7'])
# Resultado esperado: moderada (< corr_lag1), pois é uma média suavizada
```

Se `fracao_iguais` fosse próximo de 1, significaria que `lag_1 == target` — o que só aconteceria se o shift não tivesse sido aplicado corretamente (leakage). Na prática, a série tem variação diária suficiente para que esse valor seja próximo de zero.
