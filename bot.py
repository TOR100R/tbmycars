import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
db = Database()

# States
(MENU, ADD_CAR_BRAND, ADD_CAR_MODEL, ADD_CAR_PLATE, ADD_CAR_YEAR, ADD_CAR_KM, ADD_CAR_FUEL,
 SELECT_CAR, ADD_EVENT_TYPE, ADD_EVENT_DATE, ADD_EVENT_KM, ADD_EVENT_COST, ADD_EVENT_NOTES,
 ADD_EVENT_NEXT_DATE, ADD_EVENT_NEXT_KM, UPDATE_KM,
 ADD_INS_COMPANY, ADD_INS_POLICY, ADD_INS_EXPIRY, ADD_INS_COST,
 ADD_TAX_AMOUNT, ADD_TAX_EXPIRY,
 ADD_CLAIM_DATE, ADD_CLAIM_DESC, ADD_CLAIM_NUMBER, ADD_CLAIM_STATUS) = range(26)

FUEL_TYPES = ["Gasolina", "Diésel", "Híbrido", "Eléctrico", "GLP"]

EVENT_CATEGORIES = {
    "🔧 Mecánico": ["Cambio de aceite", "Filtro de aire", "Filtro de combustible",
                    "Filtro de habitáculo", "Frenos delanteros", "Frenos traseros",
                    "Correa de distribución", "Bujías", "Amortiguadores", "Embrague",
                    "Batería", "Otro mecánico"],
    "🛞 Neumáticos": ["Cambio neumáticos", "Rotación neumáticos",
                      "Control presión", "Alineación / Equilibrado"],
    "🧹 Cuidado": ["Limpieza exterior", "Limpieza interior", "Limpieza completa",
                   "Tratamiento pintura", "Tratamiento tapicería"],
    "🔍 Niveles": ["Nivel aceite", "Nivel refrigerante", "Nivel frenos",
                   "Nivel limpiaparabrisas", "Revisión general niveles"],
    "📋 ITV": ["ITV pasada", "ITV fallida", "Cita ITV"],
    "🔩 Revisión fabricante": ["Revisión 15.000 km", "Revisión 30.000 km",
                                "Revisión 60.000 km", "Revisión anual"],
    "⛽ Repostaje": ["Repostaje combustible"],
    "🛠️ Reparación": ["Reparación carrocería", "Reparación eléctrica", "Otra reparación"],
}


def main_kb(cars):
    kb = []
    if cars:
        kb += [
            [InlineKeyboardButton("🚗 Mis coches", callback_data="list_cars"),
             InlineKeyboardButton("⚠️ Alertas", callback_data="view_alerts")],
            [InlineKeyboardButton("📝 Registrar mantenimiento", callback_data="add_event")],
            [InlineKeyboardButton("📊 Ver historial", callback_data="view_history"),
             InlineKeyboardButton("📏 Actualizar km", callback_data="update_km")],
            [InlineKeyboardButton("🛡️ Seguros y admin", callback_data="admin_menu")],
        ]
    kb.append([InlineKeyboardButton("➕ Añadir coche", callback_data="add_car")])
    return InlineKeyboardMarkup(kb)


def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menú principal", callback_data="back_main")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cars = db.get_cars()
    n = len(cars)
    text = "🚗 *Mi Garaje*\n\n"
    text += "No tienes coches registrados aún." if not n else f"Tienes *{n}* coche(s) registrado(s)."
    await update.message.reply_text(text, reply_markup=main_kb(cars), parse_mode="Markdown")
    return MENU


