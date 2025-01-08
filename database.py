from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Veritabanı bağlantı URL'si
SQLALCHEMY_DATABASE_URL = "sqlite:///./tocookaiapp.db"  # SQLite için
# Alternatif PostgreSQL URL'si:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

# 2. Veritabanı motorunu oluştur
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Session Maker oluştur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Declarative Base
Base = declarative_base()