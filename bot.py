#!/usr/bin/env python3
"""
🚗 Mi Garaje Bot — Gestor completo de vehículos para Telegram
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from scheduler import setup_scheduler
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Estados de conversación
(MENU, ADD_CAR_MARCA, ADD_CAR_MODELO, ADD_CAR_MATRICULA, ADD_CAR_KM,
 ADD_CAR_ANYO, SELECT_CAR, SELECT_ACTION, ADD_MANT_TIPO, ADD_MANT_FECHA,
 ADD_MANT_KM, ADD_MANT_NOTAS, ADD_MANT_PROXKM, ADD_MANT_PROXFECHA,
 UPDATE_KM, ADD_SEGURO_CIA, ADD_SEGURO_POLIZA, ADD_SEGURO_VENCE,
 ADD_SEGURO_IMPORTE, ADD_ITV_FECHA, ADD_ITV_PROXIMA, ADD_ITV_RESULTADO,
 ADD_IMPUESTO_IMPORTE, ADD_IMPUESTO_VENCE, ADD_PARTE_FECHA,
 ADD_PARTE_DESC, ADD_PARTE_EXPEDIENTE, ADD_NEUMATICO_TIPO,
 ADD_NEUMATICO_MARCA, ADD_NEUMATICO_FECHA, ADD_NEUMATICO_KM,
 ADD_LIMPIEZA_TIPO, ADD_LIMPIEZA_FECHA, ADD_NIVEL_TIPO,
 ADD_NIVEL_FECHA, ADD_NIVEL_ESTADO) = range(36)

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

def check_owner(update: Update) -> bool:
    if OWNER_ID == 0:
        return True
    return update.effective_user.id == OWNER_ID

# ─── MENÚ PRINCIPAL ───────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_owner(update):
        await update.message.reply_text("⛔ No autorizado.")
        return ConversationHandler.END

    coches = db.get_coches()
    texto = "🚗 *Mi Garaje* — Gestor de vehículos\n\n"

    if coches:
        texto += "Tus vehículos:\n"
        for c in coches:
            texto += f"  • {c['marca']} {c['modelo']} ({c['matricula']}) — {c['km_actuales']:,} km\n"
        texto += "\n"

    keyboard = [
        [InlineKeyboardButton("🚗 Mis vehículos", callback_data="mis_coches")],
        [InlineKeyboardButton("➕ Añadir vehículo", callback_data="add_coche")],
        [InlineKeyboardButton("⚠️ Alertas pendientes", callback_data="alertas")],
        [InlineKeyboardButton("📊 Resumen general", callback_data="resumen")],
    ]
    await update.message.reply_text(
        texto, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MENU

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        return await show_main_menu(query, context)
    elif data == "add_coche":
        return await start_add_coche(query, context)
    elif data == "mis_coches":
        return await show_coches(query, context)
    elif data == "alertas":
        return await show_alertas(query, context)
    elif data == "resumen":
        return await show_resumen(query, context)
    elif data.startswith("coche_"):
        coche_id = int(data.split("_")[1])
        context.user_data["coche_id"] = coche_id
        return await show_menu_coche(query, context, coche_id)
    elif data.startswith("accion_"):
        return await handle_accion(query, context, data)
    elif data.startswith("ver_"):
        return await handle_ver(query, context, data)
    elif data.startswith("parte_estado_"):
        return await cambiar_estado_parte(query, context, data)

    return MENU

async def show_main_menu(query, context):
    coches = db.get_coches()
    texto = "🚗 *Mi Garaje* — Menú principal\n"
    keyboard = [
        [InlineKeyboardButton("🚗 Mis vehículos", callback_data="mis_coches")],
        [InlineKeyboardButton("➕ Añadir vehículo", callback_data="add_coche")],
        [InlineKeyboardButton("⚠️ Alertas pendientes", callback_data="alertas")],
        [InlineKeyboardButton("📊 Resumen general", callback_data="resumen")],
    ]
    await query.edit_message_text(texto, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── AÑADIR COCHE ─────────────────────────────────────────────────────────────

async def start_add_coche(query, context):
    coches = db.get_coches()
    if len(coches) >= 5:
        await query.edit_message_text("⚠️ Máximo 5 vehículos alcanzado.")
        return MENU
    await query.edit_message_text("🚗 *Añadir vehículo*\n\n¿Cuál es la *marca*? (ej: Toyota, Opel, Honda...)",
                                   parse_mode="Markdown")
    return ADD_CAR_MARCA

async def add_car_marca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_car"] = {"marca": update.message.text.strip()}
    await update.message.reply_text("¿Y el *modelo*? (ej: Corolla, Astra, SH125...)", parse_mode="Markdown")
    return ADD_CAR_MODELO

async def add_car_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_car"]["modelo"] = update.message.text.strip()
    await update.message.reply_text("¿*Matrícula*?", parse_mode="Markdown")
    return ADD_CAR_MATRICULA

async def add_car_matricula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_car"]["matricula"] = update.message.text.strip().upper()
    await update.message.reply_text("¿*Kilómetros actuales*? (solo el número)", parse_mode="Markdown")
    return ADD_CAR_KM

async def add_car_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        context.user_data["new_car"]["km"] = km
        await update.message.reply_text("¿*Año de matriculación*?", parse_mode="Markdown")
        return ADD_CAR_ANYO
    except ValueError:
        await update.message.reply_text("Por favor escribe solo el número de kilómetros.")
        return ADD_CAR_KM

async def add_car_anyo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anyo = int(update.message.text.strip())
        car = context.user_data["new_car"]
        car["anyo"] = anyo
        coche_id = db.add_coche(car["marca"], car["modelo"], car["matricula"], car["km"], anyo)
        keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data="start")]]
        await update.message.reply_text(
            f"✅ *{car['marca']} {car['modelo']}* añadido correctamente.\n\n"
            f"Matrícula: {car['matricula']}\nKm: {car['km']:,}\nAño: {anyo}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MENU
    except ValueError:
        await update.message.reply_text("Por favor escribe solo el año (ej: 2019).")
        return ADD_CAR_ANYO

# ─── LISTA DE COCHES ──────────────────────────────────────────────────────────

async def show_coches(query, context):
    coches = db.get_coches()
    if not coches:
        keyboard = [
            [InlineKeyboardButton("➕ Añadir vehículo", callback_data="add_coche")],
            [InlineKeyboardButton("🏠 Menú principal", callback_data="start")],
        ]
        await query.edit_message_text("No tienes vehículos aún. ¡Añade uno!",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    keyboard = []
    for c in coches:
        label = f"🚗 {c['marca']} {c['modelo']} — {c['matricula']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"coche_{c['id']}")])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data="start")])
    await query.edit_message_text("Selecciona un vehículo:",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_CAR

async def show_menu_coche(query, context, coche_id):
    coche = db.get_coche(coche_id)
    if not coche:
        await query.edit_message_text("Vehículo no encontrado.")
        return MENU

    texto = (f"🚗 *{coche['marca']} {coche['modelo']}*\n"
             f"Matrícula: {coche['matricula']} | Año: {coche['anyo']}\n"
             f"Kilómetros: *{coche['km_actuales']:,} km*\n")

    keyboard = [
        [InlineKeyboardButton("📏 Actualizar km", callback_data=f"accion_km_{coche_id}")],
        [InlineKeyboardButton("🔧 Mantenimiento", callback_data=f"ver_mantenimiento_{coche_id}"),
         InlineKeyboardButton("🛞 Neumáticos", callback_data=f"ver_neumaticos_{coche_id}")],
        [InlineKeyboardButton("📋 Seguro", callback_data=f"ver_seguro_{coche_id}"),
         InlineKeyboardButton("🔍 ITV", callback_data=f"ver_itv_{coche_id}")],
        [InlineKeyboardButton("💶 Impuesto", callback_data=f"ver_impuesto_{coche_id}"),
         InlineKeyboardButton("🚨 Partes", callback_data=f"ver_partes_{coche_id}")],
        [InlineKeyboardButton("🧹 Limpiezas", callback_data=f"ver_limpiezas_{coche_id}"),
         InlineKeyboardButton("🔬 Niveles", callback_data=f"ver_niveles_{coche_id}")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="start")],
    ]
    await query.edit_message_text(texto, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION

# ─── ACTUALIZAR KM ────────────────────────────────────────────────────────────

async def handle_accion(query, context, data):
    partes = data.split("_")
    accion = partes[1]
    coche_id = int(partes[2])
    context.user_data["coche_id"] = coche_id

    if accion == "km":
        coche = db.get_coche(coche_id)
        await query.edit_message_text(
            f"📏 *Actualizar kilómetros*\n\n"
            f"{coche['marca']} {coche['modelo']} — actualmente *{coche['km_actuales']:,} km*\n\n"
            f"¿Cuántos km tiene ahora?",
            parse_mode="Markdown"
        )
        return UPDATE_KM

    elif accion == "addmant":
        await query.edit_message_text(
            "🔧 *Nuevo mantenimiento*\n\n¿Qué tipo de mantenimiento? "
            "(ej: Cambio de aceite, Filtro de aire, Frenos, Correa distribución...)",
            parse_mode="Markdown"
        )
        return ADD_MANT_TIPO

    elif accion == "addseguro":
        await query.edit_message_text("📋 *Seguro* — ¿Compañía aseguradora?", parse_mode="Markdown")
        return ADD_SEGURO_CIA

    elif accion == "additv":
        await query.edit_message_text("🔍 *ITV* — ¿Fecha de la ITV? (DD/MM/AAAA)", parse_mode="Markdown")
        return ADD_ITV_FECHA

    elif accion == "addimpuesto":
        await query.edit_message_text("💶 *Impuesto de circulación* — ¿Importe pagado (€)?", parse_mode="Markdown")
        return ADD_IMPUESTO_IMPORTE

    elif accion == "addparte":
        await query.edit_message_text("🚨 *Parte al seguro* — ¿Fecha del parte? (DD/MM/AAAA)", parse_mode="Markdown")
        return ADD_PARTE_FECHA

    elif accion == "addneu":
        await query.edit_message_text(
            "🛞 *Neumáticos* — ¿Tipo de cambio?\n(ej: Verano, Invierno, All-season, Rueda de repuesto...)",
            parse_mode="Markdown"
        )
        return ADD_NEUMATICO_TIPO

    elif accion == "addlimpieza":
        await query.edit_message_text(
            "🧹 *Limpieza* — ¿Tipo?\n(ej: Lavado exterior, Limpieza interior, Pulido, Encerado...)",
            parse_mode="Markdown"
        )
        return ADD_LIMPIEZA_TIPO

    elif accion == "addnivel":
        await query.edit_message_text(
            "🔬 *Chequeo de niveles* — ¿Qué nivel?\n(ej: Aceite motor, Refrigerante, Frenos, Dirección, Limpiaparabrisas, Batería...)",
            parse_mode="Markdown"
        )
        return ADD_NIVEL_TIPO

    return SELECT_ACTION

async def update_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        coche_id = context.user_data["coche_id"]
        coche = db.get_coche(coche_id)
        if km < coche["km_actuales"]:
            await update.message.reply_text(
                f"⚠️ El valor introducido ({km:,} km) es menor que el actual ({coche['km_actuales']:,} km). ¿Es correcto? Escríbelo de nuevo o confirma con /forzar_{km}"
            )
            return UPDATE_KM
        db.update_km(coche_id, km)
        keyboard = [[InlineKeyboardButton("🔙 Volver al coche", callback_data=f"coche_{coche_id}")]]
        await update.message.reply_text(
            f"✅ Km actualizados: *{km:,} km*", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MENU
    except ValueError:
        await update.message.reply_text("Escribe solo el número de kilómetros.")
        return UPDATE_KM

# ─── VER SECCIONES ────────────────────────────────────────────────────────────

async def handle_ver(query, context, data):
    partes = data.split("_", 2)
    seccion = partes[1]
    coche_id = int(partes[2])
    context.user_data["coche_id"] = coche_id
    coche = db.get_coche(coche_id)
    nombre = f"{coche['marca']} {coche['modelo']}"

    if seccion == "mantenimiento":
        registros = db.get_mantenimientos(coche_id)
        texto = f"🔧 *Mantenimiento — {nombre}*\n\n"
        if registros:
            for r in registros[-10:]:
                texto += f"• *{r['tipo']}* — {r['fecha']} ({r['km_realizacion']:,} km)\n"
                if r['notas']:
                    texto += f"  _{r['notas']}_\n"
                if r['proximo_km']:
                    texto += f"  Próximo: {r['proximo_km']:,} km"
                if r['proxima_fecha']:
                    texto += f" / {r['proxima_fecha']}"
                texto += "\n"
        else:
            texto += "_Sin registros aún_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir mantenimiento", callback_data=f"accion_addmant_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "seguro":
        seguro = db.get_seguro(coche_id)
        texto = f"📋 *Seguro — {nombre}*\n\n"
        if seguro:
            texto += (f"Compañía: *{seguro['compania']}*\n"
                      f"Póliza: {seguro['num_poliza']}\n"
                      f"Vencimiento: {seguro['fecha_vencimiento']}\n"
                      f"Importe: {seguro['importe']}€\n")
        else:
            texto += "_Sin datos de seguro_\n"
        keyboard = [
            [InlineKeyboardButton("✏️ Actualizar seguro", callback_data=f"accion_addseguro_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "itv":
        itvs = db.get_itvs(coche_id)
        texto = f"🔍 *ITV — {nombre}*\n\n"
        if itvs:
            for itv in itvs:
                texto += f"• {itv['fecha']} — {itv['resultado']}\n  Próxima: {itv['proxima_fecha']}\n"
        else:
            texto += "_Sin registros de ITV_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir ITV", callback_data=f"accion_additv_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "impuesto":
        impuestos = db.get_impuestos(coche_id)
        texto = f"💶 *Impuesto circulación — {nombre}*\n\n"
        if impuestos:
            for imp in impuestos:
                texto += f"• {imp['anyo']} — {imp['importe']}€ (vence: {imp['fecha_vencimiento']})\n"
        else:
            texto += "_Sin registros_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir impuesto", callback_data=f"accion_addimpuesto_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "partes":
        partes_list = db.get_partes(coche_id)
        texto = f"🚨 *Partes al seguro — {nombre}*\n\n"
        if partes_list:
            for p in partes_list:
                estado_icon = "🟢" if p['estado'] == "cerrado" else "🟡"
                texto += f"{estado_icon} *{p['fecha']}* — {p['descripcion']}\n"
                if p['num_expediente']:
                    texto += f"  Expediente: {p['num_expediente']}\n"
        else:
            texto += "_Sin partes registrados_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir parte", callback_data=f"accion_addparte_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "neumaticos":
        neus = db.get_neumaticos(coche_id)
        texto = f"🛞 *Neumáticos — {nombre}*\n\n"
        if neus:
            for n in neus:
                texto += f"• *{n['tipo']}* ({n['marca']}) — {n['fecha']}\n  Km al cambio: {n['km_cambio']:,}\n"
        else:
            texto += "_Sin registros_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir cambio", callback_data=f"accion_addneu_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "limpiezas":
        limpiezas = db.get_limpiezas(coche_id)
        texto = f"🧹 *Limpiezas — {nombre}*\n\n"
        if limpiezas:
            for l in limpiezas:
                texto += f"• *{l['tipo']}* — {l['fecha']}\n"
        else:
            texto += "_Sin registros_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir limpieza", callback_data=f"accion_addlimpieza_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    elif seccion == "niveles":
        niveles = db.get_niveles(coche_id)
        texto = f"🔬 *Chequeos de niveles — {nombre}*\n\n"
        if niveles:
            for n in niveles:
                texto += f"• *{n['tipo']}* — {n['fecha']} → {n['estado']}\n"
        else:
            texto += "_Sin registros_\n"
        keyboard = [
            [InlineKeyboardButton("➕ Añadir chequeo", callback_data=f"accion_addnivel_{coche_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"coche_{coche_id}")],
        ]

    else:
        texto = "Sección no encontrada."
        keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data="start")]]

    await query.edit_message_text(texto, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ACTION

# ─── MANTENIMIENTO ────────────────────────────────────────────────────────────

async def add_mant_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_mant"] = {"tipo": update.message.text.strip()}
    await update.message.reply_text("📅 ¿Fecha en que se realizó? (DD/MM/AAAA)", parse_mode="Markdown")
    return ADD_MANT_FECHA

async def add_mant_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_mant"]["fecha"] = update.message.text.strip()
    await update.message.reply_text("📏 ¿Km en el momento del mantenimiento?")
    return ADD_MANT_KM

async def add_mant_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        context.user_data["new_mant"]["km"] = km
        await update.message.reply_text("📝 ¿Alguna nota o detalle? (o escribe '-' para omitir)")
        return ADD_MANT_NOTAS
    except ValueError:
        await update.message.reply_text("Escribe solo el número.")
        return ADD_MANT_KM

async def add_mant_notas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notas = update.message.text.strip()
    context.user_data["new_mant"]["notas"] = "" if notas == "-" else notas
    await update.message.reply_text("📏 ¿Próximo mantenimiento en cuántos km? (o '-' para omitir)")
    return ADD_MANT_PROXKM

async def add_mant_proxkm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == "-":
        context.user_data["new_mant"]["proximo_km"] = None
    else:
        try:
            context.user_data["new_mant"]["proximo_km"] = int(val.replace(".", "").replace(",", ""))
        except ValueError:
            context.user_data["new_mant"]["proximo_km"] = None
    await update.message.reply_text("📅 ¿Próxima fecha de mantenimiento? (DD/MM/AAAA o '-' para omitir)")
    return ADD_MANT_PROXFECHA

async def add_mant_proxfecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    m = context.user_data["new_mant"]
    m["proxima_fecha"] = None if val == "-" else val
    coche_id = context.user_data["coche_id"]
    db.add_mantenimiento(coche_id, m["tipo"], m["fecha"], m["km"], m.get("notas", ""),
                         m.get("proximo_km"), m.get("proxima_fecha"))
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text(
        f"✅ *{m['tipo']}* registrado correctamente.", parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MENU

# ─── SEGURO ───────────────────────────────────────────────────────────────────

async def add_seguro_cia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_seguro"] = {"compania": update.message.text.strip()}
    await update.message.reply_text("📋 ¿Número de póliza?")
    return ADD_SEGURO_POLIZA

async def add_seguro_poliza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_seguro"]["poliza"] = update.message.text.strip()
    await update.message.reply_text("📅 ¿Fecha de vencimiento? (DD/MM/AAAA)")
    return ADD_SEGURO_VENCE

async def add_seguro_vence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_seguro"]["vence"] = update.message.text.strip()
    await update.message.reply_text("💶 ¿Importe de la prima (€)?")
    return ADD_SEGURO_IMPORTE

async def add_seguro_importe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = context.user_data["new_seguro"]
    s["importe"] = update.message.text.strip()
    coche_id = context.user_data["coche_id"]
    db.save_seguro(coche_id, s["compania"], s["poliza"], s["vence"], s["importe"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ Seguro guardado.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── ITV ──────────────────────────────────────────────────────────────────────

async def add_itv_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_itv"] = {"fecha": update.message.text.strip()}
    await update.message.reply_text("📅 ¿Fecha de la próxima ITV? (DD/MM/AAAA)")
    return ADD_ITV_PROXIMA

async def add_itv_proxima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_itv"]["proxima"] = update.message.text.strip()
    await update.message.reply_text("✅ ¿Resultado? (Favorable / Desfavorable / Con defectos leves)")
    return ADD_ITV_RESULTADO

async def add_itv_resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    itv = context.user_data["new_itv"]
    itv["resultado"] = update.message.text.strip()
    coche_id = context.user_data["coche_id"]
    db.add_itv(coche_id, itv["fecha"], itv["proxima"], itv["resultado"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ ITV registrada.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── IMPUESTO ─────────────────────────────────────────────────────────────────

async def add_impuesto_importe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_imp"] = {"importe": update.message.text.strip()}
    await update.message.reply_text("📅 ¿Fecha de vencimiento? (DD/MM/AAAA)")
    return ADD_IMPUESTO_VENCE

async def add_impuesto_vence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    imp = context.user_data["new_imp"]
    imp["vence"] = update.message.text.strip()
    coche_id = context.user_data["coche_id"]
    anyo = datetime.now().year
    db.add_impuesto(coche_id, anyo, imp["importe"], imp["vence"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ Impuesto registrado.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── PARTE AL SEGURO ──────────────────────────────────────────────────────────

async def add_parte_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_parte"] = {"fecha": update.message.text.strip()}
    await update.message.reply_text("📝 ¿Descripción del parte?")
    return ADD_PARTE_DESC

async def add_parte_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_parte"]["desc"] = update.message.text.strip()
    await update.message.reply_text("🔢 ¿Número de expediente? (o '-' si aún no tienes)")
    return ADD_PARTE_EXPEDIENTE

async def add_parte_expediente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = context.user_data["new_parte"]
    val = update.message.text.strip()
    p["expediente"] = "" if val == "-" else val
    coche_id = context.user_data["coche_id"]
    db.add_parte(coche_id, p["fecha"], p["desc"], p["expediente"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ Parte registrado.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

async def cambiar_estado_parte(query, context, data):
    partes = data.split("_")
    parte_id = int(partes[3])
    estado = partes[4]
    db.update_parte_estado(parte_id, estado)
    await query.answer(f"Estado actualizado a: {estado}")
    return SELECT_ACTION

# ─── NEUMÁTICOS ───────────────────────────────────────────────────────────────

async def add_neu_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_neu"] = {"tipo": update.message.text.strip()}
    await update.message.reply_text("🏷️ ¿Marca de los neumáticos? (ej: Michelin, Bridgestone, Continental...)")
    return ADD_NEUMATICO_MARCA

async def add_neu_marca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_neu"]["marca"] = update.message.text.strip()
    await update.message.reply_text("📅 ¿Fecha del cambio? (DD/MM/AAAA)")
    return ADD_NEUMATICO_FECHA

async def add_neu_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_neu"]["fecha"] = update.message.text.strip()
    await update.message.reply_text("📏 ¿Km al hacer el cambio?")
    return ADD_NEUMATICO_KM

async def add_neu_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text.strip().replace(".", "").replace(",", ""))
        n = context.user_data["new_neu"]
        n["km"] = km
        coche_id = context.user_data["coche_id"]
        db.add_neumatico(coche_id, n["tipo"], n["marca"], n["fecha"], km)
        keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
        await update.message.reply_text("✅ Cambio de neumáticos registrado.", reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU
    except ValueError:
        await update.message.reply_text("Escribe solo el número.")
        return ADD_NEUMATICO_KM

# ─── LIMPIEZA ─────────────────────────────────────────────────────────────────

async def add_limpieza_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_limpieza"] = {"tipo": update.message.text.strip()}
    await update.message.reply_text("📅 ¿Fecha? (DD/MM/AAAA)")
    return ADD_LIMPIEZA_FECHA

async def add_limpieza_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    l = context.user_data["new_limpieza"]
    l["fecha"] = update.message.text.strip()
    coche_id = context.user_data["coche_id"]
    db.add_limpieza(coche_id, l["tipo"], l["fecha"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ Limpieza registrada.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── NIVELES ──────────────────────────────────────────────────────────────────

async def add_nivel_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_nivel"] = {"tipo": update.message.text.strip()}
    await update.message.reply_text("📅 ¿Fecha del chequeo? (DD/MM/AAAA)")
    return ADD_NIVEL_FECHA

async def add_nivel_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_nivel"]["fecha"] = update.message.text.strip()
    await update.message.reply_text("🔬 ¿Estado? (ej: OK, Bajo, Rellenado, Necesita cambio...)")
    return ADD_NIVEL_ESTADO

async def add_nivel_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = context.user_data["new_nivel"]
    n["estado"] = update.message.text.strip()
    coche_id = context.user_data["coche_id"]
    db.add_nivel(coche_id, n["tipo"], n["fecha"], n["estado"])
    keyboard = [[InlineKeyboardButton("🔙 Volver al vehículo", callback_data=f"coche_{coche_id}")]]
    await update.message.reply_text("✅ Chequeo de nivel registrado.", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── ALERTAS Y RESUMEN ────────────────────────────────────────────────────────

async def show_alertas(query, context):
    alertas = db.get_alertas_pendientes()
    if not alertas:
        texto = "✅ *No hay alertas pendientes*\n\nTodo está al día."
    else:
        texto = f"⚠️ *Alertas pendientes* ({len(alertas)})\n\n"
        for a in alertas:
            texto += f"🔴 *{a['coche']}* — {a['mensaje']}\n"
    keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data="start")]]
    await query.edit_message_text(texto, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

async def show_resumen(query, context):
    coches = db.get_coches()
    if not coches:
        await query.edit_message_text("No tienes vehículos registrados.",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú", callback_data="start")]]))
        return MENU

    texto = "📊 *Resumen general*\n\n"
    for c in coches:
        total_mant = db.count_mantenimientos(c["id"])
        ultimo_mant = db.get_ultimo_mantenimiento(c["id"])
        texto += (f"🚗 *{c['marca']} {c['modelo']}* ({c['matricula']})\n"
                  f"  Km: {c['km_actuales']:,} | Año: {c['anyo']}\n"
                  f"  Mantenimientos: {total_mant}\n")
        if ultimo_mant:
            texto += f"  Último: {ultimo_mant['tipo']} ({ultimo_mant['fecha']})\n"
        texto += "\n"

    keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data="start")]]
    await query.edit_message_text(texto, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# ─── COMANDO /km ──────────────────────────────────────────────────────────────

async def cmd_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando rápido: /km MATRICULA KILOMETROS"""
    if not check_owner(update):
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Uso: /km MATRICULA KILOMETROS\nEjemplo: /km 1234ABC 85000")
        return
    matricula = args[0].upper()
    try:
        km = int(args[1].replace(".", "").replace(",", ""))
        coche = db.get_coche_by_matricula(matricula)
        if not coche:
            await update.message.reply_text(f"No encontré ningún vehículo con matrícula {matricula}")
            return
        db.update_km(coche["id"], km)
        await update.message.reply_text(f"✅ {coche['marca']} {coche['modelo']} — {km:,} km actualizados.")
    except ValueError:
        await update.message.reply_text("El kilómetro debe ser un número.")

