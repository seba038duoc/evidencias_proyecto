"""
Endpoints de ingesta (Sprint 1).

POST /api/v1/audit-batches/upload
    Recibe un CSV/Excel, detecta la empresa (por ahora vía query param
    company_id — el login/auth de empresas es de otro sprint), mapea
    columnas automáticamente, y si el mapeo es válido crea el AuditBatch
    y los Shipment en estado "sin auditar" (a la espera del motor del
    Sprint 2). Si el mapeo automático no logra ubicar las columnas
    obligatorias, devuelve el detalle (incluyendo los headers reales del
    archivo) SIN tocar la base de datos, para que el frontend arme un
    formulario de mapeo manual y llame a /upload/confirm.

POST /api/v1/audit-batches/upload/confirm
    Igual que /upload, pero el mapeo lo entrega el usuario a mano (typ.
    después de que /upload devolvió MAPPING_FAILED). Valida que estén
    todos los campos obligatorios y que cada header mapeado exista
    realmente en el archivo antes de crear el batch.

GET /api/v1/audit-batches/{batch_id}
    Consulta de estado de un batch ya cargado.
"""
import io
import json

import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.column_mapping import map_columns, REQUIRED_FIELDS, ALL_FIELDS
from app.models import AuditBatch, Shipment, BatchStatus, Company
from app.schemas import UploadResponse, AuditBatchOut

router = APIRouter(prefix="/api/v1/audit-batches", tags=["audit-batches"])

ACCEPTED_EXTENSIONS = (".csv", ".xlsx", ".xls")


def _read_dataframe(filename: str, raw_bytes: bytes) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        # sep=None + engine="python" detecta automáticamente , vs ; (común en
        # exports de Excel en configuración regional chilena).
        return pd.read_csv(io.BytesIO(raw_bytes), sep=None, engine="python")
    return pd.read_excel(io.BytesIO(raw_bytes))


def _get_company_or_404(db: Session, company_id: str) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="company_id no existe")
    return company


