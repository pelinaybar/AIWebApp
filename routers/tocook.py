from fastapi import APIRouter, Depends, Path, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from ..models import Base, ToCook
from ..database import engine, SessionLocal
from typing import Annotated
from ..routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown
from bs4 import BeautifulSoup

router = APIRouter(
    prefix="/todo",
    tags=["ToCook"],
)

templates = Jinja2Templates(directory="templates")

class toCookRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=3, max_length=1500)
    priority: int = Field(gt=0, lt=6)
    completed: bool = Field(alias="complete")

def get_db():
    db = SessionLocal()
    try:
        yield db                            #yield birden fazla değer dönderebilir, return tek değer dönderir
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response

@router.get("/todo-page")
async def render_tocook_page(request: Request,db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        tocooks = db.query(ToCook).filter(ToCook.owner_id == user.get('id')).all()
        return templates.TemplateResponse("todo.html",{"request":request,"tocooks":tocooks,"user":user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_add_tocook_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html",{"request":request,"user":user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{toCook_id}")
async def render_edit_tocook_page(request: Request, toCook_id: int, db: db_dependency):
    user = await get_current_user(request.cookies.get('access_token'))
    if user is None:
        return redirect_to_login()

    tocook = db.query(ToCook).filter(ToCook.id == toCook_id).first()
    if not tocook:
        raise HTTPException(status_code=404, detail="Todo not found")

    return templates.TemplateResponse("edit-todo.html", {"request": request, "tocook": tocook, "user": user})


@router.get("/")
async def read_all(user:user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(ToCook).filter(ToCook.owner_id == user["id"]).all()       #tüm verileri getirir

@router.get("/todo/{toCook_id}",status_code=status.HTTP_200_OK)
async def get_by_id(user:user_dependency, db: db_dependency, toCook_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    tocook = db.query(ToCook).filter(ToCook.id == toCook_id).filter(ToCook.owner_id == user["id"]).first()
    if tocook is not None:
        return tocook
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create(user: user_dependency, db: db_dependency, toCook_Request: toCookRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    toCook = ToCook(**toCook_Request.dict(), owner_id=user.get('id'))
    toCook.description = create_tocook_with_gemini(toCook.description)
    db.add(toCook)
    db.commit()

    return toCook  # Yeni eklenen kaydı döndürmeyi düşünebilirsiniz



@router.put("/todo/{toCook_id}", status_code=status.HTTP_204_NO_CONTENT)
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
@router.delete("/todo/{toCook_id}", status_code=status.HTTP_204_NO_CONTENT)
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

def markdown_to_text(markdown_string):
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    return text

def create_tocook_with_gemini(tocook_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    response = llm.invoke(
        [
            HumanMessage(content="I will provide you a todo item to add my to do list. What i want you to do is to create longer and more comprehesive description of that todo item, my next message will be my todo:"),
            HumanMessage(content=tocook_string),
        ]
    )
    return markdown_to_text(response.content)

if __name__ == "__main__":
    print(create_tocook_with_gemini("buy milk"))