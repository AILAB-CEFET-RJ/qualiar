# pipeline.py
# ==========================================
# 1) Importações e setup
# ==========================================
from __future__ import annotations
from typing import Tuple, List, Dict
import argparse, os, sys, time, itertools, threading
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import re

from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
from sklearn.tree import export_text

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# ========= Helpers de console (spinner e fases) =========
class LiveSpinner:
    """Spinner simples com tempo decorrido (stdout). Use com 'with LiveSpinner(msg): ...'"""
    def __init__(self, message: str = "Processando", interval: float = 0.1):
        self.message = message
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        start = time.perf_counter()
        frames = itertools.cycle("|/-\\")
        while not self._stop.is_set():
            elapsed = time.perf_counter() - start
            sys.stdout.write(f"\r{self.message} {next(frames)}  (decorrido: {elapsed:6.1f}s)")
            sys.stdout.flush()
            time.sleep(self.interval)
        # limpar a linha
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        self._thread.join()


def phase(msg: str):
    """Contexto que marca início/fim e duração de uma fase."""
    class _Phase:
        def __enter__(self_):
            print(f"\n[⏱️] {msg} ...")
            self_.t0 = time.perf_counter()
        def __exit__(self_, exc_type, exc, tb):
            dt = time.perf_counter() - self_.t0
            print(f"[✔] {msg} finalizado em {dt:.1f}s")
    return _Phase()


# ==========================================
# 2) Carregamento e unificação dos datasets
# ==========================================
URL_INTER = "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/datasus/INTER_DR_RJ_SEAZONALITY.csv"
URL_QUALIAR = "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/main/data/DataRio/QUALIAR_RIO_DE_JANEIRO_TRATADO.csv"

def load_unificado(add_engineering: bool = True, add_calendar: bool = True) -> pd.DataFrame:
    with phase("Carregando dados brutos"):
        df_internacoes = pd.read_csv(URL_INTER, encoding="utf-8")
        df_qualiar     = pd.read_csv(URL_QUALIAR, encoding="utf-8")

    with phase("Unificando e ordenando por data"):
        df = (
            pd.merge(df_qualiar, df_internacoes, on="data_dia", how="inner")
            .sort_values("data_dia")
            .reset_index(drop=True)
        )
        df.drop(columns=["ano", "mes", "dia"], inplace=True, errors="ignore")
        df["data_dia"] = pd.to_datetime(df["data_dia"])
        df = df.sort_values("data_dia").reset_index(drop=True)

    if add_calendar:
        with phase("Criando features de calendário"):
            df["dow"] = df["data_dia"].dt.dayofweek
            df["is_weekend"] = (df["dow"] >= 5).astype(int)
            df["month"] = df["data_dia"].dt.month
            df["weekofyear"] = df["data_dia"].dt.isocalendar().week.astype(int)
            df["resp_season_peak"] = df["data_dia"].dt.month.isin([6,7,8]).astype(int)

    if add_engineering:
        with phase("Engenharia de médias móveis causais"):
            specs = [
                ("o3",   150, 0), ("o3",   150, 3), ("o3",   150, 5),
                ("no",    60, 0),
                ("so2",  150, 3), ("so2",  150, 7),
                ("nox",   60, 0),
                ("no2",   30, 0),
                ("pm10",  30, 0),
                ("pm2_5",  7, 0),
                ("co",     3, 7),
            ]
            for var, window, shift in specs:
                if var not in df.columns:
                    continue
                col_name = f"{var}_r{window}_s{shift}_mean"
                df[col_name] = (
                    df[var].shift(shift).rolling(window=window, min_periods=window).mean()
                )
    return df


# ==========================================
# 3) Funções auxiliares de preparação temporal
# ==========================================
def make_daily_frame(df: pd.DataFrame, date_col: str, target_col: str,
                     ffill_limit: int = 14, categorical_cols: List[str] | None = None) -> pd.DataFrame:
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col], errors='coerce')
    data = data.sort_values(date_col).set_index(date_col)

    full_idx = pd.date_range(data.index.min(), data.index.max(), freq='D')
    data = data.reindex(full_idx)

    if categorical_cols is None:
        categorical_cols = []

    num_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in num_cols:
        num_cols.remove(target_col)
    cat_cols = [c for c in categorical_cols if c in data.columns]

    for c in num_cols + cat_cols:
        data[f"{c}_missing"] = data[c].isna().astype(int)

    for c in num_cols:
        data[c] = data[c].ffill(limit=ffill_limit)
    for c in cat_cols:
        data[c] = data[c].ffill(limit=min(3, ffill_limit))

    return data


