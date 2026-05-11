from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import math
from app.core.database import get_db
from app.models.ecological import EcologicalMeasurement
from app.models.economic import EconomicMeasurement
from app.models.territory import Territory
from app.analysis.correlation import calculate_all_correlations, apply_bonferroni_correction
from app.analysis.partial import calculate_partial_correlation
from pydantic import BaseModel
from app.analysis.timeseries import calculate_cross_correlation, calculate_rolling_correlation
from app.analysis.regression import calculate_linear_regression, calculate_multiple_regression
from app.analysis.comparison import compare_methods

router = APIRouter(prefix="/analysis", tags=["Аналіз"])

ECO_INDICATORS = ["turbidity", "PM2.5", "PM10", "AQI", "temperature", "humidity", "pressure"]
ECON_INDICATORS = ["gdp", "salary", "unemployment", "enterprises", "healthcare", "investments"]


class CorrelationRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str
    apply_bonferroni: Optional[bool] = False


class PartialCorrelationRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str
    control_eco_indicator: str


class TimeSeriesRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str
    max_lag: Optional[int] = 6
    window: Optional[int] = 3


class RegressionRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str


class MultipleRegressionRequest(BaseModel):
    territory_id: int
    eco_indicators: List[str]
    econ_indicator: str


class ComparisonRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return r * 2 * math.asin(math.sqrt(a))


def get_related_territory_ids(territory_id: int, db: Session) -> list:
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory:
        return [territory_id]

    ids = [territory_id]
    name = territory.name

    if "область" in name.lower():
        related = db.query(Territory).filter(
            Territory.region == name
        ).all()
        for t in related:
            ids.append(t.id)
    else:
        if territory.region:
            for part in territory.region.split(","):
                part = part.strip()
                if not part:
                    continue
                region_t = db.query(Territory).filter(
                    Territory.id != territory_id,
                    Territory.name.ilike(f"%{part}%")
                ).first()
                if region_t:
                    ids.append(region_t.id)
                    break
            siblings = db.query(Territory).filter(
                Territory.id != territory_id,
                Territory.region == territory.region
            ).all()
            for t in siblings:
                ids.append(t.id)

    return list(set(ids))


def find_nearest_territory_with_data(
    territory_id: int,
    indicator: str,
    model,
    db: Session
) -> list:
    """
    Якщо для даної території немає даних по вказаному показнику —
    знаходить найближчу територію що має ці дані, і повертає її значення.
    """
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory or not territory.latitude or not territory.longitude:
        return []

    all_territories = db.query(Territory).filter(
        Territory.id != territory_id,
        Territory.latitude.isnot(None),
        Territory.longitude.isnot(None)
    ).all()

    candidates = []
    for t in all_territories:
        count = db.query(model).filter(
            model.territory_id == t.id,
            model.indicator_type == indicator
        ).count()
        if count > 0:
            dist = haversine(
                territory.latitude, territory.longitude,
                t.latitude, t.longitude
            )
            candidates.append((dist, t))

    if not candidates:
        return []

    candidates.sort(key=lambda x: x[0])
    nearest = candidates[0][1]

    if hasattr(model, 'measured_at'):
        data = db.query(model).filter(
            model.territory_id == nearest.id,
            model.indicator_type == indicator
        ).order_by(model.measured_at).all()
    else:
        data = db.query(model).filter(
            model.territory_id == nearest.id,
            model.indicator_type == indicator
        ).order_by(model.period).all()

    return [m.value for m in data]


def get_eco_values(territory_id: int, indicator: str, db: Session) -> list:
    ids = get_related_territory_ids(territory_id, db)
    data = db.query(EcologicalMeasurement).filter(
        EcologicalMeasurement.territory_id.in_(ids),
        EcologicalMeasurement.indicator_type == indicator
    ).order_by(EcologicalMeasurement.measured_at).all()
    values = [m.value for m in data]

    if not values:
        values = find_nearest_territory_with_data(
            territory_id, indicator, EcologicalMeasurement, db
        )

    return values


def get_econ_values(territory_id: int, indicator: str, db: Session) -> list:
    ids = get_related_territory_ids(territory_id, db)
    data = db.query(EconomicMeasurement).filter(
        EconomicMeasurement.territory_id.in_(ids),
        EconomicMeasurement.indicator_type == indicator
    ).order_by(EconomicMeasurement.period).all()
    values = [m.value for m in data]

    if not values:
        values = find_nearest_territory_with_data(
            territory_id, indicator, EconomicMeasurement, db
        )

    return values


