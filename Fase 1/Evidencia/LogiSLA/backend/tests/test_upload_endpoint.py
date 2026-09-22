"""
Pruebas de integración de los endpoints de carga
(POST /api/v1/audit-batches/upload y /upload/confirm).

Cubren: carga exitosa con headers en español, rechazo de mapeo incompleto
sin tocar la BD, rechazo de formato de archivo no soportado, y el flujo
completo de confirmación manual de mapeo (MAPPING_FAILED -> /confirm).
"""
import io
import json

import pandas as pd


def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def test_upload_creates_batch_and_shipments(client, sample_company):
    df = pd.DataFrame({
        "N° Guía": ["G-001", "G-002", "G-003"],
        "Transportista": ["Chilexpress", "Starken", "Chilexpress"],
        "Fecha Despacho": ["2026-09-01", "2026-09-02", "2026-09-03"],
        "Fecha Entrega": ["2026-09-05", "2026-09-06", ""],
        "Destino": ["Santiago", "Valparaíso", "Concepción"],
    })

    response = client.post(
        f"/api/v1/audit-batches/upload?company_id={sample_company.id}",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["total_rows"] == 3
    assert body["batch_id"]
    assert body["column_mapping"]["guide_number"] == "N° Guía"

    # confirmar que quedó consultable
    get_response = client.get(f"/api/v1/audit-batches/{body['batch_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["total_rows"] == 3


def test_upload_with_missing_required_columns_does_not_create_batch(client, sample_company):
    df = pd.DataFrame({
        "Numero de Guia": ["G-001"],
        "Ciudad Destino": ["Santiago"],
        # sin transportista ni fecha de despacho
    })

    response = client.post(
        f"/api/v1/audit-batches/upload?company_id={sample_company.id}",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "MAPPING_FAILED"
    assert "carrier_name" in body["unmapped_warnings"]
    assert body["batch_id"] == ""
    # el frontend necesita los headers reales para armar el formulario manual
    assert set(body["available_headers"]) == {"Numero de Guia", "Ciudad Destino"}


def test_upload_rejects_unsupported_file_extension(client, sample_company):
    response = client.post(
        f"/api/v1/audit-batches/upload?company_id={sample_company.id}",
        files={"file": ("envios.txt", b"contenido", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_unknown_company(client):
    df = pd.DataFrame({
        "Guia": ["G-001"], "Courier": ["Chilexpress"], "Fecha Despacho": ["2026-09-01"],
    })
    response = client.post(
        "/api/v1/audit-batches/upload?company_id=no-existe",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
    )
    assert response.status_code == 404


# --- /upload/confirm: flujo completo de mapeo manual ------------------

def test_confirm_creates_batch_with_manual_mapping(client, sample_company):
    """
    Flujo real: /upload falla con headers que el auto-mapeo no reconoce
    ('Guía Despacho' en vez de 'guía'), el frontend arma el mapeo manual
    con los available_headers devueltos, y /upload/confirm lo persiste.
    """
    df = pd.DataFrame({
        "Codigo Interno": ["X-1", "X-2"],
        "Empresa de Reparto": ["Chilexpress", "Blue Express"],
        "Dia de Salida": ["2026-09-01", "2026-09-02"],
    })
    csv_bytes = _csv_bytes(df)

    first = client.post(
        f"/api/v1/audit-batches/upload?company_id={sample_company.id}",
        files={"file": ("envios_raros.csv", csv_bytes, "text/csv")},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["status"] == "MAPPING_FAILED"
    assert set(first_body["unmapped_warnings"]) == {"guide_number", "carrier_name", "dispatch_date"}

    manual_mapping = {
        "guide_number": "Codigo Interno",
        "carrier_name": "Empresa de Reparto",
        "dispatch_date": "Dia de Salida",
    }
    confirm = client.post(
        f"/api/v1/audit-batches/upload/confirm?company_id={sample_company.id}",
        files={"file": ("envios_raros.csv", csv_bytes, "text/csv")},
        data={"column_mapping": json.dumps(manual_mapping)},
    )

    assert confirm.status_code == 200
    body = confirm.json()
    assert body["status"] == "PENDING"
    assert body["total_rows"] == 2
    assert body["batch_id"]
    assert body["column_mapping"] == manual_mapping

    get_response = client.get(f"/api/v1/audit-batches/{body['batch_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["total_rows"] == 2


def test_confirm_rejects_incomplete_manual_mapping(client, sample_company):
    df = pd.DataFrame({"Codigo Interno": ["X-1"], "Empresa de Reparto": ["Chilexpress"]})
    response = client.post(
        f"/api/v1/audit-batches/upload/confirm?company_id={sample_company.id}",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
        # falta mapear dispatch_date
        data={"column_mapping": json.dumps({
            "guide_number": "Codigo Interno",
            "carrier_name": "Empresa de Reparto",
        })},
    )
    assert response.status_code == 400
    assert "dispatch_date" in response.json()["detail"]


def test_confirm_rejects_header_that_does_not_exist_in_file(client, sample_company):
    df = pd.DataFrame({"Codigo Interno": ["X-1"], "Empresa de Reparto": ["Chilexpress"], "Dia de Salida": ["2026-09-01"]})
    response = client.post(
        f"/api/v1/audit-batches/upload/confirm?company_id={sample_company.id}",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
        data={"column_mapping": json.dumps({
            "guide_number": "Columna Que No Existe",
            "carrier_name": "Empresa de Reparto",
            "dispatch_date": "Dia de Salida",
        })},
    )
    assert response.status_code == 400
    assert "Columna Que No Existe" in response.json()["detail"]


def test_confirm_rejects_invalid_json(client, sample_company):
    df = pd.DataFrame({"Codigo Interno": ["X-1"]})
    response = client.post(
        f"/api/v1/audit-batches/upload/confirm?company_id={sample_company.id}",
        files={"file": ("envios.csv", _csv_bytes(df), "text/csv")},
        data={"column_mapping": "esto no es json"},
    )
    assert response.status_code == 400
