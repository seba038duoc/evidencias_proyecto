"""
Modelo relacional de LogiSLA (Sprint 1: Ingesta y Base Backend).

Tablas: companies, carriers, sla_rules, shipments, audit_batches — las
mismas mencionadas en la Fundamentación del proyecto (Modelado de Datos).

Alcance de este sprint: dejar la estructura y la ingesta funcionando.
Los campos que calcula el motor de auditoría (Sprint 2: is_sla_breached,
delay_business_hours, penalty_amount) quedan nulos hasta entonces —
por eso son nullable=True, no se calculan aquí.
"""
import enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey,
    Enum, JSON, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"        # archivo cargado, aún no auditado por el motor
    PROCESSING = "PROCESSING"  # el motor de auditoría (Sprint 2) lo está procesando
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Company(Base):
    """Empresa cliente que audita sus envíos (el usuario de LogiSLA)."""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    rut = Column(String(20), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    audit_batches = relationship("AuditBatch", back_populates="company")


class Carrier(Base):
    """Transportista (Chilexpress, Starken, etc.)."""
    __tablename__ = "carriers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sla_rules = relationship("SLARule", back_populates="carrier")
    shipments = relationship("Shipment", back_populates="carrier")


class SLARule(Base):
    """
    Regla contractual de SLA por transportista: cuántas horas hábiles
    tiene para entregar y qué multa aplica si se atrasa. El motor de
    auditoría (Sprint 2) usa esto para calcular incumplimientos.
    """
    __tablename__ = "sla_rules"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    carrier_id = Column(UUID(as_uuid=False), ForeignKey("carriers.id"), nullable=False)
    service_type = Column(String(100), nullable=True)  # ej. "Express", "Estándar"
    max_business_hours = Column(Integer, nullable=False)  # plazo comprometido en horas hábiles
    penalty_per_breach = Column(Float, nullable=False)  # monto fijo o % del flete, según defina el equipo
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    carrier = relationship("Carrier", back_populates="sla_rules")


class AuditBatch(Base):
    """
    Un lote de auditoría: representa un archivo CSV/Excel subido por el
    usuario. Nace en PENDING (Sprint 1) y el motor de auditoría (Sprint 2)
    lo procesa hasta COMPLETED.
    """
    __tablename__ = "audit_batches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING, nullable=False)
    total_rows = Column(Integer, nullable=False, default=0)
    # Mapeo de columnas detectado/confirmado (ver app/column_mapping.py),
    # se guarda para trazabilidad y para poder reprocesar el archivo.
    column_mapping = Column(JSON, nullable=True)
    unmapped_warnings = Column(JSON, nullable=True)
    # True cuando el mapeo automático no logró ubicar todas las columnas
    # obligatorias y el usuario lo confirmó/corrigió a mano (ver endpoint
    # /upload/confirm). Queda para trazabilidad: si muchos batches
    # terminan con manual_mapping=True, es señal de que el diccionario de
    # sinónimos en column_mapping.py necesita ampliarse.
    manual_mapping = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="audit_batches")
    shipments = relationship("Shipment", back_populates="audit_batch", cascade="all, delete-orphan")


class Shipment(Base):
    """
    Una guía de despacho individual dentro de un batch. Los campos de
    auditoría (is_sla_breached, delay_business_hours, penalty_amount)
    se calculan en el Sprint 2 y quedan en NULL hasta entonces.
    """
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    audit_batch_id = Column(UUID(as_uuid=False), ForeignKey("audit_batches.id"), nullable=False)
    carrier_id = Column(UUID(as_uuid=False), ForeignKey("carriers.id"), nullable=True)

    # Tal como viene del archivo, por si el carrier no matcheó a una fila existente.
    carrier_name_raw = Column(String(255), nullable=True)
    guide_number = Column(String(100), nullable=False)
    dispatch_date = Column(DateTime(timezone=True), nullable=False)
    delivery_date = Column(DateTime(timezone=True), nullable=True)  # NULL = aún no entregado
    destination = Column(String(255), nullable=True)
    declared_value = Column(Float, nullable=True)

    # --- Resultados del motor de auditoría (Sprint 2, no se llenan aquí) ---
    is_sla_breached = Column(Boolean, nullable=True)
    delay_business_hours = Column(Float, nullable=True)
    penalty_amount = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    audit_batch = relationship("AuditBatch", back_populates="shipments")
    carrier = relationship("Carrier", back_populates="shipments")
