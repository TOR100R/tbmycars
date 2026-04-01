# 🚗 Mi Garaje Bot — Telegram

Gestor completo de vehículos para Telegram. Controla hasta 5 coches con:

- 🔧 Mantenimiento mecánico (aceite, filtros, frenos, correa...)
- 🛞 Cambios de neumáticos
- 📋 Seguro (compañía, póliza, vencimiento)
- 🔍 ITV (historial y próxima fecha)
- 💶 Impuesto de circulación
- 🚨 Partes al seguro con seguimiento de expediente
- 🧹 Limpiezas
- 🔬 Chequeos de niveles (aceite, refrigerante, frenos...)
- ⚠️ Alertas automáticas por km y por fecha
- 📏 Recordatorio semanal de kilómetros

---

## 🚀 Despliegue en Render (gratis)

### Paso 1 — Crear el bot en Telegram
1. Abre Telegram y busca **@BotFather**
2. Escribe `/newbot`
3. Elige nombre (ej: *Mi Garaje*) y username (ej: *migarajebot*)
4. Guarda el **token** que te da

### Paso 2 — Obtener tu Telegram User ID
1. Busca **@userinfobot** en Telegram
2. Escríbele cualquier cosa
3. Te dirá tu **ID** (un número como 123456789)

### Paso 3 — Subir el código a GitHub
1. Crea una cuenta en [github.com](https://github.com) si no tienes
2. Crea un repositorio nuevo (privado)
3. Sube todos estos archivos

### Paso 4 — Desplegar en Render
1. Ve a [render.com](https://render.com) y crea una cuenta gratuita
2. New → **Background Worker**
3. Conecta tu repositorio de GitHub
4. En **Environment Variables** añade:
   - `BOT_TOKEN` → el token de BotFather
   - `OWNER_ID` → tu Telegram User ID
5. El `render.yaml` configura todo automáticamente
6. Haz clic en **Deploy**

### Paso 5 — Evitar que duerma (UptimeRobot)
Render en plan gratuito puede pausar el servicio.
1. Ve a [uptimerobot.com](https://uptimerobot.com) — cuenta gratuita
2. Añade un monitor HTTP apuntando a la URL de tu servicio en Render
3. Intervalo: cada 5 minutos

---

## 💬 Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `/start` | Menú principal |
| `/km MATRICULA KM` | Actualización rápida de km |
| `/alertas` | Ver alertas pendientes |
| `/cancel` | Cancelar operación actual |

---

## 📁 Estructura del proyecto

```
garaje_bot/
├── bot.py           # Bot principal y handlers
├── database.py      # Base de datos SQLite
├── scheduler.py     # Alertas automáticas diarias
├── requirements.txt # Dependencias Python
├── render.yaml      # Configuración de Render
└── README.md        # Este archivo
```

---

## ⚙️ Variables de entorno

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `BOT_TOKEN` | Token de BotFather | ✅ Sí |
| `OWNER_ID` | Tu Telegram User ID | Recomendada |
| `DB_PATH` | Ruta de la base de datos | No (por defecto: garaje.db) |