def apply_rolling_window(time_series_array: np.ndarray, initial_time_step: int,
                         max_time_step: int, window_size: int, target_idx: int):
    assert 0 <= target_idx < time_series_array.shape[1]
    start = initial_time_step
    sub_windows = (
        start +
        np.expand_dims(np.arange(window_size), 0) +
        np.expand_dims(np.arange(max_time_step + 1), 0).T
    )
    X = time_series_array[sub_windows]
    y = time_series_array[window_size:(max_time_step+window_size+1):1, target_idx]
    assert np.all(~np.isnan(y)), 'Há y NaN — ajuste construção de janelas.'
    return X, y


def rolling_to_tabular(df_windowed: pd.DataFrame, window_size: int,
                       target_col: str, date_index: pd.DatetimeIndex
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, List[str]]:
    cols = df_windowed.columns.tolist()
    target_idx = cols.index(target_col)
    A = df_windowed.to_numpy()
    max_ts = len(df_windowed) - window_size - 1

    X3d, y = apply_rolling_window(
        A, initial_time_step=0, max_time_step=max_ts, window_size=window_size, target_idx=target_idx
    )

    ns, w, nf = X3d.shape
    X2d = X3d.reshape(ns, w * nf)
    names = [f"{c}_t-{lag}" for lag in range(1, window_size+1) for c in cols]
    idx = date_index[window_size:(max_ts+window_size+1)]
    X_flat = pd.DataFrame(X2d, columns=names, index=idx)
    return X_flat, y, X3d, cols


# ==========================================
# 4) Métricas e utilidades
# ==========================================
def make_recency_weights(index: pd.DatetimeIndex, low: float = 0.5, high: float = 1.5) -> pd.Series:
    t = (index - index.min()).days.astype(float)
    w = low + (high - low) * (t - t.min()) / (t.max() - t.min() + 1e-9)
    return pd.Series(w, index=index).clip(lower=low, upper=high)

def smape(y, yhat):
    y = np.asarray(y, dtype=float); yhat = np.asarray(yhat, dtype=float)
    return 100*np.mean(2*np.abs(yhat - y)/(np.abs(y)+np.abs(yhat)+1e-9))

def wmape(y, yhat):
    y = np.asarray(y, dtype=float); yhat = np.asarray(yhat, dtype=float)
    return 100*np.sum(np.abs(yhat - y))/np.sum(np.abs(y)+1e-9)

def evaluate_predictions(y_true, y_pred) -> Dict[str, float]:
    return {
        'MAE': float(mean_absolute_error(y_true, y_pred)),
        'RMSE': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'R2': float(r2_score(y_true, y_pred)),
        'sMAPE': float(smape(y_true, y_pred)),
        'WMAPE': float(wmape(y_true, y_pred)),
    }


# ==========================================
# 5) Seleção de features (Permutation Importance)
# ==========================================
def select_top_features(X: pd.DataFrame, y: np.ndarray, pre: ColumnTransformer,
                        n_splits: int = 4, random_state: int = 42, k: int = 8) -> List[str]:
    print("\n[RF] Selecionando top-k features por permutation importance...")
    tscv = TimeSeriesSplit(n_splits=n_splits)
    base_rf = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_leaf=10, min_samples_split=10,
        max_features='sqrt', random_state=random_state, n_jobs=-1
    )
    ttr = TransformedTargetRegressor(regressor=base_rf, func=np.log1p, inverse_func=np.expm1)
    pipe = Pipeline([('pre', pre), ('rf', ttr)])

    folds = list(tscv.split(X))
    tr_idx, va_idx = folds[-1]
    Xtr, Xva = X.iloc[tr_idx], X.iloc[va_idx]
    ytr, yva = y[tr_idx], y[va_idx]

    with LiveSpinner("Ajustando modelo base p/ importance"):
        pipe.fit(Xtr, ytr)

    with LiveSpinner("Calculando permutation importance"):
        imp = permutation_importance(
            pipe, Xva, yva, n_repeats=10, random_state=random_state, scoring='neg_mean_absolute_error'
        )

    importances = pd.Series(imp.importances_mean, index=X.columns).sort_values(ascending=False)
    topk = importances.head(k).index.tolist()
    print(f"[RF] Top-{k}: {topk[:10]}{' ...' if len(topk)>10 else ''}")
    return topk