@router.post("/correlation")
def run_correlation(request: CorrelationRequest, db: Session = Depends(get_db)):
    x = get_eco_values(request.territory_id, request.eco_indicator, db)
    y = get_econ_values(request.territory_id, request.econ_indicator, db)

    if not x:
        raise HTTPException(status_code=404, detail=f"Екологічні дані '{request.eco_indicator}' не знайдено")
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")

    min_len = min(len(x), len(y))
    if min_len < 3:
        raise HTTPException(status_code=400, detail=f"Потрібно мінімум 3 спостереження (є {min_len})")

    x, y = x[:min_len], y[:min_len]
    results = calculate_all_correlations(x, y)

    if request.apply_bonferroni:
        p_values = [
            results["pearson"]["p_value"],
            results["spearman"]["p_value"],
            results["kendall"]["p_value"]
        ]
        corrected = apply_bonferroni_correction(p_values)
        results["pearson"]["p_value_bonferroni"] = corrected[0]
        results["spearman"]["p_value_bonferroni"] = corrected[1]
        results["kendall"]["p_value_bonferroni"] = corrected[2]

    return {
        "territory_id": request.territory_id,
        "eco_indicator": request.eco_indicator,
        "econ_indicator": request.econ_indicator,
        "n_observations": min_len,
        "results": results
    }


@router.post("/partial-correlation")
def run_partial_correlation(request: PartialCorrelationRequest, db: Session = Depends(get_db)):
    x = get_eco_values(request.territory_id, request.eco_indicator, db)
    y = get_econ_values(request.territory_id, request.econ_indicator, db)
    z = get_eco_values(request.territory_id, request.control_eco_indicator, db)

    if not x:
        raise HTTPException(status_code=404, detail=f"Екологічні дані '{request.eco_indicator}' не знайдено")
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")
    if not z:
        raise HTTPException(status_code=404, detail=f"Контрольна змінна '{request.control_eco_indicator}' не знайдено")

    min_len = min(len(x), len(y), len(z))
    if min_len < 4:
        raise HTTPException(status_code=400, detail="Потрібно мінімум 4 спостереження")

    x, y, z = x[:min_len], y[:min_len], z[:min_len]
    result = calculate_partial_correlation(x, y, z)
    result["controlled_variable"] = request.control_eco_indicator

    return {
        "territory_id": request.territory_id,
        "eco_indicator": request.eco_indicator,
        "econ_indicator": request.econ_indicator,
        "control_variable": request.control_eco_indicator,
        "n_observations": min_len,
        "result": result
    }


@router.post("/timeseries")
def run_timeseries(request: TimeSeriesRequest, db: Session = Depends(get_db)):
    x = get_eco_values(request.territory_id, request.eco_indicator, db)
    y = get_econ_values(request.territory_id, request.econ_indicator, db)

    if not x:
        raise HTTPException(status_code=404, detail=f"Екологічні дані '{request.eco_indicator}' не знайдено")
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")

    min_len = min(len(x), len(y))
    if min_len < 4:
        raise HTTPException(status_code=400, detail="Потрібно мінімум 4 спостереження")

    x, y = x[:min_len], y[:min_len]
    cross_corr = calculate_cross_correlation(x, y, request.max_lag)
    rolling_corr = calculate_rolling_correlation(x, y, request.window)

    return {
        "territory_id": request.territory_id,
        "eco_indicator": request.eco_indicator,
        "econ_indicator": request.econ_indicator,
        "n_observations": min_len,
        "cross_correlation": cross_corr,
        "rolling_correlation": rolling_corr
    }


@router.post("/regression")
def run_regression(request: RegressionRequest, db: Session = Depends(get_db)):
    x = get_eco_values(request.territory_id, request.eco_indicator, db)
    y = get_econ_values(request.territory_id, request.econ_indicator, db)

    if not x:
        raise HTTPException(status_code=404, detail=f"Екологічні дані '{request.eco_indicator}' не знайдено")
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")

    min_len = min(len(x), len(y))
    if min_len < 3:
        raise HTTPException(status_code=400, detail="Потрібно мінімум 3 спостереження")

    x, y = x[:min_len], y[:min_len]
    result = calculate_linear_regression(x, y, request.eco_indicator, request.econ_indicator)

    slope = result.get("slope", 0)
    intercept = result.get("intercept", 0)
    predicted = [round(slope * xi + intercept, 4) for xi in x]
    result["predicted"] = predicted

    scatter_data = []
    for xi, yi in zip(x, y):
        scatter_data.append({"x": round(float(xi), 4), "y": round(float(yi), 4), "type": "actual"})
    x_min, x_max = min(x), max(x)
    scatter_data.append({"x": round(float(x_min), 4), "y": round(slope * x_min + intercept, 4), "type": "regression"})
    scatter_data.append({"x": round(float(x_max), 4), "y": round(slope * x_max + intercept, 4), "type": "regression"})
    result["scatter_data"] = scatter_data

    return {
        "territory_id": request.territory_id,
        "eco_indicator": request.eco_indicator,
        "econ_indicator": request.econ_indicator,
        "n_observations": min_len,
        "result": result
    }


