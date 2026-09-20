from pathlib import Path
from shutil import copyfile
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select

from app.database import Database
from app.models import BusinessSettings, Category, Product

DEMO_CATALOG = {
    "Favoritos": [
        ("Casado con pollo", "Arroz, frijoles, ensalada, plátano maduro y pollo.", 420000, "🍛"),
        ("Hamburguesa de la casa", "Carne, queso, lechuga y nuestra salsa especial.", 350000, "🍔"),
    ],
    "Desayunos": [
        ("Gallo pinto", "Con huevos, natilla, plátano maduro y tortillas.", 280000, "🍳"),
        ("Tortilla con queso", "Tortilla palmeada, queso y natilla.", 180000, "🫓"),
    ],
    "Bebidas": [
        ("Fresco de cas", "Natural, frío y preparado en casa.", 100000, "🥤"),
    ],
    "Cafetería": [
        ("Café chorreado", "Una taza de café costarricense.", 90000, "☕"),
    ],
    "Acompañamientos": [
        ("Papas crujientes", "Papas doradas recién hechas.", 150000, "🍟"),
    ],
    "Postres": [
        ("Queque de chocolate", "Porción de queque de chocolate con crema y caramelo.", 220000, "🍰"),
    ],
}

DEMO_PHOTOS = {
    "Casado con pollo": "casado",
    "Hamburguesa de la casa": "hamburguesa",
    "Papas crujientes": "papas",
    "Gallo pinto": "pinto",
    "Tortilla con queso": "tortilla",
    "Fresco de cas": "cas",
    "Café chorreado": "cafe",
    "Queque de chocolate": "queque",
}


def install_demo_photo(database: Database, name: str) -> str:
    slug = DEMO_PHOTOS[name]
    source = Path(__file__).parent / "assets" / "demo" / f"{slug}.webp"
    filename = uuid5(NAMESPACE_URL, f"soda-local/demo/v1/{slug}").hex + ".webp"
    target = database.path.parent / "media" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        staging = target.with_suffix(".tmp")
        try:
            copyfile(source, staging)
            staging.replace(target)
        finally:
            staging.unlink(missing_ok=True)
    return "/api/media/" + filename


def add_demo_photos(database: Database) -> int:
    """Explicit opt-in for existing demos; preserve edited items and custom photos."""
    changed = 0
    with database.write() as session:
        for products in DEMO_CATALOG.values():
            for name, description, price, icon in products:
                matches = session.scalars(
                    select(Product).where(
                        Product.name == name,
                        Product.description == description,
                        Product.price_cents == price,
                        Product.icon == icon,
                        Product.image_url == "",
                    )
                )
                for product in matches:
                    product.image_url = install_demo_photo(database, name)
                    changed += 1
    return changed


def refresh_demo_catalog(database: Database) -> int:
    """Explicitly replace demo items by name, keeping their IDs and sales history."""
    changed = 0
    with database.write() as session:
        for index, (category_name, products) in enumerate(DEMO_CATALOG.items()):
            category = session.scalar(select(Category).where(Category.name == category_name))
            if not category:
                category = Category(name=category_name, sort_order=index)
                session.add(category)
                session.flush()
            category.sort_order = index
            for name, description, price, icon in products:
                product = session.scalar(select(Product).where(Product.name == name))
                if not product:
                    product = Product(name=name, category_id=category.id, price_cents=price)
                    session.add(product)
                product.category_id = category.id
                product.description = description
                product.price_cents = price
                product.icon = icon
                product.image_url = install_demo_photo(database, name)
                product.available = True
                changed += 1
    return changed


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
        for index, (category_name, products) in enumerate(DEMO_CATALOG.items()):
            category = session.scalar(select(Category).where(Category.name == category_name))
            if not category:
                category = Category(name=category_name, sort_order=index)
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
                        image_url=install_demo_photo(database, name),
                        available=True,
                    )
                )
        return True
