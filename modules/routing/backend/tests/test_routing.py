import json
import importlib
import sys
from pathlib import Path

pytest = importlib.import_module("pytest")

fastapi = pytest.importorskip("fastapi")
FastAPI = fastapi.FastAPI
TestClient = importlib.import_module("fastapi.testclient").TestClient

# Ensure the repository root is importable when tests are run from this directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

router = importlib.import_module("modules.routing.backend.router").router
schemas = importlib.import_module("modules.routing.backend.schemas")
Location = schemas.Location
RouteRequest = schemas.RouteRequest
service = importlib.import_module("modules.routing.backend.service")
haversine_km = service.haversine_km
solve = service.solve

SAMPLE = json.loads((Path(__file__).parent.parent / "sample_input.json").read_text(encoding="utf-8"))
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_haversine_zero_and_known():
    assert haversine_km(47.9, 106.9, 47.9, 106.9) == 0
    # Улаанбаатар - Дархан ~ 190-200 км шулуунаар
    assert 170 < haversine_km(47.9184, 106.9177, 49.4867, 105.9228) < 210


def test_all_stops_assigned_once():
    res = solve(RouteRequest(**SAMPLE))
    ids = [i for r in res.routes for i in r.stop_ids]
    assert sorted(ids) == ["A", "B", "C", "D", "E", "F"]
    assert res.unassigned_stop_ids == []


def test_capacity_respected():
    res = solve(RouteRequest(**SAMPLE))
    assert all(r.load <= 120 for r in res.routes)


def test_path_starts_and_ends_at_depot():
    res = solve(RouteRequest(**SAMPLE))
    for r in res.routes:
        assert r.path[0].id == r.path[-1].id == "WH1"


def test_two_opt_not_worse():
    base = {**SAMPLE, "vehicle_count": 1, "vehicle_capacity": None}
    a = solve(RouteRequest(**{**base, "improve": False}))
    b = solve(RouteRequest(**{**base, "improve": True}))
    assert b.total_distance_km <= a.total_distance_km + 1e-6


def test_unassigned_when_not_enough_vehicles():
    res = solve(RouteRequest(**{**SAMPLE, "vehicle_count": 1, "vehicle_capacity": 100}))
    assert res.unassigned_stop_ids


def test_duplicate_ids_rejected():
    bad = {**SAMPLE, "stops": SAMPLE["stops"] + [SAMPLE["stops"][0]]}
    with pytest.raises(ValueError):
        RouteRequest(**bad)


def test_api_optimize_ok():
    r = client.post("/api/routing/optimize", json=SAMPLE)
    assert r.status_code == 200
    assert r.json()["total_distance_km"] > 0


def test_api_oversized_stop_422():
    bad = {**SAMPLE, "vehicle_capacity": 10}
    assert client.post("/api/routing/optimize", json=bad).status_code == 422


def test_api_health():
    assert client.get("/api/routing/health").json()["status"] == "ok"