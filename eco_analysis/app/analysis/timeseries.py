import numpy as np
from scipy import stats
from typing import List, Dict, Any


def safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return 0.0
        return f
    except Exception:
        return 0.0


def calculate_cross_correlation(
    x: List[float],
    y: List[float],
    max_lag: int = 6
) -> Dict[str, Any]:
    if len(x) < 4:
        return {"error": "Потрібно мінімум 4 спостереження"}

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    x = (x - np.mean(x)) / (np.std(x) + 1e-10)
    y = (y - np.mean(y)) / (np.std(y) + 1e-10)

    # Обмежуємо max_lag щоб залишалось мінімум 2 елементи
    safe_max_lag = min(max_lag, len(x) // 2 - 1)
    if safe_max_lag < 0:
        safe_max_lag = 0

    lags = range(-safe_max_lag, safe_max_lag + 1)
    correlations = []

    for lag in lags:
        try:
            if lag < 0:
                xa = x[:lag]
                ya = y[-lag:]
            elif lag > 0:
                xa = x[lag:]
                ya = y[:-lag]
            else:
                xa = x
                ya = y

            if len(xa) < 2 or len(ya) < 2:
                continue

            corr, p_val = stats.pearsonr(xa, ya)
            correlations.append({
                "lag": int(lag),
                "correlation": safe_float(corr),
                "p_value": safe_float(p_val),
                "is_significant": bool(safe_float(p_val) < 0.05)
            })
        except Exception:
            continue

    if not correlations:
        return {"error": "Недостатньо даних для крос-кореляції"}

    best = max(correlations, key=lambda c: abs(c["correlation"]))

    return {
        "method": "cross_correlation",
        "correlations_by_lag": correlations,
        "optimal_lag": best["lag"],
        "optimal_correlation": best["correlation"],
        "interpretation": f"Найсильніша кореляція при лагу {best['lag']} = {best['correlation']}"
    }


def calculate_rolling_correlation(
    x: List[float],
    y: List[float],
    window: int = 3
) -> Dict[str, Any]:
    if len(x) < window + 1:
        return {
            "error": f"Потрібно мінімум {window + 1} спостережень для вікна {window}",
            "window_size": window,
            "rolling_correlations": [],
            "average_correlation": 0.0,
            "interpretation": f"Недостатньо даних для ковзної кореляції з вікном {window}"
        }

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    rolling = []
    for i in range(len(x) - window + 1):
        x_window = x[i:i + window]
        y_window = y[i:i + window]
        try:
            if np.std(x_window) < 1e-10 or np.std(y_window) < 1e-10:
                corr = 0.0
            else:
                corr, _ = stats.pearsonr(x_window, y_window)
                corr = safe_float(corr)
        except Exception:
            corr = 0.0

        rolling.append({
            "window_start": i,
            "window_end": i + window - 1,
            "correlation": round(corr, 4)
        })

    if not rolling:
        avg_corr = 0.0
    else:
        avg_corr = safe_float(np.mean([r["correlation"] for r in rolling]))

    return {
        "method": "rolling_correlation",
        "window_size": window,
        "rolling_correlations": rolling,
        "average_correlation": round(avg_corr, 4),
        "interpretation": f"Середня ковзна кореляція з вікном {window} = {round(avg_corr, 4)}"
    }