from urllib.request import Request

from alembic.util import status
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status
from models import Base, ToCook
from database import engine
from routers.auth import router as auth_router
from routers.tocook import router as tocook_router

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name="static")

@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page",status_code=status.HTTP_302_FOUND)

app.include_router(auth_router)
app.include_router(tocook_router)

Base.metadata.create_all(bind=engine)      #bu satır veritanabını oluşturur.