async def cmd_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /alertas — muestra alertas pendientes"""
    if not check_owner(update):
        return
    alertas = db.get_alertas_pendientes()
    if not alertas:
        await update.message.reply_text("✅ No hay alertas pendientes.")
    else:
        texto = f"⚠️ *Alertas pendientes* ({len(alertas)})\n\n"
        for a in alertas:
            texto += f"🔴 *{a['coche']}* — {a['mensaje']}\n"
        await update.message.reply_text(texto, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🏠 Menú principal", callback_data="start")]]
    await update.message.reply_text("Operación cancelada.",
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN no configurado en variables de entorno")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu_callback)],
            SELECT_CAR: [CallbackQueryHandler(menu_callback)],
            SELECT_ACTION: [CallbackQueryHandler(menu_callback)],
            ADD_CAR_MARCA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_marca)],
            ADD_CAR_MODELO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_modelo)],
            ADD_CAR_MATRICULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_matricula)],
            ADD_CAR_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_km)],
            ADD_CAR_ANYO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_anyo)],
            UPDATE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_km)],
            ADD_MANT_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_tipo)],
            ADD_MANT_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_fecha)],
            ADD_MANT_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_km)],
            ADD_MANT_NOTAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_notas)],
            ADD_MANT_PROXKM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_proxkm)],
            ADD_MANT_PROXFECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mant_proxfecha)],
            ADD_SEGURO_CIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_seguro_cia)],
            ADD_SEGURO_POLIZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_seguro_poliza)],
            ADD_SEGURO_VENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_seguro_vence)],
            ADD_SEGURO_IMPORTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_seguro_importe)],
            ADD_ITV_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_itv_fecha)],
            ADD_ITV_PROXIMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_itv_proxima)],
            ADD_ITV_RESULTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_itv_resultado)],
            ADD_IMPUESTO_IMPORTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_impuesto_importe)],
            ADD_IMPUESTO_VENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_impuesto_vence)],
            ADD_PARTE_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_parte_fecha)],
            ADD_PARTE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_parte_desc)],
            ADD_PARTE_EXPEDIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_parte_expediente)],
            ADD_NEUMATICO_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_neu_tipo)],
            ADD_NEUMATICO_MARCA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_neu_marca)],
            ADD_NEUMATICO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_neu_fecha)],
            ADD_NEUMATICO_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_neu_km)],
            ADD_LIMPIEZA_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_limpieza_tipo)],
            ADD_LIMPIEZA_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_limpieza_fecha)],
            ADD_NIVEL_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nivel_tipo)],
            ADD_NIVEL_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nivel_fecha)],
            ADD_NIVEL_ESTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nivel_estado)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("km", cmd_km))
    app.add_handler(CommandHandler("alertas", cmd_alertas))

    # Scheduler para alertas automáticas
    setup_scheduler(app, db)

    logger.info("🚗 Mi Garaje Bot arrancado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
