from sqlalchemy import select

from app.database import Database
from app.domain import BusinessError, Principal
from app.models import Category, Product
from app.schemas import CategoryInput, ProductInput
from app.services.audit import record
from app.services.media import check_image


def product_view(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "price_cents": product.price_cents,
        "available": product.available,
        "icon": product.icon,
        "image_url": product.image_url,
        "featured": product.featured,
        "sort_order": product.sort_order,
        "allergens": product.allergens,
        "cabys": product.cabys,
    }


class CatalogService:
    def __init__(self, database: Database):
        self.database = database

    def list(self, include_unavailable: bool = False) -> dict:
        with self.database.read() as session:
            query = select(Product).order_by(
                Product.featured.desc(), Product.sort_order, Product.name
            )
            if not include_unavailable:
                query = query.where(Product.available.is_(True))
            return {
                "categories": [
                    {"id": c.id, "name": c.name, "sort_order": c.sort_order}
                    for c in session.scalars(
                        select(Category).order_by(Category.sort_order, Category.name)
                    )
                ],
                "products": [product_view(p) for p in session.scalars(query)],
            }

    def save_category(self, data: CategoryInput, actor: Principal, category_id: int | None):
        with self.database.write() as session:
            name = data.name.strip()
            existing = session.scalar(select(Category).where(Category.name == name))
            if existing and existing.id != category_id:
                raise BusinessError("Ya existe una categoría con ese nombre.", 409)
            category = session.get(Category, category_id) if category_id else Category()
            if not category:
                raise BusinessError("Categoría no encontrada.", 404)
            category.name = name
            category.sort_order = data.sort_order
            session.add(category)
            session.flush()
            record(session, actor.id, "category.saved", category.id, name=name)
            return {"id": category.id, "name": category.name}

    def save_product(self, data: ProductInput, actor: Principal, product_id: int | None):
        check_image(self.database, data.image_url)
        with self.database.write() as session:
            if not session.get(Category, data.category_id):
                raise BusinessError("La categoría no existe.", 404)
            product = session.get(Product, product_id) if product_id else Product()
            if not product:
                raise BusinessError("Producto no encontrado.", 404)
            old_price = product.price_cents
            for key, value in data.model_dump().items():
                setattr(product, key, value)
            session.add(product)
            session.flush()
            record(
                session,
                actor.id,
                "product.saved",
                product.id,
                old_price_cents=old_price,
                new_price_cents=product.price_cents,
                available=product.available,
                name=product.name,
            )
            return product_view(product)
