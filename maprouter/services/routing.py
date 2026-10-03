import hashlib
import requests

from django.core.cache import cache

OSRM_URL = "https://router.project-osrm.org"


def get_route(start_latitude, start_longitude, finish_latitude, finish_longitude):
    cache_input = (
        f"{start_latitude:.6f},"
        f"{start_longitude:.6f},"
        f"{finish_latitude:.6f},"
        f"{finish_longitude:.6f}"
    )

    cache_key = "route:" + hashlib.sha256(cache_input.encode()).hexdigest()
    cached_route = cache.get(cache_key)

    if cached_route:
        return cached_route

    coordinates = (
        f"{start_longitude},{start_latitude};"
        f"{finish_longitude},{finish_latitude}"
    )

    url = f"{OSRM_URL}/route/v1/driving/{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            f"Unexpected OSRM response type: "
            f"{type(data).__name__}"
        )

    if data.get("code") != "Ok":
        raise ValueError(
            f"Unable to calculate route: {data.get('code')}"
        )

    routes = data.get("routes")

    if not routes:
        raise ValueError("OSRM returned no routes")

    route = routes[0]

    distance_meters = float(route["distance"])
    duration_seconds = float(route["duration"])

    result = {
        "distance_meters": distance_meters,
        "distance_miles": distance_meters / 1609.344,
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_seconds / 60,
        "geometry": route["geometry"],
    }

    # Cache for 24 hours
    cache.set(cache_key, result, timeout=86400)

    return result