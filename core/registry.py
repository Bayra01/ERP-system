"""Bukh modulin models-g import hiine (Alembic + create_all-d shaardlagatai)."""
import importlib

<<<<<<< HEAD
MODULES = ["auth", "masterdata", "orders", "warehouse", "transport", "routing", "finance", "notifications", "portal"]
=======
MODULES = ["auth", "masterdata", "orders", "warehouse", "transport", "routing", "finance", "notifications"]
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


def import_all_models() -> None:
    importlib.import_module("core.audit")
    for m in MODULES:
        importlib.import_module(f"modules.{m}.backend.models")
