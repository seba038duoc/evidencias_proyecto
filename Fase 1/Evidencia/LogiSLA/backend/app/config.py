"""
Configuración de la aplicación LogiSLA.

Lee la conexión a la base de datos desde una variable de entorno para no
hardcodear credenciales. En desarrollo local, usar el docker-compose.yml
incluido (levanta un Postgres en localhost:5432) y copiar .env.example a .env.
"""
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://logisla:logisla@localhost:5432/logisla",
)

# Tamaño máximo de archivo aceptado en la carga masiva (MB). El enunciado
# habla de archivos de 10.000+ filas; 25 MB cubre eso con margen para CSV/XLSX.
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
