from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, JSONResponse
from starlette import status
from .models import Base, ToCook
from .database import engine
from .routers.auth import router as auth_router
from .routers.tocook import router as tocook_router
import os

app = FastAPI()

# Hata işleyici burada tanımlanır
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body,  # Gönderilen body'yi burada görebilirsiniz
        },
    )

script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir,"static/")

app.mount("/static",StaticFiles(directory=st_abs_file_path),name="static")

@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page",status_code=status.HTTP_302_FOUND)

app.include_router(auth_router)
app.include_router(tocook_router)

Base.metadata.create_all(bind=engine)
     #bu satır veritanabını oluşturur.
