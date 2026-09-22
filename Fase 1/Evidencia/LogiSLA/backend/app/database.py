"""
Configuración de SQLAlchemy: engine, sesión y Base declarativa.

get_db() se usa como dependencia de FastAPI para inyectar una sesión por
request y garantizar que siempre se cierre, incluso si la request falla.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# pool_pre_ping evita errores por conexiones muertas cuando Cloud SQL
# recicla conexiones inactivas (relevante para el Sprint 4 en GCP).
#
# check_same_thread=False solo aplica si DATABASE_URL es SQLite (útil para
# correr una demo local rápida sin instalar Postgres): SQLite por defecto
# no permite usar una conexión desde un thread distinto al que la abrió,
# y FastAPI atiende cada request en su propio thread.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
