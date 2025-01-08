from fastapi import APIRouter, Depends, Path, HTTPException, status  # Doğru status modülünü import ettik
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Base, ToCook
from database import engine, SessionLocal  # Veritabanı bağlantısı
from typing import Annotated
from routers.auth import get_current_user

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
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/")
async def read_all(user:user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(ToCook).filter(ToCook.owner_id == user["id"]).all()       #tüm verileri getirir

@router.get("/tocook/{tocook_id}",status_code=status.HTTP_200_OK)
async def get_by_id(user:user_dependency, db: db_dependency, tocook_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    tocook = db.query(ToCook).filter(ToCook.id == tocook_id).filter(ToCook.owner_id == user["id"]).first()
    if tocook is not None:
        return tocook
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

@router.post("/tocook",status_code=status.HTTP_201_CREATED)
async def create(user:user_dependency,db: db_dependency, toCook_Request: toCookRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    toCook = ToCook(**toCook_Request.dict(),owner_id = user.get('id'))
    db.add(toCook)
    db.commit()


@router.put("/tocook/{toCook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update(user:user_dependency,
        db: db_dependency,
        toCook_Request: toCookRequest,
        toCook_id: int = Path(gt=0)):
    # Verilen ID'ye sahip kaydı sorgula
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    toCook = db.query(ToCook).filter(ToCook.id == toCook_id).filter(ToCook.owner_id == user.get('id')).first()
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
@router.delete("/tocook/{toCook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(user: user_dependency,db: db_dependency, toCook_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    toCook = db.query(ToCook).filter(ToCook.id == toCook_id).filter(ToCook.owner_id == user.get('id')).first()
    if toCook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="To Cook not found"
        )
    #db.query(ToCook).filter(ToCook.id == toCook_id).delete()   #emin olmak için
    db.delete(toCook)
    db.commit()