# ==========================================
# 6) RF com busca de hiperparâmetros (com progresso)
# ==========================================
def tune_and_fit_rf_simplified(X: pd.DataFrame, y: np.ndarray, preprocessor: ColumnTransformer,
                               n_splits: int = 5, random_state: int = 42,
                               recency_low: float = 0.7, recency_high: float = 1.3) -> Pipeline:
    base_rf = RandomForestRegressor(
        n_estimators=400, max_depth=12, min_samples_leaf=10, min_samples_split=10,
        max_features='sqrt', bootstrap=True, n_jobs=-1, random_state=random_state
    )
    ttr = TransformedTargetRegressor(regressor=base_rf, func=np.log1p, inverse_func=np.expm1)
    pipe = Pipeline([('pre', preprocessor), ('rf', ttr)])

    param_dist = {
        'rf__regressor__n_estimators': [300, 400, 600],
        'rf__regressor__max_depth': [8, 12, 16],
        'rf__regressor__min_samples_leaf': [5, 10, 20],
        'rf__regressor__min_samples_split': [5, 10, 20],
        'rf__regressor__max_features': ['sqrt', 0.5],
    }

    tscv = TimeSeriesSplit(n_splits=n_splits)
    rec_w = make_recency_weights(X.index, low=recency_low, high=recency_high).values

    print("\n[RF] Iniciando RandomizedSearchCV (isso pode levar alguns minutos)...")
    print(f"[RF] Folds: {n_splits} | Amostras treino: {len(X)} | Candidatos: {len(list(param_dist.values())[0]) * 1} (amostrados n_iter)")
    search = RandomizedSearchCV(
        pipe, param_distributions=param_dist, n_iter=12, cv=tscv,
        scoring='neg_mean_absolute_error', n_jobs=-1, random_state=random_state,
        refit=True, verbose=3  # <— imprime progresso dos fits
    )

    with LiveSpinner("Buscando melhores hiperparâmetros (RF)"):
        search.fit(X, y, rf__sample_weight=rec_w)

    print(f"[RF] Melhor conjunto de hiperparâmetros: {search.best_params_}")
    return search.best_estimator_

def print_one_tree(
    model: Pipeline,
    feature_names: List[str],
    estimator_idx: int = 0
) -> None:
    """
    Imprime uma árvore individual do Random Forest (apenas para interpretação).
    Compatível com o pipeline que usa TransformedTargetRegressor no step 'rf'.
    """
    # Step 'rf' é um TransformedTargetRegressor
    ttr = model.named_steps['rf']
    rf: RandomForestRegressor = ttr.regressor_

    # pega uma árvore do ensemble
    tree = rf.estimators_[estimator_idx]

    # exporta como texto usando os nomes de features disponíveis
    txt = export_text(
        tree,
        feature_names=feature_names[:tree.n_features_in_]
    )
    print(txt)
# ==========================================
# 7) Gráficos
# ==========================================
def _plot_series(idx, y_true, y_pred, title, plot_mode: str, outdir: str | None, filename: str):
    plt.figure(figsize=(12,5))
    plt.plot(idx, y_true, label='Observado', lw=1.2)
    plt.plot(idx, y_pred, label='Previsto', lw=1.2)
    plt.title(title); plt.xlabel('Data'); plt.ylabel('Internações / dia')
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout()
    if plot_mode == 'show':
        plt.show()
    elif plot_mode == 'save':
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, filename)
        plt.savefig(path, dpi=120, bbox_inches='tight')
        print(f"[plot salvo] {path}")
        plt.close()
    else:
        plt.close()

