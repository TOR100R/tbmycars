"""
Base de datos SQLite para Mi Garaje Bot
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "garaje.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS coches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                matricula TEXT UNIQUE NOT NULL,
                km_actuales INTEGER DEFAULT 0,
                anyo INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mantenimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                fecha TEXT NOT NULL,
                km_realizacion INTEGER,
                notas TEXT,
                proximo_km INTEGER,
                proxima_fecha TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS seguros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                compania TEXT,
                num_poliza TEXT,
                fecha_vencimiento TEXT,
                importe TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS itvs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                proxima_fecha TEXT,
                resultado TEXT,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS impuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                anyo INTEGER,
                importe TEXT,
                fecha_vencimiento TEXT,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS partes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                descripcion TEXT,
                num_expediente TEXT,
                estado TEXT DEFAULT 'abierto',
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS neumaticos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                tipo TEXT,
                marca TEXT,
                fecha TEXT,
                km_cambio INTEGER,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS limpiezas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                tipo TEXT,
                fecha TEXT,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );

            CREATE TABLE IF NOT EXISTS niveles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coche_id INTEGER NOT NULL,
                tipo TEXT,
                fecha TEXT,
                estado TEXT,
                FOREIGN KEY (coche_id) REFERENCES coches(id)
            );
        """)
        self.conn.commit()

    # ─── COCHES ───────────────────────────────────────────────────────────────

    def add_coche(self, marca, modelo, matricula, km, anyo):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO coches (marca, modelo, matricula, km_actuales, anyo) VALUES (?,?,?,?,?)",
            (marca, modelo, matricula, km, anyo)
        )
        self.conn.commit()
        return c.lastrowid

    def get_coches(self):
        c = self.conn.cursor()
        return c.execute("SELECT * FROM coches ORDER BY id").fetchall()

    def get_coche(self, coche_id):
        c = self.conn.cursor()
        return c.execute("SELECT * FROM coches WHERE id=?", (coche_id,)).fetchone()

    def get_coche_by_matricula(self, matricula):
        c = self.conn.cursor()
        return c.execute("SELECT * FROM coches WHERE matricula=?", (matricula.upper(),)).fetchone()

    def update_km(self, coche_id, km):
        c = self.conn.cursor()
        c.execute("UPDATE coches SET km_actuales=? WHERE id=?", (km, coche_id))
        self.conn.commit()

    # ─── MANTENIMIENTOS ───────────────────────────────────────────────────────

    def add_mantenimiento(self, coche_id, tipo, fecha, km, notas, proximo_km, proxima_fecha):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO mantenimientos (coche_id, tipo, fecha, km_realizacion, notas, proximo_km, proxima_fecha) VALUES (?,?,?,?,?,?,?)",
            (coche_id, tipo, fecha, km, notas, proximo_km, proxima_fecha)
        )
        self.conn.commit()

    def get_mantenimientos(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM mantenimientos WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    def count_mantenimientos(self, coche_id):
        c = self.conn.cursor()
        r = c.execute("SELECT COUNT(*) FROM mantenimientos WHERE coche_id=?", (coche_id,)).fetchone()
        return r[0]

    def get_ultimo_mantenimiento(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM mantenimientos WHERE coche_id=? ORDER BY id DESC LIMIT 1",
            (coche_id,)
        ).fetchone()

    # ─── SEGURO ───────────────────────────────────────────────────────────────

    def save_seguro(self, coche_id, compania, poliza, vence, importe):
        c = self.conn.cursor()
        existing = c.execute("SELECT id FROM seguros WHERE coche_id=?", (coche_id,)).fetchone()
        if existing:
            c.execute(
                "UPDATE seguros SET compania=?, num_poliza=?, fecha_vencimiento=?, importe=?, updated_at=CURRENT_TIMESTAMP WHERE coche_id=?",
                (compania, poliza, vence, importe, coche_id)
            )
        else:
            c.execute(
                "INSERT INTO seguros (coche_id, compania, num_poliza, fecha_vencimiento, importe) VALUES (?,?,?,?,?)",
                (coche_id, compania, poliza, vence, importe)
            )
        self.conn.commit()

    def get_seguro(self, coche_id):
        c = self.conn.cursor()
        return c.execute("SELECT * FROM seguros WHERE coche_id=?", (coche_id,)).fetchone()

    # ─── ITV ──────────────────────────────────────────────────────────────────

    def add_itv(self, coche_id, fecha, proxima, resultado):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO itvs (coche_id, fecha, proxima_fecha, resultado) VALUES (?,?,?,?)",
            (coche_id, fecha, proxima, resultado)
        )
        self.conn.commit()

    def get_itvs(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM itvs WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    def get_ultima_itv(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM itvs WHERE coche_id=? ORDER BY id DESC LIMIT 1",
            (coche_id,)
        ).fetchone()

    # ─── IMPUESTO ─────────────────────────────────────────────────────────────

    def add_impuesto(self, coche_id, anyo, importe, vence):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO impuestos (coche_id, anyo, importe, fecha_vencimiento) VALUES (?,?,?,?)",
            (coche_id, anyo, importe, vence)
        )
        self.conn.commit()

    def get_impuestos(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM impuestos WHERE coche_id=? ORDER BY anyo DESC",
            (coche_id,)
        ).fetchall()

    # ─── PARTES ───────────────────────────────────────────────────────────────

    def add_parte(self, coche_id, fecha, descripcion, expediente):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO partes (coche_id, fecha, descripcion, num_expediente) VALUES (?,?,?,?)",
            (coche_id, fecha, descripcion, expediente)
        )
        self.conn.commit()

    def get_partes(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM partes WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    def update_parte_estado(self, parte_id, estado):
        c = self.conn.cursor()
        c.execute("UPDATE partes SET estado=? WHERE id=?", (estado, parte_id))
        self.conn.commit()

    # ─── NEUMÁTICOS ───────────────────────────────────────────────────────────

    def add_neumatico(self, coche_id, tipo, marca, fecha, km):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO neumaticos (coche_id, tipo, marca, fecha, km_cambio) VALUES (?,?,?,?,?)",
            (coche_id, tipo, marca, fecha, km)
        )
        self.conn.commit()

    def get_neumaticos(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM neumaticos WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    # ─── LIMPIEZAS ────────────────────────────────────────────────────────────

    def add_limpieza(self, coche_id, tipo, fecha):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO limpiezas (coche_id, tipo, fecha) VALUES (?,?,?)",
            (coche_id, tipo, fecha)
        )
        self.conn.commit()

    def get_limpiezas(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM limpiezas WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    # ─── NIVELES ──────────────────────────────────────────────────────────────

    def add_nivel(self, coche_id, tipo, fecha, estado):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO niveles (coche_id, tipo, fecha, estado) VALUES (?,?,?,?)",
            (coche_id, tipo, fecha, estado)
        )
        self.conn.commit()

    def get_niveles(self, coche_id):
        c = self.conn.cursor()
        return c.execute(
            "SELECT * FROM niveles WHERE coche_id=? ORDER BY id DESC",
            (coche_id,)
        ).fetchall()

    # ─── ALERTAS ──────────────────────────────────────────────────────────────

    def get_alertas_pendientes(self):
        """Detecta mantenimientos próximos por km y por fecha"""
        alertas = []
        hoy = datetime.now()
        margen_dias = 30
        margen_km = 1000

        coches = self.get_coches()
        for coche in coches:
            nombre = f"{coche['marca']} {coche['modelo']} ({coche['matricula']})"
            km_actual = coche["km_actuales"]

            # Alertas de mantenimiento por km y fecha
            mantenimientos = self.get_mantenimientos(coche["id"])
            tipos_vistos = set()
            for m in mantenimientos:
                if m["tipo"] in tipos_vistos:
                    continue
                tipos_vistos.add(m["tipo"])

                if m["proximo_km"] and (m["proximo_km"] - km_actual) <= margen_km:
                    diff = m["proximo_km"] - km_actual
                    if diff <= 0:
                        alertas.append({"coche": nombre, "mensaje": f"⚠️ {m['tipo']} VENCIDO por km (hace {abs(diff):,} km)"})
                    else:
                        alertas.append({"coche": nombre, "mensaje": f"🔧 {m['tipo']} en {diff:,} km"})

                if m["proxima_fecha"]:
                    try:
                        fecha_prox = datetime.strptime(m["proxima_fecha"], "%d/%m/%Y")
                        diff_dias = (fecha_prox - hoy).days
                        if diff_dias <= margen_dias:
                            if diff_dias < 0:
                                alertas.append({"coche": nombre, "mensaje": f"⚠️ {m['tipo']} VENCIDO (hace {abs(diff_dias)} días)"})
                            else:
                                alertas.append({"coche": nombre, "mensaje": f"🔧 {m['tipo']} en {diff_dias} días"})
                    except ValueError:
                        pass

            # Alertas de seguro
            seguro = self.get_seguro(coche["id"])
            if seguro and seguro["fecha_vencimiento"]:
                try:
                    fecha_seg = datetime.strptime(seguro["fecha_vencimiento"], "%d/%m/%Y")
                    diff_dias = (fecha_seg - hoy).days
                    if diff_dias <= margen_dias:
                        msg = f"📋 Seguro vence en {diff_dias} días" if diff_dias >= 0 else f"📋 Seguro VENCIDO hace {abs(diff_dias)} días"
                        alertas.append({"coche": nombre, "mensaje": msg})
                except ValueError:
                    pass

            # Alertas de ITV
            itv = self.get_ultima_itv(coche["id"])
            if itv and itv["proxima_fecha"]:
                try:
                    fecha_itv = datetime.strptime(itv["proxima_fecha"], "%d/%m/%Y")
                    diff_dias = (fecha_itv - hoy).days
                    if diff_dias <= margen_dias:
                        msg = f"🔍 ITV en {diff_dias} días" if diff_dias >= 0 else f"🔍 ITV VENCIDA hace {abs(diff_dias)} días"
                        alertas.append({"coche": nombre, "mensaje": msg})
                except ValueError:
                    pass

            # Alertas de impuesto
            impuestos = self.get_impuestos(coche["id"])
            if impuestos:
                ultimo_imp = impuestos[0]
                if ultimo_imp["fecha_vencimiento"]:
                    try:
                        fecha_imp = datetime.strptime(ultimo_imp["fecha_vencimiento"], "%d/%m/%Y")
                        diff_dias = (fecha_imp - hoy).days
                        if diff_dias <= margen_dias:
                            msg = f"💶 Impuesto circulación en {diff_dias} días" if diff_dias >= 0 else f"💶 Impuesto VENCIDO hace {abs(diff_dias)} días"
                            alertas.append({"coche": nombre, "mensaje": msg})
                    except ValueError:
                        pass

        return alertas
