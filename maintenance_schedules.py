"""
Maintenance schedules by brand.
Each entry: (description, interval_km, interval_months)
interval_km=0 means time-based only, interval_months=0 means km-based only.
"""
from datetime import datetime, timedelta

DEFAULT_SCHEDULE = [
    ("Cambio de aceite y filtro",        15000, 12),
    ("Filtro de aire",                   30000, 24),
    ("Filtro de habitáculo",             15000, 12),
    ("Filtro de combustible",            60000, 48),
    ("Revisión de frenos",               30000, 24),
    ("Rotación de neumáticos",           10000,  6),
    ("Bujías",                           60000, 48),
    ("Correa de distribución",          120000, 72),
    ("Líquido de frenos",                    0, 24),
    ("Líquido refrigerante",                 0, 48),
    ("Batería",                              0, 48),
    ("Revisión general",                 30000, 24),
]

BRAND_SCHEDULES = {
    "opel": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Líquido refrigerante",             0, 48),
        ("Revisión general Opel",        30000, 24),
    ],
    "volkswagen": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Filtro de combustible",        60000, 48),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa / cadena distribución",120000, 72),
        ("Aceite caja DSG",              60000, 48),
        ("Líquido de frenos",                0, 24),
        ("Revisión Service WIV",         15000, 12),
    ],
    "seat": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general SEAT",        30000, 24),
    ],
    "renault": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Líquido refrigerante",             0, 48),
        ("Revisión general Renault",     30000, 24),
    ],
    "peugeot": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Peugeot",     30000, 24),
    ],
    "citroen": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Citroën",     30000, 24),
    ],
    "toyota": [
        ("Cambio de aceite y filtro",    10000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Cadena distribución (rev.)",   60000, 48),
        ("Líquido de frenos",                0, 24),
        ("Líquido refrigerante",             0, 48),
        ("Revisión general Toyota",      10000, 12),
    ],
    "ford": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Ford",        20000, 12),
    ],
    "bmw": [
        ("Cambio de aceite y filtro",    25000, 12),
        ("Filtro de aire",               60000, 36),
        ("Filtro de habitáculo",         25000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Cadena distribución (rev.)",   60000, 48),
        ("Líquido de frenos",                0, 24),
        ("Líquido refrigerante",             0, 48),
        ("Inspección I BMW",             25000, 12),
        ("Inspección II BMW",            50000, 24),
    ],
    "mercedes": [
        ("Cambio de aceite y filtro",    25000, 12),
        ("Filtro de aire",               40000, 24),
        ("Filtro de habitáculo",         20000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Líquido de frenos",                0, 24),
        ("Líquido refrigerante",             0, 48),
        ("Service A Mercedes",           25000, 12),
        ("Service B Mercedes",           50000, 24),
    ],
    "audi": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa / cadena distribución",120000, 72),
        ("Aceite caja DSG",              60000, 48),
        ("Líquido de frenos",                0, 24),
        ("Inspección menor Audi",        15000, 12),
        ("Inspección mayor Audi",        30000, 24),
    ],
    "honda": [
        ("Cambio de aceite y filtro",    10000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       45000, 36),
        ("Correa de distribución",       90000, 60),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Honda",       10000, 12),
    ],
    "hyundai": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 60),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Hyundai",     15000, 12),
    ],
    "kia": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 60),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Kia",         15000, 12),
    ],
    "nissan": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      105000, 60),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Nissan",      15000, 12),
    ],
    "fiat": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 60),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Fiat",        15000, 12),
    ],
    "skoda": [
        ("Cambio de aceite y filtro",    15000, 12),
        ("Filtro de aire",               30000, 24),
        ("Filtro de habitáculo",         15000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Skoda",       15000, 12),
    ],
    "volvo": [
        ("Cambio de aceite y filtro",    20000, 12),
        ("Filtro de aire",               40000, 24),
        ("Filtro de habitáculo",         20000, 12),
        ("Revisión de frenos",           30000, 24),
        ("Bujías",                       60000, 48),
        ("Correa de distribución",      120000, 72),
        ("Líquido de frenos",                0, 24),
        ("Revisión general Volvo",       20000, 12),
    ],
}


def get_schedule(brand: str):
    return BRAND_SCHEDULES.get(brand.lower().strip(), DEFAULT_SCHEDULE)


def get_service_timeline(brand: str, current_km: int, year: int, done_events: list):
    """
    Returns:
      - last_2: last 2 completed maintenance items (from done_events)
      - next_5: next 5 upcoming maintenance items sorted by urgency
    """
    schedule = get_schedule(brand)
    now = datetime.now()
    car_age_months = (now.year - year) * 12 + (now.month - 1)

    # Build a set of completed event types (lowercase) for matching
    done_types = {}
    for e in done_events:
        key = e['event_type'].lower()
        if key not in done_types or e['date'] > done_types[key]['date']:
            done_types[key] = e

    # Last 2 completed — most recent first
    completed_sorted = sorted(done_events, key=lambda x: x['date'], reverse=True)
    last_2 = completed_sorted[:2]

    # Next 5 upcoming
    upcoming = []
    for desc, interval_km, interval_months in schedule:
        # Find if this task was done before
        match = None
        for key, ev in done_types.items():
            if desc.lower() in key or key in desc.lower():
                match = ev
                break

        # Next due by km
        if interval_km > 0:
            if match and match.get('km'):
                next_km = match['km'] + interval_km
            else:
                cycles = current_km // interval_km
                next_km = (cycles + 1) * interval_km
            km_left = next_km - current_km
        else:
            next_km = None
            km_left = None

        # Next due by date
        if interval_months > 0:
            if match:
                try:
                    last_date = datetime.strptime(match['date'], "%d/%m/%Y")
                    next_date = last_date + timedelta(days=interval_months * 30)
                except:
                    cycles_m = car_age_months // interval_months
                    months_left = interval_months - (car_age_months % interval_months)
                    next_date = now + timedelta(days=months_left * 30)
            else:
                cycles_m = car_age_months // interval_months
                months_left = interval_months - (car_age_months % interval_months)
                next_date = now + timedelta(days=months_left * 30)
            days_left = (next_date - now).days
        else:
            next_date = None
            days_left = None

        # Urgency score (lower = more urgent)
        urgency_scores = []
        if km_left is not None and interval_km > 0:
            urgency_scores.append(km_left / interval_km)
        if days_left is not None:
            urgency_scores.append(days_left / (interval_months * 30))
        urgency = min(urgency_scores) if urgency_scores else 999

        upcoming.append({
            "description": desc,
            "next_km": next_km,
            "next_date": next_date.strftime("%d/%m/%Y") if next_date else None,
            "km_left": km_left,
            "days_left": days_left,
            "urgency": urgency,
            "overdue": urgency < 0,
        })

    upcoming.sort(key=lambda x: x['urgency'])
    return last_2, upcoming[:5]
