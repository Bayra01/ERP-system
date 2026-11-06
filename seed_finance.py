"""Sanhuugiin jishee ugugdul: suuliin 12 sariin nehemjleh, tulbur, zardal.

  python seed_finance.py          # oruulna (demo ugugdul baigaa bol yu ch hiihgui)
  python seed_finance.py --clear  # zuvhun demo ugugdliig ustgana (garaar oruulsniig hondohgui)

Demo nehemjleh: notes "[demo] ..." -eer, demo zardal: created_by = NULL (UI-aas oruulsan zardal hereglegchtei).
Random seed togtmol tul dahin ajilluulahad ijil ugugdul garna. Dun, tuluv service-eer damjin uusne.
"""
import random
import sys
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from core.database import Base, SessionLocal, engine
from core.registry import import_all_models

import_all_models()

from modules.finance.backend import service  # noqa: E402
from modules.finance.backend.models import Expense, Invoice, Payment  # noqa: E402
from modules.masterdata.backend.models import Customer  # noqa: E402

TAG = "[demo]"
TODAY = date.today()
CUSTOMERS = [  # (kod, ner, hayag) - baihgui bol uusgene
    ("DEMO-1", "Мон Барилга ХХК", "Дархан, 7-р хороолол"),
    ("DEMO-2", "Эрдэнэт Констракшн", "Эрдэнэт, Баян-Өндөр"),
    ("DEMO-3", "Хотын Засвар ХХК", "УБ, Хан-Уул дүүрэг"),
    ("DEMO-4", "Говь Трейд ХХК", "Даланзадгад, 2-р баг"),
    ("DEMO-5", "Сэлэнгэ Агро ХХК", "Сүхбаатар, Сэлэнгэ"),
]
SERVICES = ["Барилгын материал тээвэрлэлт", "Агуулахын хадгалалт", "Хот хоорондын ачаа тээвэр",
            "Хүргэлтийн үйлчилгээ", "Ачих буулгах үйлчилгээ"]


def months_back(n: int) -> list[tuple[int, int]]:
    y, m, out = TODAY.year, TODAY.month, []
    for _ in range(n):
        out.append((y, m))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out[::-1]


def day_in(rng, y: int, m: int, lo: int = 1, hi: int | None = None) -> date | None:
    last = monthrange(y, m)[1] if hi is None else min(hi, monthrange(y, m)[1])
    if (y, m) == (TODAY.year, TODAY.month):  # odoogiin sar: unuudur hurtel
        last = min(last, TODAY.day)
    if lo > last:
        return None
    d = date(y, m, rng.randint(lo, last))
    return d if d <= TODAY else None


def ensure_customers(db) -> list[Customer]:
    out = []
    for code, name, addr in CUSTOMERS:
        c = db.scalar(select(Customer).where(Customer.code == code))
        if c is None:
            c = Customer(code=code, name=name, address=addr, type="company")
            db.add(c)
            db.flush()
        out.append(c)
    db.commit()
    return out


def round10k(x: Decimal) -> Decimal:
    return (x / 10000).quantize(Decimal(1)) * 10000


def pay_plan(rng, age: int) -> str:
    """Nasnaas hamaarch: full / partial / none. Huuchin nehemjleh ihenh n tulugdsun (bodit nasjilt)."""
    r = rng.random()
    if age > 120:
        return "full" if r < .92 else "partial" if r < .97 else "none"
    if age > 75:
        return "full" if r < .75 else "partial" if r < .90 else "none"
    if age > 40:
        return "full" if r < .55 else "partial" if r < .80 else "none"
    if age > 20:
        return "full" if r < .35 else "partial" if r < .60 else "none"
    return "full" if r < .10 else "none"


