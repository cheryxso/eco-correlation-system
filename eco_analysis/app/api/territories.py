from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import asyncio
from app.core.database import get_db
from app.models.territory import Territory
from app.schemas.territory import TerritoryCreate, TerritoryResponse

router = APIRouter(prefix="/territories", tags=["Території"])


@router.post("/", response_model=TerritoryResponse)
def create_territory(data: TerritoryCreate, db: Session = Depends(get_db)):
    territory = Territory(**data.model_dump())
    db.add(territory)
    db.commit()
    db.refresh(territory)
    return territory


@router.get("/", response_model=List[TerritoryResponse])
def get_territories(db: Session = Depends(get_db)):
    return db.query(Territory).all()


@router.get("/public/stats")
def get_public_stats(db: Session = Depends(get_db)):
    from app.models.ecological import EcologicalMeasurement
    from app.models.economic import EconomicMeasurement

    territories_count = db.query(Territory).count()
    eco_count = db.query(EcologicalMeasurement).count()
    econ_count = db.query(EconomicMeasurement).count()
    territories = db.query(Territory).all()

    return {
        "territories_count": territories_count,
        "ecological_measurements_count": eco_count,
        "economic_measurements_count": econ_count,
        "territories": [
            {
                "id": t.id, "name": t.name, "region": t.region,
                "latitude": t.latitude, "longitude": t.longitude
            }
            for t in territories
        ]
    }


@router.post("/fix-regions")
async def fix_all_regions(db: Session = Depends(get_db)):
    import httpx
    fixed = 0
    skipped = 0
    errors = []

    territories = db.query(Territory).all()

    async with httpx.AsyncClient() as client:
        for t in territories:
            if "область" in (t.region or "").lower():
                skipped += 1
                continue

            try:
                await asyncio.sleep(0.5)

                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": f"{t.name}, Ukraine",
                        "format": "json",
                        "limit": 1,
                        "accept-language": "uk"
                    },
                    headers={"User-Agent": "eco-analysis-system/1.0"},
                    timeout=8.0
                )
                results = response.json()
                if results:
                    display = results[0].get("display_name", "")
                    parts = display.split(",")
                    oblast = next(
                        (p.strip() for p in parts if "область" in p.lower()),
                        None
                    )
                    if oblast:
                        t.region = oblast
                        fixed += 1
                    else:
                        errors.append(f"{t.name}: область не знайдена в {display[:80]}")
                else:
                    errors.append(f"{t.name}: місто не знайдено в Nominatim")

            except Exception as e:
                errors.append(f"{t.name}: {str(e)}")
                continue

    db.commit()

    return {
        "fixed": fixed,
        "skipped_already_correct": skipped,
        "total": len(territories),
        "errors": errors
    }


@router.get("/{territory_id}", response_model=TerritoryResponse)
def get_territory(territory_id: int, db: Session = Depends(get_db)):
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Територію не знайдено")
    return territory


@router.delete("/{territory_id}")
def delete_territory(territory_id: int, db: Session = Depends(get_db)):
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Територію не знайдено")
    db.delete(territory)
    db.commit()
    return {"message": "Територію видалено"}


@router.put("/{territory_id}", response_model=TerritoryResponse)
def update_territory(territory_id: int, data: TerritoryCreate, db: Session = Depends(get_db)):
    territory = db.query(Territory).filter(Territory.id == territory_id).first()
    if not territory:
        raise HTTPException(status_code=404, detail="Територію не знайдено")
    territory.name = data.name
    territory.region = data.region
    territory.latitude = data.latitude
    territory.longitude = data.longitude
    db.commit()
    db.refresh(territory)
    return territory