@router.post("/regression/multiple")
def run_multiple_regression(request: MultipleRegressionRequest, db: Session = Depends(get_db)):
    X = []
    for indicator in request.eco_indicators:
        values = get_eco_values(request.territory_id, indicator, db)
        if not values:
            raise HTTPException(status_code=404, detail=f"Екологічні дані '{indicator}' не знайдено")
        X.append(values)

    y = get_econ_values(request.territory_id, request.econ_indicator, db)
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")

    min_len = min(min(len(xi) for xi in X), len(y))
    if min_len < 4:
        raise HTTPException(status_code=400, detail="Потрібно мінімум 4 спостереження")

    X = [xi[:min_len] for xi in X]
    y = y[:min_len]

    required_observations = len(X) + 2
    if len(y) < required_observations:
        raise HTTPException(
            status_code=400,
            detail=f"Недостатньо спостережень: є {len(y)}, потрібно мінімум {required_observations} для {len(X)} показників"
        )

    result = calculate_multiple_regression(X, y, request.eco_indicators)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "territory_id": request.territory_id,
        "eco_indicators": request.eco_indicators,
        "econ_indicator": request.econ_indicator,
        "n_observations": len(y),
        "result": result
    }


@router.post("/comparison")
def run_comparison(request: ComparisonRequest, db: Session = Depends(get_db)):
    x = get_eco_values(request.territory_id, request.eco_indicator, db)
    y = get_econ_values(request.territory_id, request.econ_indicator, db)

    if not x:
        raise HTTPException(status_code=404, detail=f"Екологічні дані '{request.eco_indicator}' не знайдено")
    if not y:
        raise HTTPException(status_code=404, detail=f"Економічні дані '{request.econ_indicator}' не знайдено")

    min_len = min(len(x), len(y))
    if min_len < 3:
        raise HTTPException(status_code=400, detail="Потрібно мінімум 3 спостереження")

    x, y = x[:min_len], y[:min_len]
    result = compare_methods(x, y, request.eco_indicator, request.econ_indicator)

    return {
        "territory_id": request.territory_id,
        "eco_indicator": request.eco_indicator,
        "econ_indicator": request.econ_indicator,
        "n_observations": min_len,
        "result": result
    }


@router.post("/correlation-matrix")
def run_correlation_matrix(territory_id: int, db: Session = Depends(get_db)):
    eco_data = {}
    for indicator in ECO_INDICATORS:
        values = get_eco_values(territory_id, indicator, db)
        if len(values) >= 3:
            eco_data[indicator] = values

    econ_data = {}
    for indicator in ECON_INDICATORS:
        values = get_econ_values(territory_id, indicator, db)
        if len(values) >= 3:
            econ_data[indicator] = values

    if not eco_data:
        raise HTTPException(status_code=404, detail="Немає екологічних даних для цієї території")
    if not econ_data:
        raise HTTPException(status_code=404, detail="Немає економічних даних для цієї території")

    matrix = []
    for eco_ind, eco_values in eco_data.items():
        for econ_ind, econ_values in econ_data.items():
            min_len = min(len(eco_values), len(econ_values))
            if min_len < 3:
                continue
            x = eco_values[:min_len]
            y = econ_values[:min_len]

            from app.analysis.correlation import calculate_pearson, calculate_spearman
            pearson = calculate_pearson(x, y)
            spearman = calculate_spearman(x, y)

            matrix.append({
                "eco_indicator": eco_ind,
                "econ_indicator": econ_ind,
                "n": min_len,
                "pearson": pearson.get("coefficient"),
                "pearson_p": pearson.get("p_value"),
                "pearson_significant": pearson.get("is_significant"),
                "spearman": spearman.get("coefficient"),
                "spearman_p": spearman.get("p_value"),
                "spearman_significant": spearman.get("is_significant"),
                "interpretation": pearson.get("interpretation"),
            })

    if matrix:
        all_p = [row["pearson_p"] for row in matrix if row["pearson_p"] is not None]
        n = len(all_p)
        for row in matrix:
            if row["pearson_p"] is not None:
                row["pearson_p_bonferroni"] = round(min(row["pearson_p"] * n, 1.0), 4)
                row["pearson_significant_bonferroni"] = row["pearson_p_bonferroni"] < 0.05

    return {
        "territory_id": territory_id,
        "eco_indicators": list(eco_data.keys()),
        "econ_indicators": list(econ_data.keys()),
        "matrix": matrix,
        "total_pairs": len(matrix)
    }