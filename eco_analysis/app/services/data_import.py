import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ecological import EcologicalMeasurement, EcoIndicatorType, EcoDataSource
from app.models.economic import EconomicMeasurement, EconIndicatorType, EconDataSource
from app.models.territory import Territory



ECO_INDICATOR_ALIASES = {
    "якість води": "turbidity", "water_quality": "turbidity",
    "turbidity": "turbidity", "мутність": "turbidity",
    "ph_water": "turbidity", "ph": "turbidity", "ph води": "turbidity",
    "zavisli": "turbidity", "завислі речовини": "turbidity",
    "bsk5": "turbidity", "sulfat": "turbidity", "сульфати": "turbidity",
    "hlorid": "turbidity", "хлориди": "turbidity",
    "nitrat": "turbidity", "нітрати": "turbidity",
    "nitrit": "turbidity", "нітрити": "turbidity",
    "fosfat": "turbidity", "фосфати": "turbidity",
    "amoniy": "turbidity", "амоній": "turbidity",
    "pm2.5": "PM2.5", "pm25": "PM2.5", "пм2.5": "PM2.5", "pm 2.5": "PM2.5",
    "pm10": "PM10", "пм10": "PM10", "pm 10": "PM10",
    "aqi": "AQI", "air quality index": "AQI", "індекс якості повітря": "AQI",
    "temperature": "temperature", "температура": "temperature",
    "humidity": "humidity", "вологість": "humidity",
    "pressure": "pressure", "тиск": "pressure",
}


ECON_INDICATOR_ALIASES = {
    "gdp": "gdp", "ввп": "gdp", "врп": "gdp",
    "валовий регіональний продукт": "gdp",
    "валовий внутрішній продукт": "gdp",
    "salary": "salary", "зарплата": "salary",
    "заробітна плата": "salary", "зп": "salary",
    "середня заробітна плата": "salary",
    "unemployment": "unemployment", "безробіття": "unemployment",
    "рівень безробіття": "unemployment",
    "enterprises": "enterprises", "підприємства": "enterprises",
    "кількість підприємств": "enterprises",
    "healthcare": "healthcare", "охорона здоров'я": "healthcare",
    "витрати на охорону здоров'я": "healthcare",
    "investments": "investments", "інвестиції": "investments",
    "прямі інвестиції": "investments",
    "прямі іноземні інвестиції": "investments",
}


REGION_COORDS = {
    "Вінницька область":         (49.2331, 28.4682),
    "Волинська область":         (50.7472, 25.3254),
    "Дніпропетровська область":  (48.4647, 35.0462),
    "Донецька область":          (48.0159, 37.8028),
    "Житомирська область":       (50.2547, 28.6587),
    "Закарпатська область":      (48.6208, 22.2879),
    "Запорізька область":        (47.8388, 35.1396),
    "Івано-Франківська область": (48.9226, 24.7111),
    "Київська область":          (50.0529, 30.7667),
    "Кіровоградська область":    (48.5079, 32.2623),
    "Луганська область":         (48.5740, 39.3078),
    "Львівська область":         (49.8397, 24.0297),
    "Миколаївська область":      (46.9750, 31.9946),
    "Одеська область":           (46.4825, 30.7233),
    "Полтавська область":        (49.5883, 34.5514),
    "Рівненська область":        (50.6197, 26.2513),
    "Сумська область":           (50.9077, 34.7981),
    "Тернопільська область":     (49.5535, 25.5948),
    "Харківська область":        (49.9935, 36.2304),
    "Херсонська область":        (46.6354, 32.6169),
    "Хмельницька область":       (49.4229, 26.9871),
    "Черкаська область":         (49.4285, 32.0598),
    "Чернівецька область":       (48.2921, 25.9358),
    "Чернігівська область":      (51.4982, 31.2893),
    "Київ":                      (50.4501, 30.5234),
}



def normalize_region_name(raw: str) -> str | None:
    if not raw or str(raw).strip() in ("", "nan", "None"):
        return None
    raw = str(raw).strip()
    if "область" in raw.lower():
        return raw[0].upper() + raw[1:]
    key = raw.lower().strip()
    for region_name in REGION_COORDS.keys():
        first_word = region_name.split()[0].lower()
        if first_word in key or key in first_word:
            return region_name
    return raw


