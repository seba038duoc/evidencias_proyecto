"""
Fixtures compartidas para los tests de integración.

Usamos SQLite en memoria en vez de levantar un Postgres real: es lo
suficientemente compatible para probar la lógica de la API sin depender
de infraestructura externa en CI. El motor de auditoría (Sprint 2) sí
deberá probarse contra Postgres si usa features específicas (por ahora
el modelo no las usa).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import Company
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_company(db_session):
    company = Company(name="Retail Demo SpA", rut="76.123.456-7")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company