async def back_to_main(query, context):
    cars = db.get_cars()
    await query.edit_message_text("🚗 *Mi Garaje* — Menú principal",
                                  reply_markup=main_kb(cars), parse_mode="Markdown")
    context.user_data.clear()
    return MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data

    if d == "back_main":
        return await back_to_main(q, context)

    if d == "add_car":
        await q.edit_message_text("🚗 Nuevo coche\n\n¿Cuál es la *marca*? (ej: Opel, Toyota...)", parse_mode="Markdown")
        return ADD_CAR_BRAND

    if d == "list_cars":
        cars = db.get_cars()
        if not cars:
            await q.edit_message_text("No tienes coches.", reply_markup=back_kb())
            return MENU
        text = "🚗 *Tus coches:*\n\n"
        for c in cars:
            alts = db.get_pending_alerts(c['id'])
            icon = "⚠️ " if alts else "✅ "
            text += f"{icon}*{c['brand']} {c['model']}* — `{c['plate']}`\n"
            text += f"  📅 {c['year']} | ⛽ {c['fuel']} | 📏 {c['km']:,} km\n\n"
        await q.edit_message_text(text, reply_markup=back_kb(), parse_mode="Markdown")
        return MENU

    if d == "view_alerts":
        cars = db.get_cars()
        text = "⚠️ *Alertas pendientes:*\n\n"
        found = False
        for c in cars:
            alts = db.get_pending_alerts(c['id'])
            if alts:
                found = True
                text += f"🚗 *{c['brand']} {c['model']}*\n"
                for a in alts:
                    text += f"  {a}\n"
                text += "\n"
        if not found:
            text = "✅ Sin alertas pendientes. ¡Todo en orden!"
        await q.edit_message_text(text, reply_markup=back_kb(), parse_mode="Markdown")
        return MENU

    if d in ("add_event", "update_km", "view_history"):
        context.user_data['action'] = d
        return await ask_select_car(q, context)

    if d == "admin_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛡️ Registrar seguro", callback_data="ins_select")],
            [InlineKeyboardButton("💰 Impuesto circulación", callback_data="tax_select")],
            [InlineKeyboardButton("🚨 Parte al seguro", callback_data="claim_select")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_main")],
        ])
        await q.edit_message_text("🛡️ *Seguros y administración*", reply_markup=kb, parse_mode="Markdown")
        return MENU

    if d in ("ins_select", "tax_select", "claim_select"):
        context.user_data['action'] = d
        return await ask_select_car(q, context)

    return MENU


async def ask_select_car(q, context):
    cars = db.get_cars()
    if not cars:
        await q.edit_message_text("Primero añade un coche.", reply_markup=back_kb())
        return MENU
    kb = [[InlineKeyboardButton(f"🚗 {c['brand']} {c['model']} ({c['plate']})",
                                 callback_data=f"sc_{c['id']}")] for c in cars]
    kb.append([InlineKeyboardButton("⬅️ Cancelar", callback_data="back_main")])
    await q.edit_message_text("¿Para qué coche?", reply_markup=InlineKeyboardMarkup(kb))
    return SELECT_CAR


