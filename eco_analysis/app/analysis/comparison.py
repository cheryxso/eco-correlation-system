from typing import List, Dict, Any
from app.analysis.correlation import calculate_all_correlations
from app.analysis.regression import calculate_linear_regression


def method_name(method: str) -> str:
    names = {
        "pearson": "Пірсон",
        "spearman": "Спірмен",
        "kendall": "Кендалл"
    }
    return names.get(method, method)


def detect_conflicts(results: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    conflicts = []
    methods = ["pearson", "spearman", "kendall"]

    significant = [m for m in methods if results[m].get("is_significant")]
    not_significant = [m for m in methods if not results[m].get("is_significant")]

    if significant and not_significant:
        conflicts.append({
            "type": "Різна статистична значущість",
            "description": f"Значущі методи: {', '.join(method_name(m) for m in significant)}. Незначущі методи: {', '.join(method_name(m) for m in not_significant)}.",
            "possible_reason": "Можливий вплив викидів, мала вибірка або нестійка форма залежності."
        })

    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            m1 = methods[i]
            m2 = methods[j]
            c1 = float(results[m1].get("coefficient", 0) or 0)
            c2 = float(results[m2].get("coefficient", 0) or 0)

            if c1 * c2 < 0:
                conflicts.append({
                    "type": "Різний напрямок залежності",
                    "description": f"{method_name(m1)} має коефіцієнт {round(c1, 4)}, а {method_name(m2)} має коефіцієнт {round(c2, 4)}.",
                    "possible_reason": "Можлива нелінійна залежність або нестабільність даних."
                })

            if abs(abs(c1) - abs(c2)) >= 0.25:
                conflicts.append({
                    "type": "Сильна різниця між коефіцієнтами",
                    "description": f"{method_name(m1)}: {round(c1, 4)}, {method_name(m2)}: {round(c2, 4)}.",
                    "possible_reason": "Можливий вплив викидів або різниця між лінійною та ранговою залежністю."
                })

    return conflicts


def build_ranking(results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranking = []
    for method in ["pearson", "spearman", "kendall"]:
        coefficient = float(results[method].get("coefficient", 0) or 0)
        ranking.append({
            "method": method,
            "method_name": method_name(method),
            "coefficient": round(coefficient, 4),
            "abs_coefficient": round(abs(coefficient), 4),
            "is_significant": bool(results[method].get("is_significant")),
            "interpretation": results[method].get("interpretation", "")
        })

    ranking.sort(key=lambda item: item["abs_coefficient"], reverse=True)
    for index, item in enumerate(ranking, start=1):
        item["rank"] = index
        if index == 1:
            item["conclusion"] = "найсильніший результат серед методів"
        else:
            item["conclusion"] = "слабший результат порівняно з методом вище"

    return ranking


def analyze_agreement(pearson, spearman, kendall) -> Dict[str, Any]:
    coefs = [
        abs(float(pearson.get("coefficient", 0) or 0)),
        abs(float(spearman.get("coefficient", 0) or 0)),
        abs(float(kendall.get("coefficient", 0) or 0))
    ]
    max_diff = max(coefs) - min(coefs)

    sigs = [
        bool(pearson.get("is_significant")),
        bool(spearman.get("is_significant")),
        bool(kendall.get("is_significant"))
    ]
    all_agree = all(sigs) or not any(sigs)

    if max_diff < 0.1 and all_agree:
        level = "висока"
        detail = "Всі методи дають узгоджені результати"
    elif max_diff < 0.25 and all_agree:
        level = "помірна"
        detail = "Методи в цілому узгоджені, але сила коефіцієнтів трохи відрізняється"
    else:
        level = "низька"
        detail = "Є помітні розбіжності між методами"

    return {
        "level": level,
        "max_difference": round(max_diff, 4),
        "all_significant_agree": all_agree,
        "detail": detail
    }


def generate_recommendation(pearson, spearman, kendall, conflicts: List[Dict[str, str]]) -> str:
    pearson_c = abs(float(pearson.get("coefficient", 0) or 0))
    spearman_c = abs(float(spearman.get("coefficient", 0) or 0))

    if conflicts:
        return "Є суперечності між методами. Варто перевірити викиди, форму залежності та інтерпретувати результат обережно."
    if abs(pearson_c - spearman_c) > 0.15:
        return "Рекомендується звернути увагу на Спірмена, бо різниця з Пірсоном може вказувати на нелінійність або викиди."
    if pearson.get("is_significant"):
        return "Залежність статистично значуща. Для лінійної залежності можна використовувати Пірсона."
    return "Залежність статистично незначуща. Для надійнішого висновку бажано збільшити вибірку."


def compare_methods(
    x: List[float],
    y: List[float],
    x_label: str = "x",
    y_label: str = "y"
) -> Dict[str, Any]:
    correlations = calculate_all_correlations(x, y)
    regression = calculate_linear_regression(x, y, x_label, y_label)

    pearson = correlations["pearson"]
    spearman = correlations["spearman"]
    kendall = correlations["kendall"]

    method_results = {
        "pearson": pearson,
        "spearman": spearman,
        "kendall": kendall
    }

    conflicts = detect_conflicts(method_results)
    agreement = analyze_agreement(pearson, spearman, kendall)
    ranking = build_ranking(method_results)

    return {
        "method": "comparison",
        "summary_table": {
            "pearson": {
                "coefficient": pearson.get("coefficient"),
                "p_value": pearson.get("p_value"),
                "is_significant": pearson.get("is_significant"),
                "interpretation": pearson.get("interpretation")
            },
            "spearman": {
                "coefficient": spearman.get("coefficient"),
                "p_value": spearman.get("p_value"),
                "is_significant": spearman.get("is_significant"),
                "interpretation": spearman.get("interpretation")
            },
            "kendall": {
                "coefficient": kendall.get("coefficient"),
                "p_value": kendall.get("p_value"),
                "is_significant": kendall.get("is_significant"),
                "interpretation": kendall.get("interpretation")
            },
            "regression_r_squared": regression.get("r_squared"),
            "regression_equation": regression.get("equation")
        },
        "agreement": agreement,
        "conflicts": conflicts,
        "ranking": ranking,
        "recommendation": generate_recommendation(pearson, spearman, kendall, conflicts)
    }