def predict_and_plot_rf(model: Pipeline, X: pd.DataFrame, y: np.ndarray, title: str,
                        plot_mode: str='none', outdir: str|None=None, filename: str='rf.png') -> Dict:
    y_hat = model.predict(X)
    y_hat = np.clip(y_hat, 0, None)
    m = evaluate_predictions(y, y_hat)
    _plot_series(X.index, y, y_hat, title, plot_mode, outdir, filename)
    return {'metrics': m, 'pred_df': pd.DataFrame({'y_true': y, 'y_pred': y_hat}, index=X.index)}

def predict_and_plot_lstm(model: keras.Model, X_seq_scaled: np.ndarray, y_true: np.ndarray,
                          idx_dates: pd.DatetimeIndex, title: str,
                          plot_mode: str='none', outdir: str|None=None, filename: str='lstm.png') -> Dict:
    y_hat_log = model.predict(X_seq_scaled, verbose=0).reshape(-1)
    y_hat = np.expm1(y_hat_log)
    y_hat = np.clip(y_hat, 0, None)
    m = evaluate_predictions(y_true, y_hat)
    _plot_series(idx_dates, y_true, y_hat, title, plot_mode, outdir, filename)
    return {'metrics': m, 'pred_df': pd.DataFrame({'y_true': y_true, 'y_pred': y_hat}, index=idx_dates)}


# ==========================================
# 8) Preparação dos dados
# ==========================================
def prepare_rolling_dataset(df_unificado: pd.DataFrame, date_col: str='data_dia', target_col: str='y',
                            categorical_cols: List[str]=('Qualidade_do_Ar',),
                            window_size: int=14, test_size: float=0.2, gap_days: int=7,
                            k_features: int=12, random_state: int=42) -> Dict:
    with phase("Preparando base diária (ffill, flags de missing)"):
        base = make_daily_frame(
            df_unificado, date_col=date_col, target_col=target_col,
            ffill_limit=14, categorical_cols=list(categorical_cols)
        )

    with phase("Removendo possíveis vazamentos (lags prontos do alvo)"):
        drop_regex = re.compile(r'^(y_?(lag|ma|mm|rolling|roll|shift|media|soma|sum))|(_lag\d+)$', re.IGNORECASE)
        cols_to_drop = [c for c in base.columns if drop_regex.search(c)]
        base = base.drop(columns=cols_to_drop, errors='ignore')

    with phase("Construindo janelas causais e splits"):
        feat_cols = [c for c in base.columns if c != target_col]
        X_full_tab, y_full, X_full_seq, seq_cols = rolling_to_tabular(
            base[feat_cols + [target_col]], window_size=window_size, target_col=target_col, date_index=base.index
        )
        n = len(X_full_tab)
        cut = int(np.floor((1 - test_size) * n))
        train_idx = slice(0, max(cut - gap_days, 0))
        test_idx  = slice(cut, n)

        X_train_tab, y_train = X_full_tab.iloc[train_idx], y_full[train_idx]
        X_test_tab,  y_test  = X_full_tab.iloc[test_idx],  y_full[test_idx]
        X_train_seq = X_full_seq[train_idx]; X_test_seq = X_full_seq[test_idx]

    with phase("Montando pré-processador e selecionando top-k features (RF)"):
        cat_cols = [c for c in X_train_tab.columns for base_c in categorical_cols if c.startswith(f"{base_c}_t-")]
        num_cols = [c for c in X_train_tab.columns if c not in cat_cols]

        pre_tmp = ColumnTransformer(
            transformers=[
                ('num', Pipeline([('imp', SimpleImputer(strategy='median'))]), num_cols),
                ('cat', Pipeline([('imp', SimpleImputer(strategy='most_frequent')),
                                  ('ohe', OneHotEncoder(handle_unknown='ignore'))]), cat_cols),
            ],
            remainder='drop'
        )
        topk_raw = select_top_features(X_train_tab, y_train, pre_tmp, n_splits=4, random_state=random_state, k=k_features)
        must = [f'y_t-{lag}' for lag in (1, 7, 14, 30) if f'y_t-{lag}' in X_train_tab.columns]
        features_kept = list(dict.fromkeys(must + topk_raw))[:max(k_features, len(must))]

        X_train_sel = X_train_tab[features_kept]
        X_test_sel  = X_test_tab[features_kept]

        cat_cols_sel = [c for c in features_kept for base_c in categorical_cols if c.startswith(f"{base_c}_t-")]
        num_cols_sel = [c for c in features_kept if c not in cat_cols_sel]

        pre_sel = ColumnTransformer(
            transformers=[
                ('num', Pipeline([('imp', SimpleImputer(strategy='median'))]), num_cols_sel),
                ('cat', Pipeline([('imp', SimpleImputer(strategy='most_frequent')),
                                  ('ohe', OneHotEncoder(handle_unknown='ignore'))]), cat_cols_sel),
            ],
            remainder='drop'
        )

    return {
        'X_train': X_train_sel, 'y_train': y_train,
        'X_test':  X_test_sel,  'y_test':  y_test,
        'preprocessor': pre_sel, 'features_kept': features_kept,
        'X_train_seq': X_train_seq, 'X_test_seq': X_test_seq,
        'seq_feature_names': seq_cols,
        'idx_train': X_train_sel.index, 'idx_test': X_test_sel.index,
    }


