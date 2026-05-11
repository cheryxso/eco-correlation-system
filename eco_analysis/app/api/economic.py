from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import shutil
import os
from app.core.database import get_db
from app.models.economic import EconomicMeasurement
from app.models.territory import Territory
from app.schemas.economic import EconomicResponse
from app.services.data_import import import_economic_csv, preview_csv

router = APIRouter(prefix="/economic", tags=["Економічні дані"])


@router.post("/upload/{territory_id}")
def upload_economic_csv(
    territory_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Файл має бути у форматі CSV")
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = import_economic_csv(file_path, territory_id, db)
    os.remove(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "message": "Економічні дані завантажені",
        "imported": result["imported"],
        "errors": result["errors"],
        "skipped": result.get("skipped", 0),
    }


@router.post("/upload-auto")
def upload_economic_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Файл має бути у форматі CSV")
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/auto_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = import_economic_csv(file_path, None, db)
    os.remove(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "message": "Економічні дані завантажені (авто)",
        "imported": result["imported"],
        "errors": result["errors"],
        "skipped": result.get("skipped", 0),
    }


@router.post("/preview-csv")
def preview_csv_file(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/preview_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = preview_csv(file_path)
    os.remove(file_path)
    return result


@router.get("/stats/summary")
def get_econ_stats(db: Session = Depends(get_db)):
    try:
        results = db.query(
            Territory.id,
            Territory.name,
            EconomicMeasurement.indicator_type,
            func.count(EconomicMeasurement.id).label("count"),
            func.max(EconomicMeasurement.period).label("last_period")
        ).join(
            Territory,
            EconomicMeasurement.territory_id == Territory.id
        ).group_by(
            Territory.id,
            Territory.name,
            EconomicMeasurement.indicator_type
        ).all()
        return [
            {
                "territory_id": r[0],
                "territory": r[1],
                "indicator": str(r[2].value) if hasattr(r[2], "value") else str(r[2]),
                "count": r[3],
                "last_period": str(r[4]) if r[4] else None
            }
            for r in results
        ]
    except Exception:
        return []


@router.delete("/stats/{territory_id}")
def delete_econ_data(
    territory_id: int,
    indicator: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(EconomicMeasurement).filter(
        EconomicMeasurement.territory_id == territory_id
    )
    if indicator:
        query = query.filter(EconomicMeasurement.indicator_type == indicator)
    count = query.count()
    query.delete()
    db.commit()
    return {"deleted": count}


@router.get("/{territory_id}", response_model=List[EconomicResponse])
def get_economic_data(
    territory_id: int,
    indicator: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(EconomicMeasurement).filter(
        EconomicMeasurement.territory_id == territory_id
    )
    if indicator:
        query = query.filter(EconomicMeasurement.indicator_type == indicator)
    data = query.order_by(EconomicMeasurement.period).all()
    if not data:
        raise HTTPException(status_code=404, detail="Даних не знайдено")
    return data