def normalize_indicator(value: str, aliases: dict) -> str | None:
    if not value:
        return None
    key = str(value).lower().strip()
    return aliases.get(key, str(value).strip())


def detect_columns(df: pd.DataFrame) -> dict:
    cols = {str(c).lower().strip(): c for c in df.columns}
    result = {}
    for alias in ["indicator_type", "indicator", "тип", "показник", "назва"]:
        if alias in cols:
            result["indicator_type"] = cols[alias]
            break
    for alias in ["value", "значення", "величина", "val", "amount", "data", "дані"]:
        if alias in cols:
            result["value"] = cols[alias]
            break
    for alias in ["measured_at", "date", "дата", "period", "час", "time", "рік", "year", "місяць"]:
        if alias in cols:
            result["date"] = cols[alias]
            break
    for alias in ["unit", "одиниця", "од", "одиниця виміру"]:
        if alias in cols:
            result["unit"] = cols[alias]
            break
    for alias in ["region", "регіон", "область", "місто", "city", "territory", "attributes"]:
        if alias in cols:
            result["region"] = cols[alias]
            break
    return result


def read_csv_safe(file_path: str) -> pd.DataFrame:
    for enc in ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']:
        for sep in [',', ';', '\t']:
            try:
                df = pd.read_csv(file_path, encoding=enc, sep=sep, on_bad_lines='skip')
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
    raise ValueError("Не вдалось прочитати файл - перевірте формат CSV")


def get_territories_for_region(db: Session, region_name: str) -> list:
    if not region_name:
        return []

    territories = []

    if "область" in region_name.lower():
        # Шукаємо всі міста цієї області
        cities = db.query(Territory).filter(
            Territory.region == region_name
        ).all()
        territories.extend(cities)

        # Також шукаємо саму область як окрему територію
        oblast_territory = db.query(Territory).filter(
            Territory.name == region_name
        ).first()
        if oblast_territory and oblast_territory not in territories:
            territories.append(oblast_territory)

        # Якщо взагалі нічого не знайдено — шукаємо по першому слову
        if not territories:
            first_word = region_name.split()[0]
            if len(first_word) > 3:
                cities = db.query(Territory).filter(
                    Territory.region.ilike(f"%{first_word}%")
                ).all()
                territories.extend(cities)

        # Якщо досі нічого створюємо нову область
        if not territories:
            coords = REGION_COORDS.get(region_name, (None, None))
            new_t = Territory(
                name=region_name,
                region=region_name,
                latitude=coords[0],
                longitude=coords[1],
            )
            db.add(new_t)
            db.flush()
            territories.append(new_t)

    else:
        # Це конкретне місто шукаємо точно
        territory = db.query(Territory).filter(
            Territory.name == region_name
        ).first()
        if not territory:
            # Часткове співпадіння
            first_word = region_name.split()[0]
            territory = db.query(Territory).filter(
                Territory.name.ilike(f"%{first_word}%")
            ).first()
        if not territory:
            coords = REGION_COORDS.get(region_name, (None, None))
            territory = Territory(
                name=region_name,
                region=region_name,
                latitude=coords[0],
                longitude=coords[1],
            )
            db.add(territory)
            db.flush()
        territories.append(territory)

    return territories



