from ..constants import MAX_RANGE_MILES, MILES_PER_GALLON


def calculate_fuel_cost(route_distance, fuel_stops):
    """
    Calculate total fuel consumed and estimated fuel cost.

    Assumption:
    - Vehicle starts with a full tank.
    - Fuel is purchased at the selected stops.
    - Fuel economy is defined by MILES_PER_GALLON.
    """

    total_gallons = route_distance / MILES_PER_GALLON

    # Starting with a full tank (50 gallons)
    initial_fuel = 500 / MILES_PER_GALLON

    gallons_to_purchase = max(0, total_gallons - initial_fuel)

    if not fuel_stops:
        return {
            "total_gallons": round(total_gallons, 2),
            "gallons_purchased": round(gallons_to_purchase, 2),
            "total_cost": 0.0,
        }

    # For now, use the selected stop prices to calculate
    # the cost of the additional fuel required.
    cheapest_price = min(
        float(stop["station"].retail_price)
        for stop in fuel_stops
    )

    total_cost = gallons_to_purchase * cheapest_price

    return {
        "total_gallons": round(total_gallons, 2),
        "gallons_purchased": round(gallons_to_purchase, 2),
        "total_cost": round(total_cost, 2),
    }


def select_fuel_stops(route_distance, candidates):
    """
    Select the cheapest feasible fuel stations.

    Vehicle starts with a full tank and has a 500-mile range.
    """

    if route_distance <= MAX_RANGE_MILES:
        return []

    candidates = [
        c for c in candidates
        if 0 < c["route_distance"] < route_distance
    ]

    candidates.sort(key=lambda x: x["route_distance"])

    selected = []
    current_position = 0

    while route_distance - current_position > MAX_RANGE_MILES:

        # The next stop must be reachable.
        max_reachable = current_position + MAX_RANGE_MILES

        reachable = [
            c for c in candidates
            if current_position < c["route_distance"] <= max_reachable
        ]

        if not reachable:
            raise ValueError(
                f"No fuel station reachable from "
                f"{current_position:.1f} miles. "
                f"Maximum range is {MAX_RANGE_MILES} miles."
            )

        # We want a station from which the destination
        # can eventually be reached.
        useful = [
            c for c in reachable
            if route_distance - c["route_distance"]
            <= MAX_RANGE_MILES
        ]

        if useful:
            # This is the final fuel stop.
            stop = min(
                useful,
                key=lambda x: float(x["station"].retail_price)
            )
        else:
            # We still need another stop after this one.
            #
            # Look for the cheapest station in the reachable
            # range, but prefer stations further along the route.
            stop = min(
                reachable,
                key=lambda x: (
                    float(x["station"].retail_price),
                    -x["route_distance"]
                )
            )

        selected.append(stop)

        current_position = stop["route_distance"]

        # Don't consider stations behind the vehicle.
        candidates = [
            c for c in candidates
            if c["route_distance"] > current_position
        ]

    return selected