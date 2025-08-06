## Abstract

Air pollution is one of the main environmental and public health challenges in urban areas, negatively impacting the lives of thousands of Brazilians. This project aims to analyze the correlation between air quality and hospitalizations in the Brazilian Unified Health System (SUS), with the objective of predicting hospital admissions due to respiratory diseases in regions of Rio de Janeiro.

Air quality data were sourced from the MonitorAr program, while hospitalization records were obtained from the SUS Hospital Information System (SIH-SUS), covering the period from 2012 to 2024. The methodology includes preprocessing of both datasets, statistical analysis of environmental and health indicators, and the application of machine learning algorithms to develop forecasting models.

The expected outcome is that the developed models will contribute to identifying patterns and trends that precede hospitalization peaks, thus supporting decision-making in hospital resource management and public policy development to mitigate the health impacts of air pollution.


## Motivation and Context

Air pollution is a major health issue, especially in urban areas of developing countries. In Brazil, thousands of premature deaths and hospitalizations are associated with air pollutants. Despite having robust public health and environmental data systems like SIH-SUS and MonitorAr, predictive integration of these data sources remains limited.

This project aims to bridge that gap by developing machine learning models to forecast hospital admissions due to respiratory diseases in Rio de Janeiro, offering a valuable tool for public health decision-making and hospital resource management.

## Dataset Description

### Atmospheric Data

Atmospheric data was obtained from the **MonitorAr** program, made publicly available by the [DATA.RIO - Qualidade do ar](https://www.data.rio/maps/5b1bf5c3e5114564bbf9b7a372b85e17/about). Eight air quality monitoring stations across different regions of Rio de Janeiro provided hourly measurements of air pollutants and weather variables between 2012 and 2024. Variables include:

- **Pollutants**: PM₂.₅, PM₁₀, CO, NO, NO₂, NOₓ, SO₂, O₃
- **Meteorological**: Temperature, Humidity, Precipitation
- **Air Quality Index (AQI)**

Due to different operational timelines and limitations in sensor coverage, the dataset had missing values. These were addressed via linear interpolation for days with fewer than six missing values per variable. Then, data was aggregated to daily averages for each station and finally averaged city-wide.

A Box-Cox transformation was applied to reduce skewness, followed by standardization using `StandardScaler`. This ensures all features have zero mean and unit variance for optimal model performance.

### Hospitalization Data

Hospital admission records were sourced from Brazil’s public health database (SIH/SUS), filtered to include only respiratory diseases (ICD-10 codes J40–J46). The data was limited to admissions in Rio de Janeiro between 2012 and 2024.

Two target variables were created:

```python
df['internacoes_d1'] = df['num_internacoes'].shift(-1)
df['internacoes_d7'] = df['num_internacoes'].shift(-7)
```

This yields the number of hospitalizations that occurred 1 and 7 days after each date, allowing supervised learning models to predict future hospital demand.

The hospital and atmospheric datasets were then merged on the date column to create a unified time series dataset for training and evaluation.

## Feature Engineering
To enhance predictive power, we engineered additional features from the raw variables:

- Moving Averages: for selected pollutants (e.g., SO₂, PM₁₀, PM₂.₅, AQI, Humidity, Temperature) using windows of 14 to 150 days.
- Lag Variables: up to 5-day lags of the target variable `num_internacoes`.
- Cumulative Sums: 7-day and 14-day cumulative values for selected pollutants.
- PACF Analysis: used to justify the inclusion of short-term lags in the target variable.

Only transformed variables were retained for modeling.

## Modeling Approach

Three different predictive models were developed:

### 1. LSTM Neural Network

- **Architecture**:
  - LSTM (128 units) → Dropout(0.2)
  - LSTM (64 units) → Dropout(0.2)
  - Dense(32) with `tanh` activation
  - Output: Dense(1)

- **Training Setup**:
  - Loss: Mean Squared Error (MSE)
  - Optimizer: Adam (lr=0.001)
  - EarlyStopping & ReduceLROnPlateau callbacks
  - Input sequences: 30-day sliding windows
  - Targets: `log1p` transformation of `internacoes_d1` or `internacoes_d7`

### 2. Random Forest

A `RandomForestRegressor` was trained on the same dataset, excluding sequential dependencies. This served as a non-sequential baseline for comparison.

- `n_estimators = 100`
- `random_state = 42`

### 3. Hybrid LSTM + Random Forest

A two-step residual correction approach:

1. The LSTM model generates a prediction.
2. The residual (difference between true and predicted log values) is used to train a Random Forest.
3. Final prediction = LSTM output + RF residual correction

This hybrid model leverages temporal learning from LSTM and non-linear correction power of Random Forests.

## Evaluation

Models were evaluated on the original (exponentiated) scale using:

- **RMSE** (Root Mean Squared Error)
- **MAE** (Mean Absolute Error)
- **MAPE** (Mean Absolute Percentage Error)

Time-based cross-validation (`TimeSeriesSplit`) was used to preserve the temporal structure of the data and prevent data leakage. The log-transformed targets were reverted using `np.expm1()` for evaluation.

---

### Example Evaluation Results (D+1 Forecast)

| Model        | RMSE  | MAE  | MAPE    |
|--------------|-------|------|---------|
| LSTM         | 12.28 | 7.62 | 71.46%  |
| RandomForest | 12.95 | 7.72 | 69.15%  |
| **LSTM+RF**  | **5.19**  | **2.86** | **19.75%** |

The hybrid model showed significant improvements across all metrics, demonstrating the effectiveness of residual correction.