def seed_invoices(db, rng, customers) -> tuple[int, int]:
    n_inv = n_pay = 0
    for y, m in months_back(12):
        for _ in range(rng.randint(3, 5)):
            issued = day_in(rng, y, m)
            if issued is None:
                continue
            cust = rng.choice(customers)
            amount = Decimal(rng.randrange(1_200_000, 8_500_000, 10_000))
            inv = service.create_invoice(db, cust.id, amount, None, issued=issued,
                                         notes=f"{TAG} {rng.choice(SERVICES)}")
            n_inv += 1
            plan = pay_plan(rng, (TODAY - issued).days)
            if plan == "none":
                continue
            target = amount if plan == "full" else round10k(amount * Decimal(rng.choice(["0.3", "0.4", "0.5", "0.6"])))
            half = round10k(target / 2)
            parts = [target] if rng.random() < .7 or plan == "partial" else [half, target - half]
            on = issued
            for part in parts:
                on = min(on + timedelta(days=rng.randint(7, 30)), TODAY)
                method = rng.choices(["bank", "cash", "card"], weights=[75, 15, 10])[0]
                service.add_payment(db, inv.id, part, method, on, None)
                n_pay += 1
    return n_inv, n_pay


def seed_expenses(db, rng) -> int:
    rows = []
    for y, m in months_back(12):
        winter = m in (11, 12, 1, 2, 3)
        plan = [
            (25, 25, "Цалин", "Ажилчдын цалин", rng.randrange(6_800_000, 7_400_000, 10_000)),
            (5, 5, "Түрээс", "Агуулах Түрээс ХХК", 1_200_000),
            (15, 15, "Ашиглалтын зардал", "УБЦТС, дулаан", rng.randrange(550_000 if winter else 300_000,
                                                                        950_000 if winter else 500_000, 10_000)),
            (10, 12, "Харилцаа холбоо", "Юнител ХХК", 180_000),
        ]
        plan += [(1, 28, "Шатахуун", rng.choice(["Шунхлай ХХК", "Петровис ХХК", "Магнай Трейд ХХК"]),
                  rng.randrange(700_000, 1_600_000, 10_000)) for _ in range(3)]
        if rng.random() < .5:
            plan.append((1, 28, "Засвар үйлчилгээ", "Авто Сервис ХХК", rng.randrange(300_000, 1_500_000, 10_000)))
        if m in (1, 4, 7, 10):
            plan.append((3, 3, "Даатгал", "Монгол Даатгал ХК", 1_800_000))
        for lo, hi, cat, vendor, amount in plan:
            d = day_in(rng, y, m, lo, hi)
            if d is None:
                continue
            status = "pending" if (TODAY - d).days < 10 else "paid"
            rows.append(Expense(date=d, category=cat, vendor=vendor, amount=Decimal(amount),
                                status=status, created_by=None))
    db.add_all(rows)
    db.commit()
    return len(rows)


def clear(db) -> None:
    ids = db.scalars(select(Invoice.id).where(Invoice.notes.like(f"{TAG}%"))).all()
    db.execute(delete(Payment).where(Payment.invoice_id.in_(ids)))
    db.execute(delete(Invoice).where(Invoice.id.in_(ids)))
    n = db.execute(delete(Expense).where(Expense.created_by.is_(None))).rowcount
    db.commit()
    print(f"Ustgalaa: {len(ids)} nehemjleh (tulburtei), {n} zardal")


def main() -> None:
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if "--clear" in sys.argv:
            return clear(db)
        if db.scalar(select(Invoice.id).where(Invoice.notes.like(f"{TAG}%"))):
            print("Demo sanhuugiin ugugdul baina - algasav (dahin oruulah bol --clear).")
            return
        rng = random.Random(2026)
        customers = ensure_customers(db)
        n_inv, n_pay = seed_invoices(db, rng, customers)
        n_exp = seed_expenses(db, rng)
        print(f"Oruullaa: {n_inv} nehemjleh, {n_pay} tulbur, {n_exp} zardal ({engine.url.get_backend_name()})")


if __name__ == "__main__":
    main()
