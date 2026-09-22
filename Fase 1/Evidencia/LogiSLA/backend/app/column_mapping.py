"""
Mapeo automático de columnas para archivos de envíos subidos por el usuario.

El objetivo Sprint 1 es: "Implementar la ingesta y el mapeo automático de
columnas para archivos CSV/Excel de envíos masivos". Las empresas no van a
subir archivos con nombres de columna estandarizados (una dice "N° Guía",
otra "numero_guia", otra "Tracking"), así que esta función intenta
reconocer las columnas requeridas por similitud de nombre.

Es una función pura (no toca la BD ni el archivo) para que sea fácil de
testear con muchos casos de headers reales sin necesitar pandas ni un
archivo físico.
"""
import re
from dataclasses import dataclass, field

# Campos que el modelo de datos necesita sí o sí para poder auditar el envío.
REQUIRED_FIELDS = ["guide_number", "carrier_name", "dispatch_date"]

# Campos que enriquecen la auditoría pero no son obligatorios para ingestar.
OPTIONAL_FIELDS = ["delivery_date", "destination", "declared_value"]

# Sinónimos conocidos por campo. Todo en minúsculas y sin acentos/espacios
# raros — la normalización pasa el header por _normalize() antes de comparar.
SYNONYMS = {
    "guide_number": [
        "guia", "nguia", "numeroguia", "nrodeguia", "tracking",
        "trackingnumber", "numeroenvio", "nenvio", "codigoenvio", "guide",
        "waybill", "ordennumero",
    ],
    "carrier_name": [
        "transportista", "carrier", "courier", "empresadetransporte",
        "operadorlogistico", "operador",
    ],
    "dispatch_date": [
        "fechadespacho", "fechaenvio", "fechasalida", "dispatchdate",
        "shipdate", "fecharetiro",
    ],
    "delivery_date": [
        "fechaentrega", "deliverydate", "fecharecepcion", "fecharecibido",
        "fechacierre",
    ],
    "destination": [
        "destino", "destination", "ciudaddestino", "comunadestino",
        "direcciondestino",
    ],
    "declared_value": [
        "valordeclarado", "declaredvalue", "montoenvio", "valorenvio",
        "montodeclarado",
    ],
}

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


_STOPWORDS = {"de", "del", "la", "el", "los", "las", "n"}


def _normalize(header: str) -> str:
    """
    'Numero de Guia' -> 'numeroguia'. Minúsculas, sin acentos, sin
    conectores ("de", "del"...) y sin caracteres no alfanuméricos, para
    que headers redactados de forma distinta pero equivalentes matcheen
    igual (ej. "N° de Guía" y "Numero Guia").
    """
    h = header.strip().lower()
    accents = str.maketrans("áéíóúñ", "aeioun")
    h = h.translate(accents)
    words = re.findall(r"[a-z0-9]+", h)
    words = [w for w in words if w not in _STOPWORDS]
    return "".join(words)


@dataclass
class MappingResult:
    mapping: dict = field(default_factory=dict)      # {campo_interno: header_original}
    unmapped_required: list = field(default_factory=list)  # campos obligatorios sin match
    ambiguous: dict = field(default_factory=dict)     # campo: [headers candidatos] si hubo >1 match

    @property
    def is_valid(self) -> bool:
        """True si se pudo mapear todo lo obligatorio para poder ingestar el archivo."""
        return len(self.unmapped_required) == 0


def map_columns(headers: list[str]) -> MappingResult:
    """
    Dada la lista de headers tal como vienen en el archivo, devuelve el
    mapeo campo_interno -> header_original, más advertencias de lo que no
    se pudo mapear automáticamente (para que el frontend pida confirmación
    manual antes de ingestar).
    """
    result = MappingResult()
    normalized_headers = {_normalize(h): h for h in headers}

    for field_name in ALL_FIELDS:
        candidates = [normalized_headers[field_name]] if field_name in normalized_headers else []
        # match directo por nombre de campo (ej. header ya viene como "guide_number")
        if field_name in normalized_headers:
            candidates = [normalized_headers[field_name]]
        else:
            candidates = [
                normalized_headers[norm]
                for syn in SYNONYMS.get(field_name, [])
                for norm in [_normalize(syn)]
                if norm in normalized_headers
            ]
            # dedup preservando orden
            seen = set()
            candidates = [c for c in candidates if not (c in seen or seen.add(c))]

        if len(candidates) == 1:
            result.mapping[field_name] = candidates[0]
        elif len(candidates) > 1:
            result.ambiguous[field_name] = candidates
            # usamos el primero como mejor esfuerzo, pero queda registrado como ambiguo
            result.mapping[field_name] = candidates[0]
        elif field_name in REQUIRED_FIELDS:
            result.unmapped_required.append(field_name)

    return result
