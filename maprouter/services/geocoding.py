import requests, hashlib
from django.core.cache import cache
from ..constants import CENSUS_GEOCODER_URL, NOMINATIM_URL

def get_cache_key(address):
    normalized = address.lower().strip()
    address_hash = hashlib.sha256(normalized.encode()).hexdigest()
    return f"geocode:{address_hash}"

def geocoder_address(address):
    cache_key = get_cache_key(address)

    cached = cache.get(cache_key)

    if cached:
        return cached

    # # Census params
    # params = {
    #     "address": address,
    #     "benchmark": "Public_AR_Current",
    #     "vintage": "Current_Current",
    #     "format": "json",
    # }

    params = {
        "q": f"{address}, USA",
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    }

    headers = {
        "User-Agent": "fuel-route-assignment/1.0"
    }

    response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)

    data = response.json()

    response.raise_for_status()

    if not data:
        raise ValueError(
            f"Could not geocode address: {address}"
        )

    result = data[0]

    if not isinstance(result, dict):
        raise ValueError(
            f"Unexpected Nominatim response: {result}"
        )

    geocoded = {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "matched_address": result.get(
            "display_name",
            address
        ),
    }

    cache.set(cache_key,geocoded,timeout=86400)

    return geocoded