"""Modul hoorondiin sul holbolt: in-process event bus.

Modul A:  events.publish("order.confirmed", {"order_id": 5})
Modul B:  @events.subscribe("order.confirmed")
          def reserve_stock(payload): ...

Neg handler aldaa garsan ch busdad n nölöölöhgui (log hiine).
Daraa n Redis/Celery bolgoh bol ene file-g l solino.
"""
import logging
from collections import defaultdict
from collections.abc import Callable

log = logging.getLogger("erp.events")
_handlers: dict[str, list[Callable[[dict], None]]] = defaultdict(list)


def subscribe(event: str):
    def deco(fn: Callable[[dict], None]):
        _handlers[event].append(fn)
        return fn
    return deco


def publish(event: str, payload: dict | None = None) -> None:
    for fn in list(_handlers.get(event, [])):
        try:
            fn(payload or {})
        except Exception:  # noqa: BLE001
            log.exception("event handler failed: %s -> %s", event, fn.__name__)


def clear() -> None:  # tested ashiglana
    _handlers.clear()


def snapshot() -> dict:
    """Test-d: odoogiin handler-uudiig hadgalna (clear() hiigeed daraa n restore())."""
    return {k: list(v) for k, v in _handlers.items()}


def restore(saved: dict) -> None:
    _handlers.clear()
    _handlers.update({k: list(v) for k, v in saved.items()})
