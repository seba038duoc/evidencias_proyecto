"""
Crea una Company de prueba y devuelve su ID, para poder probar la carga
sin tener aún un endpoint/login de gestión de empresas (queda para otro
sprint). Uso:

    python scripts/seed_pilot_company.py
    # o con nombre propio:
    python scripts/seed_pilot_company.py "Mi Empresa Piloto" "76.111.222-3"
"""
import sys

from app.database import SessionLocal
from app.models import Company

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Retail Piloto SpA"
    rut = sys.argv[2] if len(sys.argv) > 2 else None

    db = SessionLocal()
    company = Company(name=name, rut=rut)
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"company_id={company.id}")
    db.close()
