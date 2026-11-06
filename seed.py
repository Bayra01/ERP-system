"""Demo ugugdul: python seed.py   (aguulah burtgeltei bol yu ch hiihgui)

Hereglegchid (nuuts ug = <role>123): dispatcher, warehouse, driver, accountant.
"""
from decimal import Decimal

from sqlalchemy import select

from core.database import Base, SessionLocal, engine
from core.registry import import_all_models

import_all_models()

from modules.auth.backend.models import User  # noqa: E402
from modules.auth.backend.service import create_user, ensure_first_admin  # noqa: E402
from modules.masterdata.backend.models import Customer, Location, Product  # noqa: E402
from modules.transport.backend.models import Driver, Vehicle  # noqa: E402
from modules.warehouse.backend import service as wh  # noqa: E402

WAREHOUSES = [("Төв агуулах", 47.9184, 106.9177), ("Дархан салбар", 49.4867, 105.9228),
              ("Эрдэнэт салбар", 49.0270, 104.0440)]
# sku, ner, negj, kg, une, [(aguulah index, too, min)]
PRODUCTS = [
    ("P-001", "Цемент 50кг", "шуудай", 50, 15000, [(0, 240, 100)]),
    ("P-002", "Арматур 12мм", "ш", 10.7, 32000, [(0, 35, 50)]),
    ("P-003", "Будаг цагаан 20л", "ш", 22, 85000, [(1, 0, 20)]),
    ("P-004", "Тоосго", "ш", 2.5, 450, [(1, 5200, 2000)]),
    ("P-005", "Цахилгаан кабель", "м", 0.3, 2800, [(2, 80, 60)]),
    ("P-006", "Хаалга 90см", "ш", 35, 380000, [(2, 14, 15)]),
]
CUSTOMERS = [("Мон Барилга ХХК", "Дархан, 7-р хороолол", 49.4700, 105.9500),
             ("Эрдэнэт Констракшн", "Эрдэнэт, Баян-Өндөр", 49.0300, 104.0800),
             ("Хотын Засвар ХХК", "УБ, Хан-Уул дүүрэг", 47.8864, 106.9057)]


def main() -> None:
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_first_admin(db)
        if db.scalar(select(Location.id).where(Location.type == "warehouse")):
            print("Aguulah burtgeltei baina - seed algasav.")
            return
        for role in ("dispatcher", "warehouse", "driver", "accountant"):
            if not db.scalar(select(User.id).where(User.username == role)):
                create_user(db, role, f"{role}123", role, role.capitalize())

        whs = [Location(name=n, type="warehouse", lat=lat, lng=lng) for n, lat, lng in WAREHOUSES]
        db.add_all(whs)
        db.flush()
        for sku, name, unit, kg, price, stock in PRODUCTS:
            p = db.scalar(select(Product).where(Product.sku == sku))
            if p is None:
                p = Product(sku=sku, name=name, unit=unit, weight_kg=kg, price=Decimal(price))
                db.add(p)
                db.flush()
            for i, qty, min_level in stock:
                wh.get_stock(db, whs[i].id, p.id).min_level = Decimal(min_level)
                if qty:
                    wh.move(db, whs[i].id, p.id, "in", Decimal(qty), None, "Anhnii uldegdel")
        for i, (name, addr, lat, lng) in enumerate(CUSTOMERS, start=1):
            c = Customer(code=f"DEMO-{i}", name=name, address=addr)
            db.add(c)
            db.flush()
            db.add(Location(name=f"{name} – талбай", type="customer", address=addr, lat=lat,
                            lng=lng, customer_id=c.id))
        db.add_all([Vehicle(plate_no="УБА 1234", type="truck", capacity_kg=10000),
                    Vehicle(plate_no="УНК 5678", type="truck", capacity_kg=20000),
                    Vehicle(plate_no="ДАА 9012", type="van", capacity_kg=5000)])
        driver_user = db.scalar(select(User).where(User.username == "driver"))
        db.add_all([Driver(full_name="Б. Бат", phone="99112233", user_id=driver_user.id),
                    Driver(full_name="Д. Ганбаа", phone="88112233"),
                    Driver(full_name="Э. Сарнай", phone="95112233")])
        db.commit()
        print("Demo ugugdul orloo.")


if __name__ == "__main__":
    main()
