from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.dataset import Dataset

router = APIRouter(prefix="/datasets", tags=["Датасети"])

class DatasetCreate(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=DatasetResponse)
def create_dataset(data: DatasetCreate, db: Session = Depends(get_db)):
    dataset = Dataset(
        user_id=data.user_id,
        name=data.name,
        description=data.description
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("/", response_model=List[DatasetResponse])
def get_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).all()

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не знайдено")
    return dataset

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не знайдено")
    db.delete(dataset)
    db.commit()
    return {"message": "Датасет видалено"}