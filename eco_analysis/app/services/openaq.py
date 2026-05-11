import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ecological import EcologicalMeasurement, EcoIndicatorType, EcoDataSource
from app.core.config import settings

OPENAQ_BASE_URL = "https://api.openaq.org/v3"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

PARAMETER_MAP = {
    "pm25": EcoIndicatorType.pm25,
    "pm10": EcoIndicatorType.pm10,
}

async def get_city_coordinates(city: str) -> tuple:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            NOMINATIM_URL,
            params={
                "q": f"{city}, Ukraine",
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": "eco-analysis-system/1.0"},
            timeout=10.0
        )
        results = response.json()
        if not results:
            response = await client.get(
                NOMINATIM_URL,
                params={"q": city, "format": "json", "limit": 1},
                headers={"User-Agent": "eco-analysis-system/1.0"},
                timeout=10.0
            )
            results = response.json()
        if not results:
            return None, None
        return float(results[0]["lat"]), float(results[0]["lon"])

async def fetch_openaq_data(
    city: str,
    territory_id: int,
    db: Session,
    limit: int = 50
) -> dict:
    try:
        headers = {"X-API-Key": settings.OPENAQ_API_KEY}

        lat, lon = await get_city_coordinates(city)
        if lat is None:
            return {"success": False, "error": f"Місто '{city}' не знайдено"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENAQ_BASE_URL}/locations",
                params={
                    "coordinates": f"{lat},{lon}",
                    "radius": 25000,
                    "limit": 5
                },
                headers=headers,
                timeout=15.0
            )

            if response.status_code != 200:
                return {"success": False, "error": f"OpenAQ API помилка: {response.status_code}"}

            locations = response.json().get("results", [])
            if not locations:
                return {"success": False, "error": f"Станцій поблизу '{city}' не знайдено"}

            imported = 0
            for location in locations[:3]:
                for sensor in location.get("sensors", []):
                    parameter = sensor.get("parameter", {}).get("name", "").lower()
                    if parameter not in PARAMETER_MAP:
                        continue

                    sensor_id = sensor.get("id")
                    m_response = await client.get(
                        f"{OPENAQ_BASE_URL}/sensors/{sensor_id}/measurements",
                        params={"limit": 20},
                        headers=headers,
                        timeout=15.0
                    )

                    if m_response.status_code != 200:
                        continue

                    for m in m_response.json().get("results", []):
                        try:
                            value = m.get("value")
                            date_str = m.get("period", {}).get("datetimeFrom", {}).get("utc")
                            if value is None or not date_str:
                                continue

                            measurement = EcologicalMeasurement(
                                territory_id=territory_id,
                                indicator_type=PARAMETER_MAP[parameter],
                                value=float(value),
                                unit=sensor.get("parameter", {}).get("units", ""),
                                measured_at=datetime.fromisoformat(
                                    date_str.replace("Z", "+00:00")
                                ),
                                source=EcoDataSource.openaq
                            )
                            db.add(measurement)
                            imported += 1
                        except Exception:
                            continue

            db.commit()

            if imported == 0:
                return {"success": False, "error": "Даних не знайдено — сенсори не мають вимірювань"}

            return {"success": True, "imported": imported, "city": city, "coordinates": {"lat": lat, "lon": lon}}

    except Exception as e:
        return {"success": False, "error": str(e)}