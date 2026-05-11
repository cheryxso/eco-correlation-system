from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import shutil
import os
import httpx
from app.core.database import get_db
from app.models.ecological import EcologicalMeasurement
from app.models.territory import Territory
from app.schemas.ecological import EcologicalResponse
from app.services.data_import import import_ecological_csv, preview_csv
from app.services.saveecobot import fetch_saveecobot_data

router = APIRouter(prefix="/ecological", tags=["Екологічні дані"])


def extract_region_from_display_name(display_name: str) -> str:
    parts = [p.strip() for p in display_name.split(",")]
    for part in parts:
        if "область" in part.lower():
            return part
    return parts[1] if len(parts) > 1 else ""


@router.post("/upload/{territory_id}")
def upload_ecological_csv(
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
    result = import_ecological_csv(file_path, territory_id, db)
    os.remove(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "message": "Екологічні дані завантажені",
        "imported": result["imported"],
        "errors": result["errors"],
        "skipped": result.get("skipped", 0),
    }


@router.post("/upload-auto")
def upload_ecological_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Файл має бути у форматі CSV")
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/auto_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = import_ecological_csv(file_path, None, db)
    os.remove(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "message": "Екологічні дані завантажені (авто)",
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
def get_eco_stats(db: Session = Depends(get_db)):
    try:
        results = db.query(
            Territory.id,
            Territory.name,
            EcologicalMeasurement.indicator_type,
            func.count(EcologicalMeasurement.id).label("count"),
            func.max(EcologicalMeasurement.measured_at).label("last_date")
        ).join(
            Territory,
            EcologicalMeasurement.territory_id == Territory.id
        ).group_by(
            Territory.id,
            Territory.name,
            EcologicalMeasurement.indicator_type
        ).all()
        return [
            {
                "territory_id": r[0],
                "territory": r[1],
                "indicator": str(r[2].value) if hasattr(r[2], "value") else str(r[2]),
                "count": r[3],
                "last_date": str(r[4])[:10] if r[4] else None
            }
            for r in results
        ]
    except Exception:
        return []


@router.delete("/stats/{territory_id}")
def delete_eco_data(
    territory_id: int,
    indicator: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(EcologicalMeasurement).filter(
        EcologicalMeasurement.territory_id == territory_id
    )
    if indicator:
        query = query.filter(EcologicalMeasurement.indicator_type == indicator)
    count = query.count()
    query.delete()
    db.commit()
    return {"deleted": count}


@router.post("/fetch-by-city")
async def fetch_by_city(city: str, db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            nom_response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{city}, Ukraine",
                    "format": "json",
                    "limit": 1,
                    "accept-language": "uk"
                },
                headers={"User-Agent": "eco-analysis-system/1.0"},
                timeout=10.0
            )
            nom_results = nom_response.json()
            if not nom_results:
                raise HTTPException(status_code=404, detail=f"Місто '{city}' не знайдено")
            lat = float(nom_results[0]["lat"])
            lon = float(nom_results[0]["lon"])
            display_name = nom_results[0].get("display_name", "")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка геокодування: {str(e)}")

    region = extract_region_from_display_name(display_name)

    territory = db.query(Territory).filter(
        Territory.name.ilike(f"%{city}%")
    ).first()

    created = False
    if not territory:
        territory = Territory(
            name=city,
            region=region,
            latitude=lat,
            longitude=lon
        )
        db.add(territory)
        db.commit()
        db.refresh(territory)
        created = True
    else:
        if not territory.region or "громада" in (territory.region or "").lower() or "район" in (territory.region or "").lower():
            territory.region = region
        if not territory.latitude:
            territory.latitude = lat
            territory.longitude = lon
        db.commit()

    saveecobot_result = await fetch_saveecobot_data(
        city=city,
        territory_id=territory.id,
        db=db,
        region=territory.region,
        city_lat=lat,
        city_lon=lon
    )

    imported = saveecobot_result.get("imported", 0)

    return {
        "city": city,
        "territory_id": territory.id,
        "territory_created": created,
        "region": territory.region,
        "coordinates": {"lat": lat, "lon": lon},
        "imported": imported,
        "stations_found": saveecobot_result.get("stations_found", 0),
        "territories_updated": saveecobot_result.get("territories_updated", 1),
        "used_nearest": saveecobot_result.get("used_nearest", False),
        "nearest_city": saveecobot_result.get("nearest_city"),
        "success": saveecobot_result["success"],
        "error": saveecobot_result.get("error"),
        "message": f"Завантажено {imported} записів для {city} ({territory.region})"
                   if saveecobot_result["success"]
                   else saveecobot_result.get("error", "Помилка")
    }


@router.get("/{territory_id}", response_model=List[EcologicalResponse])
def get_ecological_data(
    territory_id: int,
    indicator: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(EcologicalMeasurement).filter(
        EcologicalMeasurement.territory_id == territory_id
    )
    if indicator:
        query = query.filter(EcologicalMeasurement.indicator_type == indicator)
    data = query.order_by(EcologicalMeasurement.measured_at).all()
    if not data:
        raise HTTPException(status_code=404, detail="Даних не знайдено")
    return data