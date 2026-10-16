"""Маршрутын оновчлол: Nearest Neighbor (багтаамжтай) + 2-opt сайжруулалт."""
import math

from .schemas import RouteRequest, RouteResponse, VehicleRoute

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def distance_matrix(points) -> list[list[float]]:
    n = len(points)
    dm = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(points[i].lat, points[i].lng, points[j].lat, points[j].lng)
            dm[i][j] = dm[j][i] = d
    return dm


def route_length(path: list[int], dm) -> float:
    return sum(dm[a][b] for a, b in zip(path, path[1:]))


def two_opt(route: list[int], dm) -> list[int]:
    """Depot (0) эхлэл/төгсгөлд тогтмол, дундах зогсоолуудыг сайжруулна."""
    path = [0] + route + [0]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if dm[a][c] + dm[b][d] < dm[a][b] + dm[c][d] - 1e-9:
                    path[i : j + 1] = reversed(path[i : j + 1])
                    improved = True
    return path[1:-1]


def solve(req: RouteRequest) -> RouteResponse:
    points = [req.depot] + req.stops
    n = len(req.stops)
    dm = distance_matrix(points)

    cap = req.vehicle_capacity
    # Багтаамж өгөөгүй бол зогсоолыг машинуудад тэнцүү хуваана
    max_stops = None if cap else math.ceil(n / req.vehicle_count)

    unvisited = set(range(1, n + 1))
    raw_routes: list[tuple[list[int], float]] = []

    for _ in range(req.vehicle_count):
        if not unvisited:
            break
        route, load, cur = [], 0.0, 0
        while True:
            cand = [
                j for j in unvisited
                if (cap is None or load + points[j].demand <= cap)
                and (max_stops is None or len(route) < max_stops)
            ]
            if not cand:
                break
            nxt = min(cand, key=lambda j: dm[cur][j])
            route.append(nxt)
            load += points[nxt].demand
            unvisited.discard(nxt)
            cur = nxt
        if route:
            raw_routes.append((route, load))

    routes: list[VehicleRoute] = []
    for k, (route, load) in enumerate(raw_routes):
        if req.improve and len(route) > 2:
            route = two_opt(route, dm)
        full = [0] + route + [0]
        dist = route_length(full, dm)
        routes.append(
            VehicleRoute(
                vehicle_index=k,
                stop_ids=[points[i].id for i in route],
                path=[points[i] for i in full],
                load=round(load, 3),
                distance_km=round(dist, 3),
                duration_min=round(dist / req.avg_speed_kmh * 60, 1),
            )
        )

    return RouteResponse(
        routes=routes,
        total_distance_km=round(sum(r.distance_km for r in routes), 3),
        total_duration_min=round(sum(r.duration_min for r in routes), 1),
        unassigned_stop_ids=sorted(points[i].id for i in unvisited),
    )