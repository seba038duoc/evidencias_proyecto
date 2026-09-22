"""
Pruebas unitarias del mapeo automático de columnas.

Esto es justamente lo que antes vivía en el "Sprint de Calidad" separado;
ahora se escribe junto con la función que testea, dentro del Sprint 1.
Cubrimos casos reales de headers variados, no solo el caso feliz, porque
el objetivo es que LogiSLA acepte archivos de distintas empresas sin
que cada una tenga que adaptarse a un formato fijo.
"""
from app.column_mapping import map_columns, REQUIRED_FIELDS


def test_maps_standard_spanish_headers():
    headers = ["N° Guía", "Transportista", "Fecha Despacho", "Fecha Entrega", "Destino"]
    result = map_columns(headers)

    assert result.is_valid
    assert result.mapping["guide_number"] == "N° Guía"
    assert result.mapping["carrier_name"] == "Transportista"
    assert result.mapping["dispatch_date"] == "Fecha Despacho"
    assert result.mapping["delivery_date"] == "Fecha Entrega"
    assert result.mapping["destination"] == "Destino"


def test_maps_english_and_snake_case_headers():
    headers = ["tracking_number", "carrier", "ship_date", "delivery_date"]
    result = map_columns(headers)

    assert result.is_valid
    assert result.mapping["guide_number"] == "tracking_number"
    assert result.mapping["dispatch_date"] == "ship_date"


def test_reports_missing_required_fields():
    # Sin columna de transportista ni de fecha de despacho.
    headers = ["Numero de Guia", "Ciudad Destino"]
    result = map_columns(headers)

    assert not result.is_valid
    assert "carrier_name" in result.unmapped_required
    assert "dispatch_date" in result.unmapped_required
    # el campo que sí matcheó no debe reportarse como faltante
    assert "guide_number" not in result.unmapped_required


def test_optional_fields_are_not_required_to_be_valid():
    # Solo llegan los 3 campos obligatorios, sin destino ni valor declarado.
    headers = ["Guia", "Courier", "Fecha Despacho"]
    result = map_columns(headers)

    assert result.is_valid
    assert set(REQUIRED_FIELDS).issubset(result.mapping.keys())
    assert "destination" not in result.mapping
    assert "declared_value" not in result.mapping


def test_is_case_and_accent_insensitive():
    headers = ["GUÍA", "TRANSPORTISTA", "FECHA DE DESPACHO".replace(" DE ", " ")]
    # variante con acentos, mayúsculas y espacios irregulares
    headers = ["  Guía  ", "TRANSPORTISTA", "fechadespacho"]
    result = map_columns(headers)

    assert result.is_valid


def test_empty_headers_reports_all_required_as_missing():
    result = map_columns([])
    assert not result.is_valid
    assert set(result.unmapped_required) == set(REQUIRED_FIELDS)
