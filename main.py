from fastapi import FastAPI
from models import Base, ToCook
from database import engine
from routers.auth import router as auth_router
from routers.tocook import router as tocook_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(tocook_router)

Base.metadata.create_all(bind=engine)      #bu satır veritanabını oluşturur.
