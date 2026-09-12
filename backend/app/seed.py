from sqlalchemy import func, select

from app.database import Database
from app.models import BusinessSettings, Category, Product

DEMO_CATALOG = {
    "Favoritos": [
        ("Casado con pollo", "Arroz, frijoles, ensalada, plátano maduro y pollo.", 420000, "🍛"),
        ("Hamburguesa de la casa", "Carne, queso, lechuga y nuestra salsa especial.", 350000, "🍔"),
        ("Papas crujientes", "Papas doradas recién hechas.", 150000, "🍟"),
    ],
    "Desayunos": [
        ("Gallo pinto", "Con huevos, natilla, plátano maduro y tortillas.", 280000, "🍳"),
        ("Tortilla con queso", "Tortilla palmeada, queso y natilla.", 180000, "🫓"),
    ],
    "Bebidas": [
        ("Fresco de cas", "Natural, frío y preparado en casa.", 100000, "🥤"),
        ("Café chorreado", "Una taza de café costarricense.", 90000, "☕"),
    ],
}


def initialize_business(database: Database):
    with database.write() as session:
        if not session.get(BusinessSettings, 1):
            session.add(
                BusinessSettings(
                    id=1,
                    name="Mi Soda",
                    tagline="Hecho aquí. Servido con cariño.",
                    sinpe_phone="",
                    phone="",
                    address="",
                )
            )


def seed_demo_catalog(database: Database):
    with database.write() as session:
        if session.scalar(select(func.count()).select_from(Product)):
            return False
        for category_name, products in DEMO_CATALOG.items():
            category = session.scalar(select(Category).where(Category.name == category_name))
            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.flush()
            for name, description, price, icon in products:
                session.add(
                    Product(
                        category_id=category.id,
                        name=name,
                        description=description,
                        price_cents=price,
                        icon=icon,
                        available=True,
                    )
                )
        return True