async def select_car_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back_main":
        return await back_to_main(q, context)

    car_id = int(q.data.split("_")[1])
    context.user_data['car_id'] = car_id
    action = context.user_data.get('action')
    car = db.get_car(car_id)

    if action == "add_event":
        kb = [[InlineKeyboardButton(cat, callback_data=f"cat_{i}")]
              for i, cat in enumerate(EVENT_CATEGORIES)]
        kb.append([InlineKeyboardButton("⬅️ Cancelar", callback_data="back_main")])
        await q.edit_message_text(f"🚗 *{car['brand']} {car['model']}*\n\n¿Qué tipo de mantenimiento?",
                                   reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return ADD_EVENT_TYPE

    if action == "update_km":
        await q.edit_message_text(
            f"📏 *{car['brand']} {car['model']}*\nKm actuales: *{car['km']:,}*\n\n¿Cuántos km tiene ahora?",
            parse_mode="Markdown")
        return UPDATE_KM

    if action == "view_history":
        events = db.get_events(car_id)
        claims = db.get_claims(car_id)
        ins_list = db.get_insurance(car_id)
        text = f"📊 *Historial — {car['brand']} {car['model']}*\n\n"
        if ins_list:
            ins = ins_list[0]
            text += f"🛡️ *Seguro:* {ins['company']} | Póliza: `{ins['policy']}`\n"
            text += f"  Vence: {ins['expiry']} | Prima: {ins['cost']}€\n\n"
        if events:
            text += "📝 *Últimos mantenimientos:*\n"
            for e in events[:15]:
                text += f"• {e['date']} — {e['event_type']}"
                if e['km']:
                    text += f" ({e['km']:,} km)"
                if e['cost']:
                    text += f" — {e['cost']}€"
                text += "\n"
        if claims:
            text += f"\n🚨 *Partes al seguro:* {len(claims)}\n"
            for cl in claims[:3]:
                text += f"• {cl['date']} — {cl['description'][:30]} [{cl['status']}]\n"
        if not events and not ins_list and not claims:
            text += "Sin registros aún."
        await q.edit_message_text(text, reply_markup=back_kb(), parse_mode="Markdown")
        return MENU

    if action == "ins_select":
        await q.edit_message_text("🛡️ ¿Cuál es la compañía aseguradora?")
        return ADD_INS_COMPANY

    if action == "tax_select":
        await q.edit_message_text("💰 ¿Cuánto pagaste de impuesto de circulación? (€)")
        return ADD_TAX_AMOUNT

    if action == "claim_select":
        await q.edit_message_text("🚨 ¿Cuándo ocurrió el siniestro? (DD/MM/AAAA o 'hoy')")
        return ADD_CLAIM_DATE

    return MENU


# --- ADD CAR ---
async def add_car_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text.strip()
    await update.message.reply_text("¿Cuál es el *modelo*?", parse_mode="Markdown")
    return ADD_CAR_MODEL

async def add_car_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['model'] = update.message.text.strip()
    await update.message.reply_text("¿Cuál es la *matrícula*?", parse_mode="Markdown")
    return ADD_CAR_PLATE

async def add_car_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['plate'] = update.message.text.strip().upper()
    await update.message.reply_text("¿De qué *año* es?", parse_mode="Markdown")
    return ADD_CAR_YEAR

async def add_car_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        y = int(update.message.text.strip())
        assert 1950 <= y <= datetime.now().year + 1
        context.user_data['year'] = y
        await update.message.reply_text("¿Cuántos *km* tiene actualmente?", parse_mode="Markdown")
        return ADD_CAR_KM
    except:
        await update.message.reply_text("Año no válido. Inténtalo de nuevo (ej: 2019).")
        return ADD_CAR_YEAR

async def add_car_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        context.user_data['km'] = km
        kb = [[InlineKeyboardButton(f, callback_data=f"fuel_{f}")] for f in FUEL_TYPES]
        await update.message.reply_text("¿Qué combustible usa?", reply_markup=InlineKeyboardMarkup(kb))
        return ADD_CAR_FUEL
    except:
        await update.message.reply_text("Número no válido. Inténtalo de nuevo.")
        return ADD_CAR_KM

async def add_car_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    fuel = q.data.replace("fuel_", "")
    d = context.user_data
    db.add_car(d['brand'], d['model'], d['plate'], d['year'], d['km'], fuel)
    cars = db.get_cars()
    await q.edit_message_text(
        f"✅ *{d['brand']} {d['model']}* añadido.\n`{d['plate']}` | {d['year']} | {d['km']:,} km | {fuel}",
        reply_markup=main_kb(cars), parse_mode="Markdown")
    context.user_data.clear()
    return MENU


# --- UPDATE KM ---
async def update_km_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        car_id = context.user_data['car_id']
        car = db.get_car(car_id)
        if km < car['km']:
            await update.message.reply_text(
                f"⚠️ Los km introducidos ({km:,}) son menores que los actuales ({car['km']:,}). ¿Es correcto? Escríbelo de nuevo o confirma con el mismo valor.")
            return UPDATE_KM
        db.update_km(car_id, km)
        cars = db.get_cars()
        await update.message.reply_text(
            f"✅ Km actualizados: *{car['brand']} {car['model']}* → *{km:,} km*",
            reply_markup=main_kb(cars), parse_mode="Markdown")
        context.user_data.clear()
        return MENU
    except:
        await update.message.reply_text("Número no válido.")
        return UPDATE_KM


# --- ADD EVENT ---
async def add_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back_main":
        return await back_to_main(q, context)

    cats = list(EVENT_CATEGORIES.keys())

    if q.data.startswith("cat_"):
        idx = int(q.data[4:])
        cat = cats[idx]
        context.user_data['event_cat'] = cat
        events = EVENT_CATEGORIES[cat]
        kb = [[InlineKeyboardButton(e, callback_data=f"evt_{i}")] for i, e in enumerate(events)]
        kb.append([InlineKeyboardButton("⬅️ Volver", callback_data="back_cats")])
        await q.edit_message_text(f"*{cat}*\n\n¿Qué operación?",
                                   reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return ADD_EVENT_TYPE

    if q.data == "back_cats":
        kb = [[InlineKeyboardButton(cat, callback_data=f"cat_{i}")]
              for i, cat in enumerate(EVENT_CATEGORIES)]
        kb.append([InlineKeyboardButton("⬅️ Cancelar", callback_data="back_main")])
        await q.edit_message_text("¿Qué tipo de mantenimiento?", reply_markup=InlineKeyboardMarkup(kb))
        return ADD_EVENT_TYPE

    if q.data.startswith("evt_"):
        cat = context.user_data.get('event_cat', '')
        events = EVENT_CATEGORIES.get(cat, [])
        idx = int(q.data[4:])
        context.user_data['event_type'] = events[idx]
        await q.edit_message_text(
            f"📝 *{events[idx]}*\n\n¿Cuándo se realizó? (DD/MM/AAAA o 'hoy')",
            parse_mode="Markdown")
        return ADD_EVENT_DATE

    return ADD_EVENT_TYPE


async def add_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    date = datetime.now().strftime("%d/%m/%Y") if txt == "hoy" else txt
    try:
        datetime.strptime(date, "%d/%m/%Y")
        context.user_data['event_date'] = date
        await update.message.reply_text("📏 ¿Cuántos km tenía en ese momento? (o escribe '-' para omitir)")
        return ADD_EVENT_KM
    except:
        await update.message.reply_text("Formato incorrecto. Usa DD/MM/AAAA o escribe 'hoy'.")
        return ADD_EVENT_DATE


async def add_event_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == '-':
        context.user_data['event_km'] = None
    else:
        try:
            context.user_data['event_km'] = int(txt.replace(".", "").replace(",", ""))
        except:
            await update.message.reply_text("Número no válido. Inténtalo de nuevo o escribe '-'.")
            return ADD_EVENT_KM
    await update.message.reply_text("💶 ¿Cuánto costó? (en € o '-' para omitir)")
    return ADD_EVENT_COST


async def add_event_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == '-':
        context.user_data['event_cost'] = None
    else:
        try:
            context.user_data['event_cost'] = float(txt.replace(",", "."))
        except:
            await update.message.reply_text("Número no válido. Inténtalo de nuevo o escribe '-'.")
            return ADD_EVENT_COST
    await update.message.reply_text("📓 ¿Alguna nota adicional? (o '-' para omitir)")
    return ADD_EVENT_NOTES


async def add_event_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data['event_notes'] = None if txt == '-' else txt
    await update.message.reply_text("📅 ¿Cuándo toca el próximo? (DD/MM/AAAA o '-' para omitir)")
    return ADD_EVENT_NEXT_DATE


async def add_event_next_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == '-':
        context.user_data['event_next_date'] = None
    else:
        try:
            datetime.strptime(txt, "%d/%m/%Y")
            context.user_data['event_next_date'] = txt
        except:
            await update.message.reply_text("Formato incorrecto. Usa DD/MM/AAAA o escribe '-'.")
            return ADD_EVENT_NEXT_DATE
    await update.message.reply_text("📏 ¿A cuántos km toca el próximo? (o '-' para omitir)")
    return ADD_EVENT_NEXT_KM


async def add_event_next_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == '-':
        context.user_data['event_next_km'] = None
    else:
        try:
            context.user_data['event_next_km'] = int(txt.replace(".", "").replace(",", ""))
        except:
            await update.message.reply_text("Número no válido o escribe '-'.")
            return ADD_EVENT_NEXT_KM

    d = context.user_data
    car_id = d['car_id']
    car = db.get_car(car_id)
    db.add_event(car_id, d['event_type'], d['event_date'], d.get('event_km'),
                 d.get('event_cost'), d.get('event_notes'),
                 d.get('event_next_date'), d.get('event_next_km'))

    text = f"✅ *{d['event_type']}* registrado para *{car['brand']} {car['model']}*\n"
    text += f"  📅 {d['event_date']}"
    if d.get('event_km'):
        text += f" | 📏 {d['event_km']:,} km"
    if d.get('event_cost'):
        text += f" | 💶 {d['event_cost']}€"
    if d.get('event_next_date'):
        text += f"\n  ⏭️ Próximo: {d['event_next_date']}"
    if d.get('event_next_km'):
        text += f" / {d['event_next_km']:,} km"

    cars = db.get_cars()
    await update.message.reply_text(text, reply_markup=main_kb(cars), parse_mode="Markdown")
    context.user_data.clear()
    return MENU


# --- INSURANCE ---
async def add_ins_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ins_company'] = update.message.text.strip()
    await update.message.reply_text("¿Número de póliza?")
    return ADD_INS_POLICY

async def add_ins_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ins_policy'] = update.message.text.strip()
    await update.message.reply_text("¿Fecha de vencimiento? (DD/MM/AAAA)")
    return ADD_INS_EXPIRY

async def add_ins_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        datetime.strptime(txt, "%d/%m/%Y")
        context.user_data['ins_expiry'] = txt
        await update.message.reply_text("¿Cuánto cuesta la prima anual? (€ o '-' para omitir)")
        return ADD_INS_COST
    except:
        await update.message.reply_text("Formato incorrecto. Usa DD/MM/AAAA.")
        return ADD_INS_EXPIRY

async def add_ins_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    cost = None if txt == '-' else float(txt.replace(",", "."))
    d = context.user_data
    car = db.get_car(d['car_id'])
    db.add_insurance(d['car_id'], d['ins_company'], d['ins_policy'], d['ins_expiry'], cost)
    cars = db.get_cars()
    await update.message.reply_text(
        f"✅ Seguro registrado para *{car['brand']} {car['model']}*\n"
        f"  🛡️ {d['ins_company']} | Póliza: `{d['ins_policy']}`\n  Vence: {d['ins_expiry']}",
        reply_markup=main_kb(cars), parse_mode="Markdown")
    context.user_data.clear()
    return MENU


# --- TAX ---
async def add_tax_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['tax_amount'] = float(update.message.text.strip().replace(",", "."))
        await update.message.reply_text("¿Cuándo vence? (DD/MM/AAAA)")
        return ADD_TAX_EXPIRY
    except:
        await update.message.reply_text("Número no válido.")
        return ADD_TAX_AMOUNT

async def add_tax_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        datetime.strptime(txt, "%d/%m/%Y")
        d = context.user_data
        car = db.get_car(d['car_id'])
        db.add_tax(d['car_id'], d['tax_amount'], txt)
        cars = db.get_cars()
        await update.message.reply_text(
            f"✅ Impuesto registrado para *{car['brand']} {car['model']}*\n"
            f"  💰 {d['tax_amount']}€ | Vence: {txt}",
            reply_markup=main_kb(cars), parse_mode="Markdown")
        context.user_data.clear()
        return MENU
    except:
        await update.message.reply_text("Formato incorrecto. Usa DD/MM/AAAA.")
        return ADD_TAX_EXPIRY


# --- CLAIM ---
async def add_claim_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    date = datetime.now().strftime("%d/%m/%Y") if txt == "hoy" else txt
    try:
        datetime.strptime(date, "%d/%m/%Y")
        context.user_data['claim_date'] = date
        await update.message.reply_text("¿Descripción del siniestro?")
        return ADD_CLAIM_DESC
    except:
        await update.message.reply_text("Formato incorrecto. Usa DD/MM/AAAA o 'hoy'.")
        return ADD_CLAIM_DATE

async def add_claim_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['claim_desc'] = update.message.text.strip()
    await update.message.reply_text("¿Número de expediente? (o '-' si no lo tienes aún)")
    return ADD_CLAIM_NUMBER

async def add_claim_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data['claim_number'] = None if txt == '-' else txt
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Abierto", callback_data="status_Abierto"),
         InlineKeyboardButton("✅ Cerrado", callback_data="status_Cerrado")],
        [InlineKeyboardButton("⏳ En tramitación", callback_data="status_En tramitación")],
    ])
    await update.message.reply_text("¿Estado del parte?", reply_markup=kb)
    return ADD_CLAIM_STATUS