def import_ecological_csv(
    file_path: str,
    territory_id: int | None,
    db: Session,
    column_mapping: dict = None
) -> dict:
    try:
        df = read_csv_safe(file_path)
        detected = detect_columns(df)
        mapping = column_mapping or detected

        col_indicator = mapping.get("indicator_type")
        col_value     = mapping.get("value")
        col_date      = mapping.get("date")
        col_unit      = mapping.get("unit")
        col_region    = mapping.get("region")

        if not col_value or col_value not in df.columns:
            return {
                "success": False,
                "error": f"Не знайдено колонку зі значеннями. Доступні: {list(df.columns)}"
            }

        imported = errors = skipped = 0

        for _, row in df.iterrows():
            try:
                # Визначаємо список territory_id
                if territory_id is not None:
                    territory_ids = [territory_id]
                elif col_region and col_region in df.columns:
                    raw_region = str(row[col_region])
                    region_name = normalize_region_name(raw_region) or raw_region
                    territories = get_territories_for_region(db, region_name)
                    territory_ids = [t.id for t in territories]
                else:
                    skipped += 1
                    continue

                if not territory_ids:
                    skipped += 1
                    continue

                if col_indicator and col_indicator in df.columns:
                    ind_str = normalize_indicator(str(row[col_indicator]), ECO_INDICATOR_ALIASES)
                else:
                    ind_str = "turbidity"

                try:
                    indicator_type = EcoIndicatorType(ind_str)
                except ValueError:
                    skipped += 1
                    continue

                raw_val = str(row[col_value]).replace(',', '.').replace(' ', '').replace('\xa0', '')
                value = float(raw_val)

                if col_date and col_date in df.columns:
                    try:
                        measured_at = pd.to_datetime(row[col_date])
                    except Exception:
                        measured_at = datetime.utcnow()
                else:
                    measured_at = datetime.utcnow()

                unit = str(row[col_unit]) if col_unit and col_unit in df.columns else None

                # Додаємо запис для КОЖНОЇ території цього регіону
                for tid in territory_ids:
                    db.add(EcologicalMeasurement(
                        territory_id=tid,
                        indicator_type=indicator_type,
                        value=value,
                        unit=unit,
                        measured_at=measured_at,
                        source=EcoDataSource.csv,
                    ))
                    imported += 1

            except Exception:
                errors += 1
                continue

        db.commit()
        return {
            "success": True,
            "imported": imported,
            "errors": errors,
            "skipped": skipped,
            "detected_columns": detected,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}



def import_economic_csv(
    file_path: str,
    territory_id: int | None,
    db: Session,
    column_mapping: dict = None
) -> dict:
    try:
        df = read_csv_safe(file_path)
        detected = detect_columns(df)
        mapping = column_mapping or detected

        col_indicator = mapping.get("indicator_type")
        col_value     = mapping.get("value")
        col_period    = mapping.get("date")
        col_unit      = mapping.get("unit")
        col_region    = mapping.get("region")

        if not col_value or col_value not in df.columns:
            return {
                "success": False,
                "error": f"Не знайдено колонку зі значеннями. Доступні: {list(df.columns)}"
            }

        imported = errors = skipped = 0

        for _, row in df.iterrows():
            try:
                if territory_id is not None:
                    territory_ids = [territory_id]
                elif col_region and col_region in df.columns:
                    raw_region = str(row[col_region])
                    region_name = normalize_region_name(raw_region) or raw_region
                    territories = get_territories_for_region(db, region_name)
                    territory_ids = [t.id for t in territories]
                else:
                    skipped += 1
                    continue

                if not territory_ids:
                    skipped += 1
                    continue

                if col_indicator and col_indicator in df.columns:
                    ind_str = normalize_indicator(str(row[col_indicator]), ECON_INDICATOR_ALIASES)
                else:
                    ind_str = "gdp"

                try:
                    indicator_type = EconIndicatorType(ind_str)
                except ValueError:
                    skipped += 1
                    continue

                raw_val = str(row[col_value]).replace(',', '.').replace(' ', '').replace('\xa0', '')
                value = float(raw_val)

                period = str(row[col_period]) if col_period and col_period in df.columns else str(datetime.utcnow().year)
                unit = str(row[col_unit]) if col_unit and col_unit in df.columns else None

                for tid in territory_ids:
                    db.add(EconomicMeasurement(
                        territory_id=tid,
                        indicator_type=indicator_type,
                        value=value,
                        unit=unit,
                        period=period,
                        source=EconDataSource.csv,
                    ))
                    imported += 1

            except Exception:
                errors += 1
                continue

        db.commit()
        return {
            "success": True,
            "imported": imported,
            "errors": errors,
            "skipped": skipped,
            "detected_columns": detected,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}



def preview_csv(file_path: str) -> dict:
    try:
        df = read_csv_safe(file_path)
        detected = detect_columns(df)
        return {
            "success": True,
            "columns": list(df.columns),
            "preview": df.head(5).fillna("").to_dict(orient="records"),
            "detected_mapping": detected,
            "total_rows": len(df),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}