# ==========================================
# 9) Pré-processamento para LSTM
# ==========================================
def scale_seq_fit_transform(X_train_seq: np.ndarray, X_test_seq: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    with phase("Normalizando sequências (fit no treino)"):
        n_train, w, f = X_train_seq.shape
        n_test,  w2, f2 = X_test_seq.shape
        assert (w, f) == (w2, f2), "Dimensão inconsistente treino/teste"

        Xtr2d = X_train_seq.reshape(n_train*w, f).astype('float64')
        Xte2d = X_test_seq.reshape(n_test*w2, f2).astype('float64')

        med = np.nanmedian(Xtr2d, axis=0)
        inds = np.where(np.isnan(Xtr2d));  Xtr2d[inds] = med[inds[1]]
        inds2 = np.where(np.isnan(Xte2d)); Xte2d[inds2] = med[inds2[1]]

        scaler = StandardScaler()
        Xtr_scaled2d = scaler.fit_transform(Xtr2d)
        Xte_scaled2d = scaler.transform(Xte2d)

        Xtr_scaled = Xtr_scaled2d.reshape(n_train, w, f).astype('float32')
        Xte_scaled = Xte_scaled2d.reshape(n_test,  w2, f2).astype('float32')

    return Xtr_scaled, Xte_scaled, med, scaler


# ==========================================
# 10) LSTM otimizada (logs claros; Keras já mostra progresso)
# ==========================================
def build_and_train_lstm_optimized(X_train_seq_scaled: np.ndarray, y_train: np.ndarray,
                                   idx_train: pd.DatetimeIndex, window_size: int,
                                   patience: int=20, epochs: int=200, batch_size: int=32,
                                   random_state: int=42):
    print("\n[LSTM] Preparando splits temporais de treino/validação (~10% final para validação)")
    tf.random.set_seed(random_state)

    n_samples, w, n_feat = X_train_seq_scaled.shape
    assert w == window_size, "window_size não bate com shape da sequência"

    val_size = max(int(0.1 * n_samples), 1)
    train_end = n_samples - val_size

    X_tr = X_train_seq_scaled[:train_end]
    X_va = X_train_seq_scaled[train_end:]
    y_tr_raw = y_train[:train_end]
    y_va_raw = y_train[train_end:]

    y_tr = np.log1p(y_tr_raw).astype('float32')
    y_va = np.log1p(y_va_raw).astype('float32')

    rec_w_series = make_recency_weights(idx_train, low=0.7, high=1.3)
    w_full = rec_w_series.values.astype('float32')
    w_tr = w_full[:train_end]

    print("[LSTM] Construindo modelo (2 LSTM + 3 Dense com dropout)")
    model = keras.Sequential([
        layers.Input(shape=(window_size, n_feat)),
        layers.LSTM(128, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.2),

        layers.Dense(64, activation="relu"),
        layers.Dropout(0.2),
        layers.Dense(32, activation="relu"),
        layers.Dropout(0.2),

        layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=5e-4),
                  loss="mae", metrics=["mae", "mse"])

    print(f"[LSTM] Iniciando treinamento (epochs={epochs}, batch_size={batch_size}, patience={patience})")
    cb_early = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=patience, restore_best_weights=True, verbose=1
    )
    cb_reduce = keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=7, min_lr=1e-6, verbose=1
    )

    t0 = time.perf_counter()
    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_va, y_va),
        epochs=epochs, batch_size=batch_size,
        sample_weight=w_tr,
        callbacks=[cb_early, cb_reduce],
        verbose=1  # Keras já imprime barra/época
    )
    dt = time.perf_counter() - t0
    print(f"[LSTM] Treinamento concluído em {dt:.1f}s")
    return model, history


