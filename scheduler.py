"""
Scheduler without APScheduler - uses periodic checks triggered by UptimeRobot pings.
Stores last sent timestamps in DB to avoid duplicates.
"""
import logging
from datetime import datetime
from database import Database

logger = logging.getLogger(__name__)

DAYS_ES = {
    "Lunes": "mon", "Martes": "tue", "Miércoles": "wed",
    "Jueves": "thu", "Viernes": "fri", "Sábado": "sat", "Domingo": "sun"
}
DAYS_NUM = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

db = Database()


async def check_and_send_reminders(bot):
    """Called on every web ping. Sends reminders if it's the right day/hour."""
    cfg = db.get_scheduler_config()
    if not cfg.get('chat_id'):
        return

    now = datetime.now()
    chat_id = cfg['chat_id']

    # Weekly summary
    if cfg.get('weekly_enabled', 1):
        target_day = DAYS_NUM.get(cfg.get('weekly_day', 'mon'), 0)
        target_hour = cfg.get('weekly_hour', 9)
        last_weekly = cfg.get('last_weekly_sent', '')
        today_key = now.strftime('%Y-%W')  # year + week number

        if (now.weekday() == target_day and
                now.hour == target_hour and
                last_weekly != today_key):
            await send_weekly_summary(bot, chat_id)
            db.save_scheduler_config(last_weekly_sent=today_key)

    # KM reminder
    if cfg.get('km_enabled', 1):
        target_day = DAYS_NUM.get(cfg.get('km_day', 'sun'), 6)
        target_hour = cfg.get('km_hour', 10)
        last_km = cfg.get('last_km_sent', '')
        today_key = now.strftime('%Y-%W')

        if (now.weekday() == target_day and
                now.hour == target_hour and
                last_km != today_key):
            await send_km_reminder(bot, chat_id)
            db.save_scheduler_config(last_km_sent=today_key)


async def send_weekly_summary(bot, chat_id: int):
    cars = db.get_cars()
    if not cars:
        return
    text = "📋 *Resumen semanal — Mi Garaje*\n\n"
    any_alert = False
    for car in cars:
        alerts = db.get_pending_alerts(car['id'])
        text += f"🚗 *{car['brand']} {car['model']}* ({car['plate']})\n"
        text += f"  📏 {car['km']:,} km\n"
        if alerts:
            any_alert = True
            for a in alerts:
                text += f"  {a}\n"
        else:
            text += "  ✅ Sin alertas\n"
        text += "\n"
    if not any_alert:
        text += "✅ *Todo en orden esta semana.*"
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending weekly summary: {e}")


async def send_km_reminder(bot, chat_id: int):
    cars = db.get_cars()
    if not cars:
        return
    text = "📏 *Actualización de kilómetros*\n\n"
    text += "¿Puedes actualizar los km de tus coches?\n\n"
    for car in cars:
        text += f"🚗 {car['brand']} {car['model']} — *{car['km']:,} km*\n"
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending km reminder: {e}")
