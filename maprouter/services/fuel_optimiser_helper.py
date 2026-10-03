from shapely.geometry import LineString, Point
from shapely.ops import transform
import pyproj

from ..constants import ROUTE_CORRIDOR_MILES
import hashlib
import json

from django.core.cache import cache


def create_route_line(geometry):
    return LineString(geometry["coordinates"])

def station_distance_along_route(route_geometry, station):
    route_line = create_route_line(route_geometry)

    project = pyproj.Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3857",
        always_xy=True
    ).transform

    projected_route = transform(
        project,
        route_line
    )

    point = Point(
        station.longitude,
        station.latitude
    )

    projected_point = transform(
        project,
        point
    )

    distance_meters = projected_route.project(
        projected_point
    )

    return distance_meters / 1609.344


def get_route_candidates(route_geometry, stations):
    cache_input = json.dumps(
        route_geometry,
        sort_keys=True
    )

    cache_key = (
        "route_candidates:"
        + hashlib.sha256(
            cache_input.encode()
        ).hexdigest()
    )

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    route_line = create_route_line(route_geometry)

    project = pyproj.Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3857",
        always_xy=True
    ).transform

    projected_route = transform(
        project,
        route_line
    )

    candidates = []

    for station in stations:
        if (
            station.latitude is None
            or station.longitude is None
        ):
            continue

        point = Point(
            station.longitude,
            station.latitude
        )

        projected_point = transform(
            project,
            point
        )

        distance_meters = projected_route.distance(
            projected_point
        )

        distance_miles = distance_meters / 1609.344

        if distance_miles <= ROUTE_CORRIDOR_MILES:

            route_distance = (
                station_distance_along_route(
                    route_geometry,
                    station
                )
            )

            candidates.append({
                "station": station,
                "distance_from_route": distance_miles,
                "route_distance": route_distance,
            })

    candidates.sort(
        key=lambda item: item["route_distance"]
    )

    cache.set(
        cache_key,
        candidates,
        timeout=86400
    )

    return candidates