# ==========================================
# 11) Pipelines RF e LSTM
# ==========================================
def run_pipeline_rf_rolling(df_unificado: pd.DataFrame, date_col: str='data_dia', target_col: str='y',
                            categorical_cols: List[str]=('Qualidade_do_Ar',), window_size: int=14,
                            test_size: float=0.2, gap_days: int=7, k_features: int=30,
                            random_state: int=42, recency_low: float=0.7, recency_high: float=1.3,
                            plot_mode: str='none', outdir: str|None=None) -> Dict:
    prepared = prepare_rolling_dataset(
        df_unificado=df_unificado, date_col=date_col, target_col=target_col,
        categorical_cols=categorical_cols, window_size=window_size,
        test_size=test_size, gap_days=gap_days, k_features=k_features, random_state=random_state
    )

    X_train_tab = prepared['X_train']; y_train = prepared['y_train']
    X_test_tab  = prepared['X_test'];  y_test  = prepared['y_test']
    pre_sel     = prepared['preprocessor']; topk = prepared['features_kept']

    best_model = tune_and_fit_rf_simplified(
        X_train_tab, y_train, preprocessor=pre_sel, n_splits=5, random_state=random_state,
        recency_low=recency_low, recency_high=recency_high
    )

    train_res = predict_and_plot_rf(
        best_model, X_train_tab, y_train,
        'Real x Previsto — RF (Treino)', plot_mode=plot_mode, outdir=outdir, filename='rf_treino.png'
    )
    test_res  = predict_and_plot_rf(
        best_model, X_test_tab, y_test,
        'Real x Previsto — RF (Teste)',  plot_mode=plot_mode, outdir=outdir, filename='rf_teste.png'
    )

    print('\n===== Árvore 0 do RF (resumo) =====')
    print_one_tree(best_model, feature_names=X_train_tab.columns.tolist(), estimator_idx=0)

    return {'model': best_model, 'features_kept': topk,
            'train_metrics': train_res['metrics'], 'test_metrics': test_res['metrics']}


def run_pipeline_lstm_rolling_optimized(df_unificado: pd.DataFrame, date_col: str='data_dia', target_col: str='y',
                                        categorical_cols: List[str]=('Qualidade_do_Ar',), window_size: int=30,
                                        test_size: float=0.2, gap_days: int=7, random_state: int=42,
                                        patience: int=20, epochs: int=200, batch_size: int=32,
                                        plot_mode: str='none', outdir: str|None=None) -> Dict:
    prepared = prepare_rolling_dataset(
        df_unificado=df_unificado, date_col=date_col, target_col=target_col,
        categorical_cols=categorical_cols, window_size=window_size,
        test_size=test_size, gap_days=gap_days, k_features=30, random_state=random_state
    )
    X_train_seq = prepared['X_train_seq']; X_test_seq = prepared['X_test_seq']
    y_train = prepared['y_train']; y_test = prepared['y_test']
    idx_train = prepared['idx_train']; idx_test = prepared['idx_test']

    X_train_scaled, X_test_scaled, medians_used, scaler_seq = scale_seq_fit_transform(X_train_seq, X_test_seq)
    lstm_model, history = build_and_train_lstm_optimized(
        X_train_scaled, y_train, idx_train=idx_train, window_size=window_size,
        patience=patience, epochs=epochs, batch_size=batch_size, random_state=random_state
    )

    train_res = predict_and_plot_lstm(
        lstm_model, X_train_scaled, y_train, idx_train,
        title='Real x Previsto — LSTM Otimizada (Treino)', plot_mode=plot_mode, outdir=outdir, filename='lstm_treino.png'
    )
    test_res = predict_and_plot_lstm(
        lstm_model, X_test_scaled, y_test, idx_test,
        title='Real x Previsto — LSTM Otimizada (Teste)',  plot_mode=plot_mode, outdir=outdir, filename='lstm_teste.png'
    )
    return {'model': lstm_model, 'train_metrics': train_res['metrics'], 'test_metrics': test_res['metrics']}


