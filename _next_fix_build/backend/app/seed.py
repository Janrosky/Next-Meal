from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.database import Database
from app.models import Business, Customer, Ticket


def initialize_demo(database: Database):
    with database.sessions() as session:
        if session.get(Business, 1) is None:
            session.add(Business(id=1, name="Next-Fix Studio", phone="+506 2222-3344", address="San José, Costa Rica"))
        if session.scalar(select(func.count(Customer.id))) == 0:
            customers = [
                Customer(name="María Fernández", phone="8888-2140", email="maria@example.com"),
                Customer(name="Carlos Jiménez", phone="8702-9912", email="carlos@example.com"),
                Customer(name="Ana Rodríguez", phone="8311-4500", email="ana@example.com"),
                Customer(name="Luis Vargas", phone="7044-1932", email="luis@example.com"),
                Customer(name="Sofía Herrera", phone="6122-8041", email="sofia@example.com"),
                Customer(name="Diego Mora", phone="8817-6632", email="diego@example.com"),
            ]
            session.add_all(customers)
            session.flush()
            now = datetime.now(UTC)
            rows = [
                (0, "Automóvil", "Toyota", "Corolla 2018", "BCT-482", "Ruido metálico al frenar y vibración en el volante.", "diagnosing", "high", "Marco", 2400000, 850000, 2),
                (1, "Celular", "Apple", "iPhone 14 Pro", "IMEI-88421", "Pantalla quebrada, táctil funciona parcialmente.", "approval", "normal", "Sofía", 3500000, 7200000, 1),
                (2, "Electrodoméstico", "Samsung", "Lavadora WA17", "SN-340099", "No completa el ciclo de centrifugado.", "repairing", "urgent", "Marco", 1850000, 3200000, 3),
                (3, "Computadora", "Lenovo", "ThinkPad T14", "PF-44K90", "Se apaga al conectar el cargador.", "received", "normal", "Andrea", 0, 0, 0),
                (4, "Bicicleta", "Trek", "Marlin 7", "TRK-9912", "Cambio trasero salta bajo carga.", "ready", "normal", "Diego", 1200000, 1800000, 4),
                (5, "Automóvil", "Hyundai", "Tucson 2020", "BZM-117", "Aire acondicionado no enfría.", "repairing", "high", "Marco", 4000000, 7500000, 2),
            ]
            for index, row in enumerate(rows, 1):
                customer_index, asset, brand, model, serial, issue, status, priority, tech, labor, parts, days = row
                session.add(Ticket(code=f"NF-2026-{index:04d}", customer_id=customers[customer_index].id, asset_type=asset, brand=brand, model=model, serial_number=serial, issue=issue, status=status, priority=priority, assigned_to=tech, labor_cents=labor, parts_cents=parts, paid_cents=0, estimated_at=now + timedelta(days=days) if days else None, created_at=now - timedelta(days=index), updated_at=now - timedelta(hours=index * 2)))
        session.commit()
