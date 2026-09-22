"""Schemas Pydantic: forma de las respuestas de la API (no de los modelos de BD)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    batch_id: str
    filename: str
    status: str
    total_rows: int
    column_mapping: dict
    unmapped_warnings: list[str]
    ambiguous_warnings: dict[str, list[str]]
    message: str
    # Headers tal como vienen en el archivo. Cuando status == "MAPPING_FAILED",
    # el frontend usa esta lista para armar los selects de mapeo manual
    # (ver POST /upload/confirm) sin tener que volver a parsear el archivo.
    available_headers: list[str] = []


class AuditBatchOut(BaseModel):
    id: str
    filename: str
    status: str
    total_rows: int
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