# ==========================================
# 12) CLI com argparse
# ==========================================
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pipeline de previsão (RF ou LSTM) com estados de carregamento.")
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp):
        sp.add_argument("--test-size", type=float, default=0.20, help="Proporção de teste (default: 0.20)")
        sp.add_argument("--gap-days", type=int, default=7, help="Folga temporal entre treino e teste (default: 7)")
        sp.add_argument("--date-col", default="data_dia", help="Nome da coluna de data (default: data_dia)")
        sp.add_argument("--target-col", default="y", help="Nome da coluna alvo (default: y)")
        sp.add_argument("--random-state", type=int, default=42, help="Seed (default: 42)")
        sp.add_argument("--max-year", type=int, default=None, help="Filtra df_unificado para ano <= max-year (opcional)")
        sp.add_argument("--plots", choices=["show","save","none"], default="none",
                        help="Exibir/salvar gráficos: show | save | none (default: none)")
        sp.add_argument("--outdir", default="outputs", help="Pasta para salvar gráficos (se --plots save)")

    sp_rf = sub.add_parser("rf", help="Executa o Random Forest")
    add_common(sp_rf)
    sp_rf.add_argument("--window-size", type=int, default=14, help="Tamanho da janela causal (default: 14)")
    sp_rf.add_argument("--k-features", type=int, default=30, help="Top-k features após seleção (default: 30)")
    sp_rf.add_argument("--recency-low", type=float, default=0.7, help="Peso mínimo de recência (default: 0.7)")
    sp_rf.add_argument("--recency-high", type=float, default=1.3, help="Peso máximo de recência (default: 1.3)")

    sp_lstm = sub.add_parser("lstm", help="Executa a LSTM otimizada")
    add_common(sp_lstm)
    sp_lstm.add_argument("--window-size", type=int, default=30, help="Tamanho da janela causal (default: 30)")
    sp_lstm.add_argument("--epochs", type=int, default=200, help="Épocas de treino (default: 200)")
    sp_lstm.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    sp_lstm.add_argument("--patience", type=int, default=20, help="Paciência do EarlyStopping (default: 20)")

    return p


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    # Backend de plot
    if args.plots == "show":
        pass
    else:
        matplotlib.use("Agg")

    df_unificado = load_unificado(add_engineering=True, add_calendar=True)

    if args.max_year is not None and "year" in df_unificado.columns:
        df_unificado = df_unificado[df_unificado["year"] <= args.max_year].copy()

    if args.command == "rf":
        out = run_pipeline_rf_rolling(
            df_unificado=df_unificado, date_col=args.date_col, target_col=args.target_col,
            window_size=args.window_size, test_size=args.test_size, gap_days=args.gap_days,
            k_features=args.k_features, random_state=args.random_state,
            recency_low=args.recency_low, recency_high=args.recency_high,
            plot_mode=args.plots, outdir=args.outdir
        )
        print("\n[RF] Features usadas:", out["features_kept"])
        print("[RF] Métricas Treino:", out["train_metrics"])
        print("[RF] Métricas Teste :", out["test_metrics"])

    elif args.command == "lstm":
        out = run_pipeline_lstm_rolling_optimized(
            df_unificado=df_unificado, date_col=args.date_col, target_col=args.target_col,
            window_size=args.window_size, test_size=args.test_size, gap_days=args.gap_days,
            random_state=args.random_state, epochs=args.epochs, batch_size=args.batch_size,
            patience=args.patience, plot_mode=args.plots, outdir=args.outdir
        )
        print("\n[LSTM] Métricas Treino:", out["train_metrics"])
        print("[LSTM] Métricas Teste :", out["test_metrics"])
    else:
        parser.error("Comando desconhecido.")


if __name__ == "__main__":
    main()
