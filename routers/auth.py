from datetime import timedelta

from aiohttp import payload_type
from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY = "nfylsj08qes55s8rt1uv5ww92dtfbn50"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db                            #yield birden fazla değer dönderebilir, return tek değer dönderir
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str



def create_access_token(username:str,user_id:str,role:str, expires_delta:timedelta):
    payload = {'sub':username,'user_id':user_id,'role':role}
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({'exp':expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str,db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role
    )
    db.add(user)
    db.commit()

async def get_current_user(token: Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or username")
        return {'username':username,'id':user_id,'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")




@router.post("/token",response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    # authenticate_user fonksiyonundan dönen kullanıcı nesnesini kontrol ediyoruz
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:  # Eğer kullanıcı bulunamazsa veya şifre yanlışsa
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.username,user.id,user.role,timedelta(minutes=60)) # Token oluşturmayı burada ekleyeceksiniz
    return {"access_token": token, "token_type": "bearer"}
