import argparse
import getpass
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.config import Settings
from app.database import Database
from app.domain import BusinessError, Role
from app.models import User
from app.schemas import UserInput
from app.seed import add_demo_photos, initialize_business, refresh_demo_catalog, seed_demo_catalog
from app.services.business import COSTA_RICA
from app.services.employees import EmployeeService


def main():
    parser = argparse.ArgumentParser(description="Administración local de SodaLocal")
    subcommands = parser.add_subparsers(dest="command", required=True)
    init = subcommands.add_parser("init", help="Crear el primer administrador")
    init.add_argument("--demo", action="store_true", help="Agregar un menú de ejemplo")
    backup = subcommands.add_parser("backup", help="Respaldar SQLite de forma consistente")
    backup.add_argument("--output", type=Path)
    subcommands.add_parser("demo-images", help="Agregar fotos a productos de ejemplo sin modificar")
    subcommands.add_parser(
        "demo-refresh", help="Reemplazar fotos y datos de productos demo por nombre y ampliar categorías"
    )
    args = parser.parse_args()
    database = Database(Settings.from_environment().database_path)
    database.initialize()
    initialize_business(database)
    try:
        if args.command == "init":
            with database.read() as session:
                users = session.scalar(select(func.count()).select_from(User))
            if not users:
                username = input("Usuario administrador [admin]: ").strip() or "admin"
                password = getpass.getpass("Contraseña: ")
                if not password:
                    raise BusinessError("Escribí una contraseña.")
                if password != getpass.getpass("Repetir contraseña: "):
                    raise BusinessError("Las contraseñas no coinciden.")
                EmployeeService(database).create(
                    UserInput(username=username, password=password, role=Role.ADMIN)
                )
                print("Administrador creado.")
            else:
                print("Ya hay usuarios. Administralos desde la aplicación.")
            if args.demo:
                seeded = seed_demo_catalog(database)
                print("Menú de ejemplo creado." if seeded else "El catálogo ya contiene productos.")
        elif args.command == "demo-images":
            print(f"Fotografías agregadas: {add_demo_photos(database)}")
        elif args.command == "demo-refresh":
            print(f"Productos de ejemplo actualizados: {refresh_demo_catalog(database)}")
        else:
            target = args.output or database.path.parent / "backups" / (
                "manual-" + datetime.now(COSTA_RICA).strftime("%Y%m%d-%H%M%S") + ".sqlite3"
            )
            database.backup(target)
            print(f"Respaldo guardado: {target.resolve()}")
    finally:
        database.close()


if __name__ == "__main__":
    main()
