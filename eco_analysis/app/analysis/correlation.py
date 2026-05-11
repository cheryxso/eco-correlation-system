import numpy as np
from scipy import stats
from typing import List, Dict, Any, Tuple


def interpolate_missing(values: List[float]) -> List[float]:
    """
    Лінійна інтерполяція пропущених значень (None/NaN).
    Крайні пропуски заповнюються найближчим наявним значенням.
    """
    arr = np.array(values, dtype=float)
    nans = np.isnan(arr)
    if not nans.any():
        return values

    indices = np.arange(len(arr))
    arr[nans] = np.interp(indices[nans], indices[~nans], arr[~nans])
    return arr.tolist()


def remove_outliers_iqr(values: List[float], factor: float = 1.5) -> Tuple[List[float], int]:
    """
    Виявлення та заміна викидів методом міжквартильного розмаху (IQR).

    Значення за межами [Q1 - factor*IQR, Q3 + factor*IQR] вважаються викидами
    і замінюються на медіану вибірки (замість видалення, щоб не скорочувати ряд).

    Повертає очищений список і кількість замінених викидів.
    """
    arr = np.array(values, dtype=float)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1

    if iqr == 0:
        return values, 0

    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    median = np.median(arr)

    outlier_mask = (arr < lower) | (arr > upper)
    outlier_count = int(outlier_mask.sum())

    arr[outlier_mask] = median
    return arr.tolist(), outlier_count


def prepare_data(x: List[float], y: List[float]) -> Dict[str, Any]:
    """
    Повна підготовка двох рядів даних до кореляційного аналізу:
    1. Інтерполяція пропущених значень
    2. Видалення викидів методом IQR
    3. Повертає підготовлені дані і звіт про трансформації
    """
    x_interp = interpolate_missing(x)
    y_interp = interpolate_missing(y)

    x_clean, x_outliers = remove_outliers_iqr(x_interp)
    y_clean, y_outliers = remove_outliers_iqr(y_interp)

    return {
        "x": x_clean,
        "y": y_clean,
        "preparation_report": {
            "original_length": len(x),
            "x_outliers_replaced": x_outliers,
            "y_outliers_replaced": y_outliers,
            "x_missing_interpolated": sum(1 for v in x if v is None or (isinstance(v, float) and np.isnan(v))),
            "y_missing_interpolated": sum(1 for v in y if v is None or (isinstance(v, float) and np.isnan(v))),
        }
    }


def check_normality(x: List[float]) -> Dict[str, Any]:
    """Тест Шапіро-Вілка на нормальність розподілу"""
    if len(x) < 3:
        return {"is_normal": None, "p_value": None, "note": "Замало даних"}
    if len(x) > 5000:
        return {"is_normal": None, "p_value": None, "note": "Вибірка завелика для тесту Шапіро-Вілка"}
    stat, p_value = stats.shapiro(x)
    is_normal = bool(p_value > 0.05)
    return {
        "statistic": round(float(stat), 4),
        "p_value": round(float(p_value), 4),
        "is_normal": is_normal,
        "note": "нормальний розподіл" if is_normal else "розподіл не нормальний"
    }


def recommend_method(normality_x: Dict, normality_y: Dict) -> str:
    x_normal = normality_x.get("is_normal")
    y_normal = normality_y.get("is_normal")
    if x_normal is None or y_normal is None:
        return "Недостатньо даних для рекомендації"
    if x_normal and y_normal:
        return "Обидва розподіли нормальні - рекомендується Пірсон"
    if not x_normal and not y_normal:
        return "Обидва розподіли не нормальні - рекомендується Спірмен або Кендалл"
    return "Один розподіл не нормальний - рекомендується Спірмен або Кендалл"


def interpret_correlation(coef: float) -> str:
    abs_coef = abs(coef)
    direction = "позитивна" if coef > 0 else "негативна"
    if abs_coef >= 0.9:
        strength = "дуже сильна"
    elif abs_coef >= 0.7:
        strength = "сильна"
    elif abs_coef >= 0.5:
        strength = "помірна"
    elif abs_coef >= 0.3:
        strength = "слабка"
    else:
        strength = "дуже слабка"
    return f"{strength} {direction} кореляція"


def calculate_pearson(x: List[float], y: List[float]) -> Dict[str, Any]:
    if len(x) < 3 or len(y) < 3:
        return {"error": "Потрібно мінімум 3 спостереження"}
    coef, p_value = stats.pearsonr(x, y)
    return {
        "method": "pearson",
        "coefficient": round(float(coef), 4),
        "p_value": round(float(p_value), 4),
        "is_significant": bool(p_value < 0.05),
        "interpretation": interpret_correlation(coef)
    }


def calculate_spearman(x: List[float], y: List[float]) -> Dict[str, Any]:
    if len(x) < 3 or len(y) < 3:
        return {"error": "Потрібно мінімум 3 спостереження"}
    coef, p_value = stats.spearmanr(x, y)
    return {
        "method": "spearman",
        "coefficient": round(float(coef), 4),
        "p_value": round(float(p_value), 4),
        "is_significant": bool(p_value < 0.05),
        "interpretation": interpret_correlation(coef)
    }


def calculate_kendall(x: List[float], y: List[float]) -> Dict[str, Any]:
    if len(x) < 3 or len(y) < 3:
        return {"error": "Потрібно мінімум 3 спостереження"}
    coef, p_value = stats.kendalltau(x, y)
    return {
        "method": "kendall",
        "coefficient": round(float(coef), 4),
        "p_value": round(float(p_value), 4),
        "is_significant": bool(p_value < 0.05),
        "interpretation": interpret_correlation(coef)
    }


def calculate_all_correlations(x: List[float], y: List[float]) -> Dict[str, Any]:
    prepared = prepare_data(x, y)
    x_clean = prepared["x"]
    y_clean = prepared["y"]

    normality_x = check_normality(x_clean)
    normality_y = check_normality(y_clean)

    return {
        "preparation": prepared["preparation_report"],
        "normality_check": {
            "eco_indicator": normality_x,
            "econ_indicator": normality_y,
            "recommendation": recommend_method(normality_x, normality_y)
        },
        "pearson": calculate_pearson(x_clean, y_clean),
        "spearman": calculate_spearman(x_clean, y_clean),
        "kendall": calculate_kendall(x_clean, y_clean)
    }


def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    n = len(p_values)
    return [round(min(float(p) * n, 1.0), 4) for p in p_values]