def _load_upload_or_400(filename: str, raw_bytes: bytes) -> pd.DataFrame:
    if not filename.lower().endswith(ACCEPTED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Usa {ACCEPTED_EXTENSIONS}")
    try:
        df = _read_dataframe(filename, raw_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {exc}")
    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo no tiene filas de datos")
    return df


def _persist_batch(
    db: Session,
    company_id: str,
    filename: str,
    df: pd.DataFrame,
    mapping: dict,
    manual_mapping: bool,
) -> AuditBatch:
    """
    Crea el AuditBatch y sus Shipment a partir de un mapeo ya validado
    (automático o confirmado a mano). Compartido por /upload y
    /upload/confirm para no duplicar la lógica de inserción.
    """
    batch = AuditBatch(
        company_id=company_id,
        filename=filename,
        status=BatchStatus.PENDING,
        total_rows=len(df),
        column_mapping=mapping,
        manual_mapping=manual_mapping,
    )
    db.add(batch)
    db.flush()  # para tener batch.id antes del commit

    shipments = []
    for _, row in df.iterrows():
        shipments.append(Shipment(
            audit_batch_id=batch.id,
            carrier_name_raw=str(row.get(mapping.get("carrier_name"), "")).strip() or None,
            guide_number=str(row[mapping["guide_number"]]).strip(),
            dispatch_date=pd.to_datetime(row[mapping["dispatch_date"]]),
            delivery_date=(
                pd.to_datetime(row[mapping["delivery_date"]])
                if "delivery_date" in mapping and pd.notna(row.get(mapping["delivery_date"]))
                else None
            ),
            destination=(
                str(row.get(mapping["destination"], "")).strip() or None
                if "destination" in mapping else None
            ),
            declared_value=(
                float(row[mapping["declared_value"]])
                if "declared_value" in mapping and pd.notna(row.get(mapping["declared_value"]))
                else None
            ),
        ))
    db.bulk_save_objects(shipments)
    db.commit()
    db.refresh(batch)
    return batch


@router.post("/upload", response_model=UploadResponse)
async def upload_audit_batch(
    company_id: str = Query(..., description="ID de la empresa dueña del batch"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _get_company_or_404(db, company_id)
    raw_bytes = await file.read()
    df = _load_upload_or_400(file.filename, raw_bytes)

    mapping_result = map_columns(list(df.columns))

    if not mapping_result.is_valid:
        # No tocamos la BD: devolvemos el diagnóstico (incluyendo los
        # headers reales) para que el frontend arme el formulario de
        # mapeo manual y llame a /upload/confirm con el mismo archivo.
        missing = ", ".join(mapping_result.unmapped_required)
        return UploadResponse(
            batch_id="",
            filename=file.filename,
            status="MAPPING_FAILED",
            total_rows=len(df),
            column_mapping=mapping_result.mapping,
            unmapped_warnings=mapping_result.unmapped_required,
            ambiguous_warnings=mapping_result.ambiguous,
            available_headers=list(df.columns),
            message=(
                f"No se pudieron mapear automáticamente las columnas obligatorias: {missing}. "
                "Confirma el mapeo manualmente en /upload/confirm."
            ),
        )

    batch = _persist_batch(db, company_id, file.filename, df, mapping_result.mapping, manual_mapping=False)

    return UploadResponse(
        batch_id=batch.id,
        filename=batch.filename,
        status=batch.status.value,
        total_rows=batch.total_rows,
        column_mapping=mapping_result.mapping,
        unmapped_warnings=[],
        ambiguous_warnings=mapping_result.ambiguous,
        message=f"Batch creado con {batch.total_rows} guías. Pendiente de auditoría (Sprint 2).",
    )


@router.post("/upload/confirm", response_model=UploadResponse)
async def confirm_audit_batch_mapping(
    company_id: str = Query(..., description="ID de la empresa dueña del batch"),
    file: UploadFile = File(..., description="El mismo archivo que se intentó subir en /upload"),
    column_mapping: str = Form(
        ...,
        description=(
            'JSON {"campo_interno": "header_del_archivo"} para los campos '
            'obligatorios (guide_number, carrier_name, dispatch_date) y, '
            'opcionalmente, delivery_date / destination / declared_value.'
        ),
    ),
    db: Session = Depends(get_db),
):
    _get_company_or_404(db, company_id)
    raw_bytes = await file.read()
    df = _load_upload_or_400(file.filename, raw_bytes)

    try:
        mapping = json.loads(column_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="column_mapping no es JSON válido")

    if not isinstance(mapping, dict):
        raise HTTPException(status_code=400, detail="column_mapping debe ser un objeto JSON")

    unknown_fields = set(mapping.keys()) - set(ALL_FIELDS)
    if unknown_fields:
        raise HTTPException(status_code=400, detail=f"Campos desconocidos en column_mapping: {sorted(unknown_fields)}")

    missing_required = [f for f in REQUIRED_FIELDS if f not in mapping or not mapping[f]]
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan campos obligatorios en column_mapping: {missing_required}",
        )

    unknown_headers = [h for h in mapping.values() if h not in df.columns]
    if unknown_headers:
        raise HTTPException(
            status_code=400,
            detail=f"Estos headers no existen en el archivo: {unknown_headers}. Headers disponibles: {list(df.columns)}",
        )

    batch = _persist_batch(db, company_id, file.filename, df, mapping, manual_mapping=True)

    return UploadResponse(
        batch_id=batch.id,
        filename=batch.filename,
        status=batch.status.value,
        total_rows=batch.total_rows,
        column_mapping=mapping,
        unmapped_warnings=[],
        ambiguous_warnings={},
        message=f"Batch creado con {batch.total_rows} guías a partir de un mapeo confirmado manualmente.",
    )


@router.get("/{batch_id}", response_model=AuditBatchOut)
def get_audit_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.query(AuditBatch).filter(AuditBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return batch
