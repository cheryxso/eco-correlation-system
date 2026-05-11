import numpy as np
from scipy import stats
from typing import List, Dict, Any


def safe_float(val, default=0.0) -> float:
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return f
    except Exception:
        return default


def interpret_regression(r_squared: float, p_value: float = None) -> str:
    if r_squared >= 0.9:
        quality = "дуже висока"
    elif r_squared >= 0.7:
        quality = "висока"
    elif r_squared >= 0.5:
        quality = "помірна"
    elif r_squared >= 0.3:
        quality = "низька"
    else:
        quality = "дуже низька"

    result = f"Якість моделі {quality} (R²={round(safe_float(r_squared), 4)})"
    if p_value is not None:
        result += f", модель {'значуща' if p_value < 0.05 else 'незначуща'} (p={round(safe_float(p_value), 4)})"
    return result


def calculate_linear_regression(
    x: List[float],
    y: List[float],
    x_label: str = "x",
    y_label: str = "y"
) -> Dict[str, Any]:
    if len(x) < 3:
        return {"error": "Потрібно мінімум 3 спостереження"}

    x_arr = np.array(x, dtype=float)
    y_arr = np.array(y, dtype=float)

    if np.std(x_arr) < 1e-10 or np.std(y_arr) < 1e-10:
        return {"error": "Неможливо побудувати регресію: один із рядів має сталі значення"}

    slope, intercept, r_value, p_value, std_err = stats.linregress(x_arr, y_arr)

    r_squared = safe_float(r_value ** 2)
    n = len(x_arr)
    adj_r_squared = safe_float(1 - (1 - r_squared) * (n - 1) / (n - 2)) if n > 2 else 0.0

    y_pred = slope * x_arr + intercept
    residuals = y_arr - y_pred
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))

    if ss_res > 1e-10 and n > 2:
        f_stat = safe_float((ss_tot - ss_res) / (ss_res / (n - 2)))
    else:
        f_stat = 0.0

    scatter_data = []
    for xi, yi in zip(x_arr, y_arr):
        scatter_data.append({"x": round(safe_float(xi), 4), "y": round(safe_float(yi), 4), "type": "actual"})

    x_min = float(np.min(x_arr))
    x_max = float(np.max(x_arr))
    scatter_data.append({"x": round(x_min, 4), "y": round(safe_float(slope * x_min + intercept), 4), "type": "regression"})
    scatter_data.append({"x": round(x_max, 4), "y": round(safe_float(slope * x_max + intercept), 4), "type": "regression"})

    return {
        "method": "linear_regression",
        "equation": f"{y_label} = {round(safe_float(slope), 4)} * {x_label} + {round(safe_float(intercept), 4)}",
        "slope": round(safe_float(slope), 4),
        "intercept": round(safe_float(intercept), 4),
        "r_squared": round(r_squared, 4),
        "adj_r_squared": round(adj_r_squared, 4),
        "f_statistic": round(f_stat, 4),
        "p_value": round(safe_float(p_value), 4),
        "std_error": round(safe_float(std_err), 4),
        "is_significant": bool(safe_float(p_value) < 0.05),
        "n_observations": n,
        "predicted": [round(safe_float(v), 4) for v in y_pred],
        "residuals": [round(safe_float(r), 4) for r in residuals],
        "scatter_data": scatter_data,
        "interpretation": interpret_regression(r_squared, safe_float(p_value))
    }


def interpret_vif(vif_value: float) -> str:
    if vif_value >= 10:
        return "сильна мультиколінеарність"
    if vif_value >= 5:
        return "можлива мультиколінеарність"
    return "норма"


def calculate_vif(X_arr: np.ndarray, labels: List[str]) -> List[Dict[str, Any]]:
    result = []
    n, k = X_arr.shape

    if k < 2:
        return result

    for i in range(k):
        target = X_arr[:, i]
        others = np.delete(X_arr, i, axis=1)

        if others.shape[1] == 0 or np.std(target) < 1e-10:
            vif_value = 1.0
        else:
            others_with_const = np.column_stack([np.ones(n), others])
            try:
                coef = np.linalg.lstsq(others_with_const, target, rcond=None)[0]
                pred = others_with_const @ coef
                ss_res = float(np.sum((target - pred) ** 2))
                ss_tot = float(np.sum((target - np.mean(target)) ** 2))
                r2 = 1 - ss_res / ss_tot if ss_tot > 1e-10 else 0.0
                vif_value = 1 / (1 - r2) if r2 < 0.999999 else 999.0
            except Exception:
                vif_value = 999.0

        result.append({
            "indicator": labels[i],
            "vif": round(safe_float(vif_value), 4),
            "interpretation": interpret_vif(safe_float(vif_value))
        })

    return result


def calculate_multiple_regression(
    X: List[List[float]],
    y: List[float],
    x_labels: List[str] = None
) -> Dict[str, Any]:
    if not X:
        return {"error": "Оберіть екологічні показники для множинної регресії"}

    if x_labels is None:
        x_labels = [f"x{i + 1}" for i in range(len(X))]

    required_observations = len(X) + 2
    if len(y) < required_observations:
        return {"error": f"Недостатньо спостережень: є {len(y)}, потрібно мінімум {required_observations} для {len(X)} показників"}

    try:
        X_arr = np.array(X, dtype=float).T
        y_arr = np.array(y, dtype=float)
    except Exception:
        return {"error": "Дані містять некоректні числові значення"}

    n, k = X_arr.shape
    if n < k + 2:
        return {"error": f"Недостатньо спостережень: є {n}, потрібно мінімум {k + 2} для {k} показників"}

    X_with_const = np.column_stack([np.ones(n), X_arr])

    try:
        coefficients = np.linalg.lstsq(X_with_const, y_arr, rcond=None)[0]
    except Exception as e:
        return {"error": str(e)}

    y_pred = X_with_const @ coefficients
    residuals = y_arr - y_pred
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))

    r_squared = safe_float(1 - ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
    adj_r_squared = safe_float(1 - (1 - r_squared) * (n - 1) / (n - k - 1)) if n > k + 1 else 0.0

    coef_dict = {"intercept": round(safe_float(coefficients[0]), 4)}
    for i, label in enumerate(x_labels):
        coef_dict[label] = round(safe_float(coefficients[i + 1]), 4)

    return {
        "method": "multiple_regression",
        "coefficients": coef_dict,
        "r_squared": round(r_squared, 4),
        "adj_r_squared": round(adj_r_squared, 4),
        "n_observations": n,
        "predicted": [round(safe_float(v), 4) for v in y_pred],
        "residuals": [round(safe_float(r), 4) for r in residuals],
        "vif": calculate_vif(X_arr, x_labels),
        "interpretation": interpret_regression(r_squared, None)
    }