async def add_claim_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    status = q.data.replace("status_", "")
    d = context.user_data
    car = db.get_car(d['car_id'])
    db.add_claim(d['car_id'], d['claim_date'], d['claim_desc'], d.get('claim_number'), status)
    cars = db.get_cars()
    await q.edit_message_text(
        f"✅ Parte registrado para *{car['brand']} {car['model']}*\n"
        f"  🚨 {d['claim_date']} — {d['claim_desc'][:50]}\n  Estado: {status}",
        reply_markup=main_kb(cars), parse_mode="Markdown")
    context.user_data.clear()
    return MENU


def run_web_server():
    """Minimal HTTP server so Render doesn't kill the process."""
    port = int(os.environ.get("PORT", 8080))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, *args):
            pass
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


def main():
    import asyncio
    threading.Thread(target=run_web_server, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu_handler)],
            SELECT_CAR: [CallbackQueryHandler(select_car_handler)],
            ADD_CAR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_brand)],
            ADD_CAR_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_model)],
            ADD_CAR_PLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_plate)],
            ADD_CAR_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_year)],
            ADD_CAR_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_km)],
            ADD_CAR_FUEL: [CallbackQueryHandler(add_car_fuel)],
            UPDATE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_km_handler)],
            ADD_EVENT_TYPE: [CallbackQueryHandler(add_event_type)],
            ADD_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_date)],
            ADD_EVENT_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_km)],
            ADD_EVENT_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_cost)],
            ADD_EVENT_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_notes)],
            ADD_EVENT_NEXT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_next_date)],
            ADD_EVENT_NEXT_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_next_km)],
            ADD_INS_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ins_company)],
            ADD_INS_POLICY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ins_policy)],
            ADD_INS_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ins_expiry)],
            ADD_INS_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ins_cost)],
            ADD_TAX_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tax_amount)],
            ADD_TAX_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tax_expiry)],
            ADD_CLAIM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_claim_date)],
            ADD_CLAIM_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_claim_desc)],
            ADD_CLAIM_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_claim_number)],
            ADD_CLAIM_STATUS: [CallbackQueryHandler(add_claim_status)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    logger.info("Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
