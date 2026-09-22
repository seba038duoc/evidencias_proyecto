"""Punto de entrada de la API LogiSLA."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import audit_batches

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Crea las tablas si no existen, al levantar el server real. En tests
    esto NO corre contra Postgres: los tests arman su propia BD SQLite en
    conftest.py, así que un error de conexión acá solo se registra como
    warning y no tumba la app. En producción (Sprint 4) esto se reemplaza
    por migraciones Alembic para tener control de versiones del esquema.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo conectar a la base de datos al iniciar: %s", exc)
    yield


app = FastAPI(
    title="LogiSLA API",
    description="Auditoría inteligente de SLA de transporte",
    version="0.1.0",
    lifespan=lifespan,
)

# El frontend (Next.js) corre en otro origen (localhost:3000 en dev, otro
# dominio en Cloud Run/Vercel en el Sprint 4), así que el navegador
# necesita estos headers CORS o bloquea las llamadas fetch(). En dev
# dejamos localhost:3000/3001 fijos; ALLOWED_ORIGINS permite agregar el
# dominio real de producción sin tocar código.
default_origins = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_batches.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
