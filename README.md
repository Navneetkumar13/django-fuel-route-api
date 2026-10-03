# Fuel Route Optimizer API

A Django REST API that calculates a driving route between two US locations and identifies cost-effective fuel stops using the provided fuel-price dataset.

## Features

- Accepts start and finish locations through a REST API.
- Geocodes locations using OpenStreetMap Nominatim.
- Calculates the driving route using OSRM.
- Returns route distance, duration, and GeoJSON route geometry.
- Finds fuel stations available in the database along the route.
- Selects feasible fuel stops based on the vehicle's maximum range and fuel prices.
- Calculates estimated fuel consumption and fuel cost.
- Uses Redis caching for geocoding, routing, and route-candidate calculations.
- PostgreSQL is used for persistent fuel-station data.

## Technology Stack

- Python 3.14+
- Django 6.1.1
- Django REST Framework
- PostgreSQL
- Redis
- OSRM
- OpenStreetMap Nominatim
- Shapely / PyProj
- Docker / Docker Compose

## Vehicle Assumptions

- Maximum driving range: **500 miles**
- Fuel economy: **10 miles per gallon**
- Implied tank capacity: **50 gallons**
- Vehicle starts with a full tank.

## Project Structure

```text
map/
├── data/
│   └── fuel-prices-for-be-assessment.csv
├── map/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── maprouter/
│   ├── migrations/
│   ├── services/
│   │   ├── fuel_optimiser.py
│   │   ├── fuel_optimiser_helper.py
│   │   ├── geocoding.py
│   │   └── routing.py
│   ├── management/
│   │   └── commands/
│   │       └── import_fuel_stations.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── constants.py
│   └── tests.py
├── manage.py
├── requirements.txt
```

## API

### Calculate Route

**Endpoint**

```text
POST /route/
```

**Request**

```json
{
  "start": "New York, NY",
  "finish": "Chicago, IL"
}
```

The response contains:

- Geocoded start and finish locations
- Route distance in miles
- Estimated route duration
- GeoJSON route geometry
- Fuel consumption
- Estimated fuel cost
- Selected fuel stops and their prices

Example response shape:

```json
{
  "start": {
    "input": "New York, NY",
    "matched_address": "...",
    "latitude": 40.7127,
    "longitude": -74.0060
  },
  "finish": {
    "input": "Chicago, IL",
    "matched_address": "...",
    "latitude": 41.8756,
    "longitude": -87.6244
  },
  "route": {
    "distance_miles": 790.12,
    "duration_minutes": 720.5,
    "geometry": {
      "type": "LineString",
      "coordinates": []
    }
  },
  "fuel": {
    "total_gallons": 79.01,
    "gallons_purchased": 29.01,
    "total_cost": 107.33
  },
  "fuel_stops": [
    {
      "station_id": 123,
      "name": "Example Fuel Station",
      "address": "Example Address",
      "city": "Example City",
      "state": "PA",
      "price_per_gallon": 3.699
    }
  ]
}
```

## Fuel Stop Selection

The vehicle starts with a full 50-gallon tank, giving it a maximum range of 500 miles.

For routes longer than 500 miles, the optimizer considers fuel stations that are reachable from the current position. It prioritizes a cheaper station when it can still be used while maintaining the vehicle's maximum range to the destination.

If no reachable station is available within the required range, the API returns an error instead of selecting an invalid fuel stop.

## Fuel Cost Calculation

Fuel consumption:

```text
Total gallons = route distance / 10 MPG
```

Because the vehicle starts with a full 50-gallon tank:

```text
Gallons to purchase = max(0, total gallons - 50)
```

The estimated cost is based on the selected fuel-stop prices.

## Caching

Redis is used through `django-redis`.

The following expensive operations are cached for 24 hours:

- Address geocoding
- OSRM route calculation
- Route fuel-station candidate calculation

This avoids repeating external API calls and expensive route/station calculations for identical requests.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd map
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL and Redis

Make sure PostgreSQL and Redis are running locally, or use the provided Docker Compose configuration.

For Redis on Ubuntu:

```bash
sudo systemctl start redis-server
redis-cli ping
```

Expected:

```text
PONG
```

### 5. Configure the database

Update the database configuration in `map/settings.py` or provide the required environment variables if using Docker.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Import fuel-price data

```bash
python manage.py import_fuel_stations
```

### 8. Start Django

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## Running Tests

```bash
python manage.py test
```

## Example cURL Request

```bash
curl -X POST http://127.0.0.1:8000/route/   -H "Content-Type: application/json"   -d '{
    "start": "New York, NY",
    "finish": "Chicago, IL"
  }'
```

## External Services

### OpenStreetMap Nominatim

Used to convert user-provided locations into latitude/longitude coordinates.

### OSRM

Used to calculate the driving route and route geometry.

Both are external HTTP services. The first request for a new route depends on their availability and response time. Redis caching reduces repeated calls for the same inputs.

## Data Notes

The supplied CSV is imported into PostgreSQL and provides the fuel-price information used by the API.

The supplied dataset has incomplete coordinate coverage. Only stations with usable coordinates can currently participate directly in route-candidate calculations. If a requested route does not have enough stations with usable price/location data, the API returns an error rather than selecting an invalid fuel stop.

## API Error Handling

Typical client-side errors return HTTP `400`, including:

- Missing required request fields
- Invalid request data
- Unable to geocode a requested location
- No feasible fuel station available within the vehicle's range

Unexpected server errors return HTTP `500`.

## Performance

The first request for a new start/finish pair performs the required external calls and route calculations. Repeated requests for the same route use Redis cache entries and therefore avoid most of that work.

## License

This project was created as a backend engineering assignment.
