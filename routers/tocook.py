from fastapi import APIRouter, Depends, Path, HTTPException, status  # Doğru status modülünü import ettik
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.testing.provision import drop_follower_db

from models import Base, ToCook
from database import engine, SessionLocal  # Veritabanı bağlantısı
from typing import Annotated

router = APIRouter(
    prefix="/tocook",
    tags=["ToCook"],
)

class toCookRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=3, max_length=1500)
    priority: int = Field(gt=0, lt=6)
    completed:(bool)

def get_db():
    db = SessionLocal()
    try:
        yield db                            #yield birden fazla değer dönderebilir, return tek değer dönderir
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(ToCook).all()           #tüm verileri getirir

@router.get("/get_by_id/{tocook_id}",status_code=status.HTTP_200_OK)
async def get_by_id(db: db_dependency, tocook_id: int = Path(gt=0)):
    tocook = db.query(ToCook).filter(ToCook.id == tocook_id).first()
    if tocook is not None:
        return tocook
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

@router.post("/create",status_code=status.HTTP_201_CREATED)
async def create(db: db_dependency, toCook_Request: toCookRequest):
    toCook = ToCook(**toCook_Request.dict())
    db.add(toCook)
    db.commit()


@router.put("/update/{toCook_id}", status_code=status.HTTP_202_ACCEPTED)
async def update(
        db: db_dependency,
        toCook_Request: toCookRequest,
        toCook_id: int = Path(gt=0)):
    # Verilen ID'ye sahip kaydı sorgula
    toCook = db.query(ToCook).filter(ToCook.id == toCook_id).first()
    if toCook is not None:
        # Güncellemeleri uygula
        toCook.title = toCook_Request.title
        toCook.description = toCook_Request.description
        toCook.priority = toCook_Request.priority
        toCook.completed = toCook_Request.completed
        # Değişiklikleri kaydet
        db.add(toCook)
        db.commit()
        # Güncellenmiş kaydı döndür
        return toCook
    # Kayıt bulunamazsa hata döndür
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
    )
@router.delete("/delete/{toCook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(db: db_dependency, toCook_id: int = Path(gt=0)):
    toCook = db.query(ToCook).filter(ToCook.id == toCook_id).first()
    if toCook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="To Cook not found"
        )
    #db.query(ToCook).filter(ToCook.id == toCook_id).delete()   #emin olmak için
    db.delete(toCook)
    db.commit()

