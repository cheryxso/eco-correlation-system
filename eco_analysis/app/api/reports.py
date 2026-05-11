from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
from app.core.database import get_db
from app.models.territory import Territory
from app.models.ecological import EcologicalMeasurement
from app.models.economic import EconomicMeasurement
from app.analysis.correlation import calculate_all_correlations
from app.analysis.partial import calculate_partial_correlation
from app.analysis.regression import calculate_linear_regression, calculate_multiple_regression
from app.analysis.timeseries import calculate_cross_correlation, calculate_rolling_correlation
from app.analysis.comparison import compare_methods
from app.services.pdf_report import generate_pdf

router = APIRouter(prefix="/reports", tags=["Звіти"])

ECO_INDICATORS = ["turbidity", "PM2.5", "PM10", "AQI", "temperature", "humidity", "pressure"]
ECON_INDICATORS = ["gdp", "salary", "unemployment", "enterprises", "healthcare", "investments"]


class ReportRequest(BaseModel):
    territory_id: int
    eco_indicator: str
    econ_indicator: str
    multiple_eco_indicators: Optional[List[str]] = None
    include_regression: Optional[bool] = True
    include_timeseries: Optional[bool] = True
    include_partial: Optional[bool] = True
    include_multiple_regression: Optional[bool] = True
    include_comparison: Optional[bool] = True


def get_related_territory_ids(territory_id: int, db: Session) -> list:
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory:
        return [territory_id]

    ids = [territory_id]
    if territory.region:
        siblings = db.query(Territory).filter(
            Territory.id != territory_id,
            Territory.region == territory.region
        ).all()
        ids.extend([t.id for t in siblings])

    return list(set(ids))


def get_eco_values(territory_id: int, indicator: str, db: Session) -> list:
    ids = get_related_territory_ids(territory_id, db)
    data = db.query(EcologicalMeasurement).filter(
        EcologicalMeasurement.territory_id.in_(ids),
        EcologicalMeasurement.indicator_type == indicator
    ).order_by(EcologicalMeasurement.measured_at).all()
    return [m.value for m in data]


def get_econ_values(territory_id: int, indicator: str, db: Session) -> list:
    ids = get_related_territory_ids(territory_id, db)
    data = db.query(EconomicMeasurement).filter(
        EconomicMeasurement.territory_id.in_(ids),
        EconomicMeasurement.indicator_type == indicator
    ).order_by(EconomicMeasurement.period).all()
    return [m.value for m in data]


def align_pair(x: list, y: list):
    min_len = min(len(x), len(y))
    return x[:min_len], y[:min_len], min_len


def find_control_indicator(territory_id: int, main_indicator: str, y_len: int, db: Session):
    for indicator in ECO_INDICATORS:
        if indicator == main_indicator:
            continue
        values = get_eco_values(territory_id, indicator, db)
        if min(len(values), y_len) >= 4:
            return indicator, values
    return None, []


def prepare_multiple_indicators(territory_id: int, selected: list, y_len: int, db: Session):
    ordered = []
    for indicator in selected:
        if indicator in ECO_INDICATORS and indicator not in ordered:
            ordered.append(indicator)
    for indicator in ECO_INDICATORS:
        if indicator not in ordered:
            ordered.append(indicator)

    result_labels = []
    result_values = []
    for indicator in ordered:
        values = get_eco_values(territory_id, indicator, db)
        if min(len(values), y_len) >= 4:
            result_labels.append(indicator)
            result_values.append(values)
        if len(result_labels) >= 3:
            break

    return result_labels, result_values


@router.post("/generate")
def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    territory = db.query(Territory).filter(Territory.id == request.territory_id).first()
    if not territory:
        raise HTTPException(status_code=404, detail="Територію не знайдено")

    if request.eco_indicator not in ECO_INDICATORS:
        raise HTTPException(status_code=400, detail="Некоректний екологічний показник")
    if request.econ_indicator not in ECON_INDICATORS:
        raise HTTPException(status_code=400, detail="Некоректний економічний показник")

    x_raw = get_eco_values(request.territory_id, request.eco_indicator, db)
    y_raw = get_econ_values(request.territory_id, request.econ_indicator, db)

    if not x_raw or not y_raw:
        raise HTTPException(status_code=404, detail="Недостатньо даних для генерації звіту")

    x, y, min_len = align_pair(x_raw, y_raw)
    if min_len < 3:
        raise HTTPException(status_code=400, detail=f"Потрібно мінімум 3 спостереження, зараз є {min_len}")

    correlation_results = calculate_all_correlations(x, y)

    regression_result = None
    if request.include_regression:
        regression_result = calculate_linear_regression(x, y, request.eco_indicator, request.econ_indicator)

    timeseries_result = None
    if request.include_timeseries:
        if min_len >= 4:
            timeseries_result = {
                "cross_correlation": calculate_cross_correlation(x, y, max_lag=3),
                "rolling_correlation": calculate_rolling_correlation(x, y, window=3)
            }
        else:
            timeseries_result = {"error": "Потрібно мінімум 4 спостереження для аналізу часових рядів"}

    partial_result = None
    if request.include_partial:
        control_indicator, z_raw = find_control_indicator(request.territory_id, request.eco_indicator, len(y_raw), db)
        if control_indicator:
            partial_len = min(len(x_raw), len(y_raw), len(z_raw))
            if partial_len >= 4:
                partial_result = calculate_partial_correlation(
                    x_raw[:partial_len],
                    y_raw[:partial_len],
                    z_raw[:partial_len]
                )
                partial_result["controlled_variable"] = control_indicator
                partial_result["n_observations"] = partial_len
        if partial_result is None:
            partial_result = {"error": "Недостатньо даних для часткової кореляції"}

    multiple_regression_result = None
    if request.include_multiple_regression:
        selected = request.multiple_eco_indicators or [request.eco_indicator]
        labels, values = prepare_multiple_indicators(request.territory_id, selected, len(y_raw), db)
        if len(labels) >= 2:
            multi_len = min(min(len(v) for v in values), len(y_raw))
            X = [v[:multi_len] for v in values]
            yy = y_raw[:multi_len]
            multiple_regression_result = calculate_multiple_regression(X, yy, labels)
        else:
            multiple_regression_result = {"error": "Недостатньо екологічних показників для множинної регресії"}

    comparison_result = None
    if request.include_comparison:
        comparison_result = compare_methods(x, y, request.eco_indicator, request.econ_indicator)

    os.makedirs("reports", exist_ok=True)
    filename = f"report_{request.territory_id}_{request.eco_indicator}_{request.econ_indicator}.pdf"
    output_path = f"reports/{filename}"

    success = generate_pdf(
        territory_name=territory.name,
        eco_indicator=request.eco_indicator,
        econ_indicator=request.econ_indicator,
        n_observations=min_len,
        correlation_results=correlation_results,
        output_path=output_path,
        regression_result=regression_result,
        timeseries_result=timeseries_result,
        partial_result=partial_result,
        multiple_regression_result=multiple_regression_result,
        comparison_result=comparison_result
    )

    if not success:
        raise HTTPException(status_code=500, detail="Помилка генерації PDF")

    return FileResponse(path=output_path, media_type="application/pdf", filename=filename)
