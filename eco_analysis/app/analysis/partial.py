import numpy as np
from scipy import stats
from typing import List, Dict, Any

def calculate_partial_correlation(
    x: List[float],
    y: List[float],
    z: List[float]
) -> Dict[str, Any]:
    if len(x) < 4:
        return {"error": "Потрібно мінімум 4 спостереження"}

    def residuals(a, b):
        coef, _, _, _, _ = np.polyfit(b, a, 1, full=False), None, None, None, None
        slope, intercept = np.polyfit(b, a, 1)
        return [a[i] - (slope * b[i] + intercept) for i in range(len(a))]

    res_x = residuals(x, z)
    res_y = residuals(y, z)

    coef, p_value = stats.pearsonr(res_x, res_y)

    return {
        "method": "partial_correlation",
        "coefficient": round(float(coef), 4),
        "p_value": round(float(p_value), 4),
        "is_significant": bool(p_value < 0.05),
        "interpretation": interpret_partial(coef),
        "controlled_variable": "z"
    }

def interpret_partial(coef: float) -> str:
    abs_coef = abs(coef)
    direction = "позитивна" if coef > 0 else "негативна"
    if abs_coef >= 0.7:
        strength = "сильна"
    elif abs_coef >= 0.4:
        strength = "помірна"
    elif abs_coef >= 0.2:
        strength = "слабка"
    else:
        strength = "дуже слабка"
    return f"{strength} {direction} часткова кореляція"