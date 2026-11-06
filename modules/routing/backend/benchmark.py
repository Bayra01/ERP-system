"""Ажиллуулах: python -m modules.routing.backend.benchmark"""
import random
import time

from .schemas import Location, RouteRequest
from .service import solve


def run(n: int, vehicles: int = 5, seed: int = 1):
    rnd = random.Random(seed)
    depot = Location(id="D", lat=47.9184, lng=106.9177)
    stops = [
        Location(id=f"S{i}", lat=47.8 + rnd.random() * 0.2, lng=106.8 + rnd.random() * 0.3, demand=rnd.randint(1, 20))
        for i in range(n)
    ]
    for improve in (False, True):
        req = RouteRequest(depot=depot, stops=stops, vehicle_count=vehicles, improve=improve)
        t = time.perf_counter()
        res = solve(req)
        dt = time.perf_counter() - t
        print(f"n={n:4d} 2-opt={improve!s:5} зай={res.total_distance_km:8.2f} км  хугацаа={dt:6.2f} с")


if __name__ == "__main__":
    for n in (25, 50, 100, 200):
        run(n)