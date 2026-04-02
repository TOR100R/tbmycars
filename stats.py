"""Statistics calculations for the garage bot."""
from datetime import datetime
from database import Database

db = Database()


def get_car_stats(car_id: int) -> dict:
    """Calculate cost statistics for a car."""
    events = db.get_events(car_id, limit=500)
    taxes = db.get_scheduler_config()  # not used here
    car = db.get_car(car_id)

    total_cost = 0.0
    by_year = {}
    by_category = {}
    event_count = 0

    category_map = {
        "aceite": "🔧 Mecánico",
        "filtro": "🔧 Mecánico",
        "frenos": "🔧 Mecánico",
        "correa": "🔧 Mecánico",
        "bujías": "🔧 Mecánico",
        "amortiguador": "🔧 Mecánico",
        "embrague": "🔧 Mecánico",
        "batería": "🔧 Mecánico",
        "mecánico": "🔧 Mecánico",
        "reparación": "🛠️ Reparación",
        "neumático": "🛞 Neumáticos",
        "rotación": "🛞 Neumáticos",
        "alineación": "🛞 Neumáticos",
        "limpieza": "🧹 Cuidado",
        "tratamiento": "🧹 Cuidado",
        "nivel": "🔍 Niveles",
        "itv": "📋 ITV",
        "revisión": "🔩 Revisión",
        "repostaje": "⛽ Repostaje",
    }

    for e in events:
        if not e['cost']:
            continue
        cost = float(e['cost'])
        total_cost += cost
        event_count += 1

        # By year
        try:
            year = datetime.strptime(e['date'], "%d/%m/%Y").year
            by_year[year] = by_year.get(year, 0.0) + cost
        except:
            pass

        # By category
        etype = e['event_type'].lower()
        cat = "🔧 Mecánico"
        for keyword, c in category_map.items():
            if keyword in etype:
                cat = c
                break
        by_category[cat] = by_category.get(cat, 0.0) + cost

    # Cost per km
    cost_per_km = None
    if car and car['km'] and car['km'] > 0 and total_cost > 0:
        cost_per_km = total_cost / car['km']

    return {
        "total_cost": total_cost,
        "event_count": event_count,
        "by_year": dict(sorted(by_year.items(), reverse=True)),
        "by_category": dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True)),
        "cost_per_km": cost_per_km,
    }


def format_stats_text(car, stats: dict) -> str:
    text = f"📊 *Estadísticas — {car['brand']} {car['model']}*\n\n"

    if stats['total_cost'] == 0:
        text += "Sin costes registrados aún.\n"
        text += "_Añade costes al registrar mantenimientos._"
        return text

    text += f"💶 *Coste total registrado:* {stats['total_cost']:.2f}€\n"
    text += f"📝 *Operaciones con coste:* {stats['event_count']}\n"
    if stats['cost_per_km']:
        text += f"📏 *Coste por km:* {stats['cost_per_km']:.4f}€/km\n"
    text += "\n"

    if stats['by_year']:
        text += "📅 *Por año:*\n"
        for year, cost in stats['by_year'].items():
            text += f"  {year}: {cost:.2f}€\n"
        text += "\n"

    if stats['by_category']:
        text += "🗂️ *Por categoría:*\n"
        for cat, cost in stats['by_category'].items():
            pct = (cost / stats['total_cost'] * 100) if stats['total_cost'] else 0
            text += f"  {cat}: {cost:.2f}€ ({pct:.0f}%)\n"

    return text
