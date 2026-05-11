from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets
from app.core.database import get_db
from app.models.invite import InviteCode
from app.models.user import UserRole

router = APIRouter(prefix="/invites", tags=["Інвайт-коди"])

class InviteCreate(BaseModel):
    role: UserRole
    expires_in_days: Optional[int] = 7

class InviteResponse(BaseModel):
    id: int
    code: str
    role: UserRole
    is_used: bool
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/generate", response_model=InviteResponse)
def generate_invite(data: InviteCreate, db: Session = Depends(get_db)):
    prefix = data.role.value.upper()
    code = f"{prefix}-{secrets.token_urlsafe(8)}"
    expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)

    invite = InviteCode(
        code=code,
        role=data.role,
        expires_at=expires_at
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite

@router.get("/", response_model=list[InviteResponse])
def get_invites(db: Session = Depends(get_db)):
    return db.query(InviteCode).all()

@router.delete("/{invite_id}")
def delete_invite(invite_id: int, db: Session = Depends(get_db)):
    invite = db.query(InviteCode).filter(InviteCode.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Код не знайдено")
    db.delete(invite)
    db.commit()
    return {"message": "Код видалено"}