"""Pruebas de la lectura de la URL de la base de datos (app/config.py)."""

from app.config import normalizar_url_base_datos


def test_url_postgres_de_proveedores_en_la_nube_se_normaliza():
    url = "postgres://usuario:clave@ep-ejemplo.neon.tech/neondb?sslmode=require"
    assert normalizar_url_base_datos(url) == (
        "postgresql://usuario:clave@ep-ejemplo.neon.tech/neondb?sslmode=require"
    )


def test_otras_urls_no_cambian():
    for url in (
        "postgresql+psycopg2://logisla:logisla@localhost:5432/logisla",
        "postgresql://u:c@host/db",
        "sqlite:///./logisla.db",
    ):
        assert normalizar_url_base_datos(f"  {url}\n") == url
