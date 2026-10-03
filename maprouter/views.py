from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . serializers import RouteRequestSerializer
from .services.geocoding import geocoder_address
from .services.routing import get_route
from .services.fuel_optimiser import select_fuel_stops, calculate_fuel_cost
from .services.fuel_optimiser_helper import get_route_candidates
from .models import FuelStation


class RouteAPIView(APIView):

    def post(self, request):
        serializer = RouteRequestSerializer(data = request.data)

        serializer.is_valid(raise_exception = True)

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        try:
            # 1. Geocode start
            start_location = geocoder_address(start)

            # 2. Geocode finish
            finish_location = geocoder_address(finish)

            # 3. Get driving route
            route = get_route(
                start_location["latitude"],
                start_location["longitude"],
                finish_location["latitude"],
                finish_location["longitude"]
            )

            # 4. Get fuel stations
            stations = FuelStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

            # 5. Find stations near route
            candidates = get_route_candidates(route['geometry'], stations)
            # print("Candidates for Fuel Stops\n")
            # print(candidates)
            print("TOTAL CANDIDATES:", len(candidates))

            for candidate in candidates[:10]:
                print(
                    candidate["station"].name,
                    candidate["station"].city,
                    candidate["station"].state,
                    "route_distance=",
                    candidate["route_distance"],
                    "from_route=",
                    candidate["distance_from_route"],
                )

            # 6. Optimize fuel stops
            fuel_stops = select_fuel_stops(route["distance_miles"], candidates)



            fuel_cost = calculate_fuel_cost(route["distance_miles"], fuel_stops)

            return Response(
                {
                    "start": {
                        "input": start,
                        "matched_address": start_location["matched_address"],
                        "latitude": start_location["latitude"],
                        "longitude": start_location["longitude"]
                    },

                    "finish": {
                        "input": finish,
                        "matched_address": finish_location["matched_address"],
                        "latitude": finish_location["latitude"],
                        "longitude": finish_location["longitude"]
                    },

                    "route" : {
                        "distance_miles": round(route["distance_miles"], 2),
                        "duration_minutes": round(route["duration_minutes"], 2),
                        "geometry": route["geometry"]
                    },

                    "fuel_cost" : fuel_cost,

                    "fuel_stops": [
                        {
                            "station_id": item["station"].id,
                            "name": item["station"].name,
                            "address": item["station"].address,
                            "city": item["station"].city,
                            "state": item["station"].state,
                            "latitude": item["station"].latitude,
                            "longitude": item["station"].longitude,
                            "price_per_gallon": float(
                                item["station"].retail_price
                            ),
                            "route_distance_miles": round(
                                item["route_distance"], 2
                            ),
                        }
                        for item in fuel_stops
                    ]
                }, status = status.HTTP_200_OK
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Unable to calculate route", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

