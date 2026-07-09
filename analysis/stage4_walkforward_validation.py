"""Stage 4 -- Methodology Design: actual walk-forward validation, LSTM vs classical baselines.
Executes the pre-registered, data-length-driven rule locked at Stage 1/2 council gates:
  n>=60 -> LSTM-eligible pending validation (test here: u5mr_who, n=92)
  n=25-59 -> Prophet/BSTS-only, LSTM not expected to survive (test here: tb_incidence_per100k, n=25)
  n<25 -> walk-forward-exempt entirely (not tested)
Classical baseline = statsmodels ETS (Holt-Winters, BSTS-adjacent) + ARIMA, since Prophet is not
installed in this environment; both are legitimate small-N-appropriate alternatives and match the
method family (state-space / ARIMA) the sibling projects (19, 20) used as their winning baseline.
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

panel = pd.read_csv("../data/processed/national_panel.csv")

def get_series(col):
    s = panel[['year', col]].dropna().sort_values('year')
    return s['year'].values, s[col].values

def walk_forward_classical(y, min_train, model_fn):
    errors = []
    for cut in range(min_train, len(y)):
        train, test = y[:cut], y[cut]
        try:
            pred = model_fn(train)
        except Exception:
            continue
        errors.append(abs(pred - test))
    return errors

def ets_forecast(train):
    m = ExponentialSmoothing(train, trend='add', damped_trend=True).fit()
    return m.forecast(1)[0]

def arima_forecast(train):
    m = ARIMA(train, order=(1, 1, 1)).fit()
    return m.forecast(1)[0]

class SimpleLSTM(nn.Module):
    def __init__(self, hidden=8):
        super().__init__()
        self.lstm = nn.LSTM(1, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 1)
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

def lstm_walk_forward(y, min_train, lookback=5, epochs=100, n_seeds=3, hidden=8):
    """Multi-seed version (Stage 4 council correction, Spatial & ML Auditor + Scite Skeptic):
    a single random initialization per fold conflates genuine forecast error with initialization
    noise -- an under-specified small network (hidden=8) is especially seed-sensitive at n=25-92.
    Returns, per fold: the SEED-AVERAGED error (mean across n_seeds) plus the per-seed spread,
    so variance is reported rather than a single provisional point estimate."""
    y = np.asarray(y, dtype=np.float32)
    mean, std = y.mean(), y.std()
    yz = (y - mean) / std
    fold_mean_errors = []
    fold_seed_spreads = []
    for cut in range(min_train, len(y)):
        train = yz[:cut]
        if len(train) <= lookback:
            continue
        X, Y = [], []
        for i in range(len(train) - lookback):
            X.append(train[i:i+lookback])
            Y.append(train[i+lookback])
        X = torch.tensor(np.array(X)).unsqueeze(-1).float()
        Y = torch.tensor(np.array(Y)).unsqueeze(-1).float()
        last_window = torch.tensor(train[-lookback:]).unsqueeze(0).unsqueeze(-1).float()

        seed_errors = []
        for seed in range(n_seeds):
            torch.manual_seed(seed)
            model = SimpleLSTM(hidden=hidden)
            opt = torch.optim.Adam(model.parameters(), lr=0.01)
            loss_fn = nn.MSELoss()
            for _ in range(epochs):
                opt.zero_grad()
                pred = model(X)
                loss = loss_fn(pred, Y)
                loss.backward()
                opt.step()
            with torch.no_grad():
                pred_z = model(last_window).item()
            pred = pred_z * std + mean
            seed_errors.append(abs(pred - y[cut]))
        fold_mean_errors.append(np.mean(seed_errors))
        fold_seed_spreads.append(np.std(seed_errors))
    return fold_mean_errors, fold_seed_spreads

def mape(y, errors, n_test):
    actuals = y[-n_test:]
    return np.mean([e / abs(a) for e, a in zip(errors, actuals) if a != 0]) * 100

results = {}

print("=== TIER 1: u5mr_who (n=92) -- LSTM-eligible pending validation ===")
years, y = get_series('u5mr_who')
min_train = len(y) - 10  # last 10 years as expanding-window test folds
ets_err = walk_forward_classical(y, min_train, ets_forecast)
arima_err = walk_forward_classical(y, min_train, arima_forecast)
lstm_err, lstm_spread = lstm_walk_forward(y, min_train, hidden=8, n_seeds=5)
lstm_err_big, lstm_spread_big = lstm_walk_forward(y, min_train, hidden=32, n_seeds=5)
print(f"n={len(y)}, folds={len(ets_err)}")
print(f"ETS        MAE={np.mean(ets_err):.3f}  MAPE={mape(y, ets_err, len(ets_err)):.2f}%")
print(f"ARIMA      MAE={np.mean(arima_err):.3f}  MAPE={mape(y, arima_err, len(arima_err)):.2f}%")
print(f"LSTM(h=8)  MAE={np.mean(lstm_err):.3f} (seed SD mean={np.mean(lstm_spread):.3f})  MAPE={mape(y, lstm_err, len(lstm_err)):.2f}%")
print(f"LSTM(h=32) MAE={np.mean(lstm_err_big):.3f} (seed SD mean={np.mean(lstm_spread_big):.3f})  MAPE={mape(y, lstm_err_big, len(lstm_err_big)):.2f}%")
results['u5mr_who'] = dict(n=len(y), folds=len(ets_err),
                            ets_mae=np.mean(ets_err), arima_mae=np.mean(arima_err),
                            lstm_h8_mae=np.mean(lstm_err), lstm_h8_seed_sd=np.mean(lstm_spread),
                            lstm_h32_mae=np.mean(lstm_err_big), lstm_h32_seed_sd=np.mean(lstm_spread_big),
                            ets_mape=mape(y, ets_err, len(ets_err)), arima_mape=mape(y, arima_err, len(arima_err)),
                            lstm_h8_mape=mape(y, lstm_err, len(lstm_err)), lstm_h32_mape=mape(y, lstm_err_big, len(lstm_err_big)))

print("\n=== TIER 2: tb_incidence_per100k (n=25) -- Prophet/BSTS-only expected ===")
years2, y2 = get_series('tb_incidence_per100k')
min_train2 = len(y2) - 6
ets_err2 = walk_forward_classical(y2, min_train2, ets_forecast)
arima_err2 = walk_forward_classical(y2, min_train2, arima_forecast)
lstm_err2, lstm_spread2 = lstm_walk_forward(y2, min_train2, lookback=3, hidden=8, n_seeds=5)
lstm_err2_big, lstm_spread2_big = lstm_walk_forward(y2, min_train2, lookback=3, hidden=32, n_seeds=5)
print(f"n={len(y2)}, folds={len(ets_err2)}")
print(f"ETS        MAE={np.mean(ets_err2):.3f}  MAPE={mape(y2, ets_err2, len(ets_err2)):.2f}%")
print(f"ARIMA      MAE={np.mean(arima_err2):.3f}  MAPE={mape(y2, arima_err2, len(arima_err2)):.2f}%")
print(f"LSTM(h=8)  MAE={np.mean(lstm_err2):.3f} (seed SD mean={np.mean(lstm_spread2):.3f})  MAPE={mape(y2, lstm_err2, len(lstm_err2)):.2f}%")
print(f"LSTM(h=32) MAE={np.mean(lstm_err2_big):.3f} (seed SD mean={np.mean(lstm_spread2_big):.3f})  MAPE={mape(y2, lstm_err2_big, len(lstm_err2_big)):.2f}%")
results['tb_incidence_per100k'] = dict(n=len(y2), folds=len(ets_err2),
                            ets_mae=np.mean(ets_err2), arima_mae=np.mean(arima_err2),
                            lstm_h8_mae=np.mean(lstm_err2), lstm_h8_seed_sd=np.mean(lstm_spread2),
                            lstm_h32_mae=np.mean(lstm_err2_big), lstm_h32_seed_sd=np.mean(lstm_spread2_big),
                            ets_mape=mape(y2, ets_err2, len(ets_err2)), arima_mape=mape(y2, arima_err2, len(arima_err2)),
                            lstm_h8_mape=mape(y2, lstm_err2, len(lstm_err2)), lstm_h32_mape=mape(y2, lstm_err2_big, len(lstm_err2_big)))

pd.DataFrame(results).T.to_csv("../outputs/data/walkforward_validation_results.csv")
print("\nSaved: outputs/data/walkforward_validation_results.csv")
