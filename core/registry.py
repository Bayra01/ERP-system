"""Bukh modulin models-g import hiine (Alembic + create_all-d shaardlagatai)."""
import importlib

MODULES = ["auth", "masterdata", "orders", "warehouse", "transport", "routing", "finance", "notifications"]


def import_all_models() -> None:
    importlib.import_module("core.audit")
    for m in MODULES:
        importlib.import_module(f"modules.{m}.backend.models")
