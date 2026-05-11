import httpx
import math
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ecological import EcologicalMeasurement, EcoIndicatorType, EcoDataSource
from app.models.territory import Territory

SAVEECOBOT_URL = "https://api.saveecobot.com/output.json"

PARAMETER_MAP = {
    "PM2.5": EcoIndicatorType.pm25,
    "PM10": EcoIndicatorType.pm10,
    "Air Quality Index": EcoIndicatorType.aqi,
    "Temperature": EcoIndicatorType.temperature,
    "Humidity": EcoIndicatorType.humidity,
    "Pressure": EcoIndicatorType.pressure,
}

UNIT_MAP = {
    "PM2.5": "μg/m³",
    "PM10": "μg/m³",
    "Air Quality Index": "AQI",
    "Temperature": "°C",
    "Humidity": "%",
    "Pressure": "hPa",
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Відстань між двома точками в кілометрах"""
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def get_station_coords(station: dict):
    """Витягує координати станції з різних можливих полів"""
    for lat_key in ["lat", "latitude", "Lat", "Latitude"]:
        for lon_key in ["lon", "lng", "longitude", "Lon", "Lng", "Longitude"]:
            lat = station.get(lat_key)
            lon = station.get(lon_key)
            if lat is not None and lon is not None:
                try:
                    return float(lat), float(lon)
                except Exception:
                    continue
    return None, None


def find_stations_by_city(stations: list, city: str) -> list:
    """Знаходить станції по назві міста"""
    city_lower = city.lower()
    return [
        s for s in stations
        if city_lower in s.get("cityName", "").lower()
        or city_lower in s.get("stationName", "").lower()
        or city_lower in s.get("localName", "").lower()
    ]


def find_nearest_stations(stations: list, lat: float, lon: float, max_distance_km: float = 300) -> list:
    """
    Знаходить найближчі станції до заданих координат.
    Повертає станції в радіусі max_distance_km, відсортовані за відстанню.
    """
    candidates = []
    for station in stations:
        s_lat, s_lon = get_station_coords(station)
        if s_lat is None or s_lon is None:
            continue
        dist = haversine_distance(lat, lon, s_lat, s_lon)
        if dist <= max_distance_km:
            candidates.append((dist, station))

    candidates.sort(key=lambda x: x[0])

    if not candidates:
        return []

    # Беремо станції в межах найближчого міста (перші 3 найближчі)
    nearest_dist = candidates[0][0]
    result = []
    for dist, station in candidates:
        if dist <= nearest_dist + 50:  # в межах 50 км від найближчої
            result.append(station)
        if len(result) >= 5:
            break

    return result


async def fetch_saveecobot_data(
    city: str,
    territory_id: int,
    db: Session,
    region: str = None,
    city_lat: float = None,
    city_lon: float = None
) -> dict:
    """
    Завантажує дані з SaveEcoBot.

    Логіка:
    1. Шукаємо станції по назві міста
    2. Якщо не знайдено і є координати — знаходимо найближчі станції по координатах
    3. Записуємо дані до territory_id і до всіх міст цього регіону в БД
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SAVEECOBOT_URL, timeout=15.0)
            if response.status_code != 200:
                return {"success": False, "error": f"SaveEcoBot API помилка: {response.status_code}"}
            stations = response.json()

        # 1. Шукаємо по назві міста
        matching = find_stations_by_city(stations, city)
        used_nearest = False
        nearest_city_name = None

        # 2. Якщо не знайдено — шукаємо найближчу станцію по координатах
        if not matching:
            # Беремо координати з БД якщо не передані
            if city_lat is None or city_lon is None:
                territory = db.query(Territory).filter(Territory.id == territory_id).first()
                if territory and territory.latitude and territory.longitude:
                    city_lat = territory.latitude
                    city_lon = territory.longitude

            if city_lat is not None and city_lon is not None:
                matching = find_nearest_stations(stations, city_lat, city_lon)
                if matching:
                    used_nearest = True
                    nearest_city_name = matching[0].get("cityName", "невідоме місто")

        if not matching:
            return {
                "success": False,
                "error": f"Для міста '{city}' не знайдено станцій. Перевірте координати міста в Дашборді."
            }

        # Знаходимо всі міста цього регіону в БД для запису
        territory_ids = [territory_id]
        if region:
            region_cities = db.query(Territory).filter(
                Territory.region == region
            ).all()
            for t in region_cities:
                if t.id not in territory_ids:
                    territory_ids.append(t.id)

        imported = 0
        for station in matching:
            for p in station.get("pollutants", []):
                pol_name = p.get("pol", "")
                if pol_name not in PARAMETER_MAP:
                    continue
                value = p.get("value")
                if value is None:
                    continue
                try:
                    time_str = p.get("time")
                    measured_at = datetime.fromisoformat(
                        time_str.replace("Z", "+00:00")
                    ) if time_str else datetime.utcnow()

                    for tid in territory_ids:
                        db.add(EcologicalMeasurement(
                            territory_id=tid,
                            indicator_type=PARAMETER_MAP[pol_name],
                            value=float(value),
                            unit=UNIT_MAP.get(pol_name, ""),
                            measured_at=measured_at,
                            source=EcoDataSource.saveecobot
                        ))
                    imported += len(territory_ids)
                except Exception:
                    continue

        db.commit()

        if imported == 0:
            return {"success": False, "error": "Дані є але не вдалось імпортувати"}

        return {
            "success": True,
            "imported": imported,
            "city": city,
            "stations_found": len(matching),
            "territories_updated": len(territory_ids),
            "used_nearest": used_nearest,
            "nearest_city": nearest_city_name,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}