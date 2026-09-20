"""Ordered SQLite upgrades; existing installations are never recreated."""

VERSION = 2

ADDITIONS_V2 = {
    "categories": {"sort_order": "INTEGER NOT NULL DEFAULT 0"},
    "products": {
        "image_url": "VARCHAR(100) NOT NULL DEFAULT ''",
        "featured": "BOOLEAN NOT NULL DEFAULT 0",
        "sort_order": "INTEGER NOT NULL DEFAULT 0",
        "allergens": "VARCHAR(300) NOT NULL DEFAULT ''",
        "cabys": "VARCHAR(13) NOT NULL DEFAULT ''",
    },
    "business_settings": {
        "logo_url": "VARCHAR(100) NOT NULL DEFAULT ''",
        "cover_url": "VARCHAR(100) NOT NULL DEFAULT ''",
        "primary_color": "VARCHAR(7) NOT NULL DEFAULT '#184c3b'",
        "accent_color": "VARCHAR(7) NOT NULL DEFAULT '#e99a53'",
        "background_color": "VARCHAR(7) NOT NULL DEFAULT '#f6f7f3'",
        "surface_color": "VARCHAR(7) NOT NULL DEFAULT '#ffffff'",
        "text_color": "VARCHAR(7) NOT NULL DEFAULT '#233b32'",
        "hero_title": "VARCHAR(100) NOT NULL DEFAULT 'Tu antojo, recién hecho.'",
        "receipt_footer": "VARCHAR(200) NOT NULL DEFAULT '¡Gracias por tu visita!'",
        "opening_hours": "VARCHAR(300) NOT NULL DEFAULT ''",
        "accepting_orders": "BOOLEAN NOT NULL DEFAULT 1",
        "closed_message": "VARCHAR(200) NOT NULL DEFAULT 'En este momento no recibimos pedidos.'",
    },
}


def upgrade_v2(connection):
    for table, columns in ADDITIONS_V2.items():
        existing = {row[1] for row in connection.exec_driver_sql(f'PRAGMA table_info("{table}")')}
        for name, definition in columns.items():
            if name not in existing:
                connection.exec_driver_sql(
                    f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}'
                )
