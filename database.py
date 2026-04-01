import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get("DB_PATH", "garaje.db")


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._create_tables()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL, model TEXT NOT NULL,
                plate TEXT NOT NULL UNIQUE, year INTEGER,
                km INTEGER DEFAULT 0, fuel TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL, event_type TEXT NOT NULL,
                date TEXT NOT NULL, km INTEGER, cost REAL, notes TEXT,
                next_date TEXT, next_km INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            );
            CREATE TABLE IF NOT EXISTS insurance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL, company TEXT, policy TEXT,
                expiry TEXT, cost REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            );
            CREATE TABLE IF NOT EXISTS taxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL, amount REAL, expiry TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            );
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL, date TEXT, description TEXT,
                claim_number TEXT, status TEXT DEFAULT 'Abierto',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            );
        """)
        conn.commit()
        conn.close()

    def add_car(self, brand, model, plate, year, km, fuel):
        conn = self._conn()
        c = conn.cursor()
        c.execute("INSERT INTO cars (brand,model,plate,year,km,fuel) VALUES (?,?,?,?,?,?)",
                  (brand, model, plate, year, km, fuel))
        conn.commit()
        rid = c.lastrowid
        conn.close()
        return rid

    def get_cars(self):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM cars ORDER BY brand, model").fetchall()
        conn.close()
        return rows

    def get_car(self, car_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
        conn.close()
        return row

    def update_km(self, car_id, km):
        conn = self._conn()
        conn.execute("UPDATE cars SET km=? WHERE id=?", (km, car_id))
        conn.commit()
        conn.close()

    def add_event(self, car_id, event_type, date, km, cost, notes, next_date, next_km):
        conn = self._conn()
        conn.execute(
            "INSERT INTO events (car_id,event_type,date,km,cost,notes,next_date,next_km) VALUES (?,?,?,?,?,?,?,?)",
            (car_id, event_type, date, km, cost, notes, next_date, next_km))
        conn.commit()
        conn.close()
        if km:
            car = self.get_car(car_id)
            if car and km > car['km']:
                self.update_km(car_id, km)

    def get_events(self, car_id, limit=20):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM events WHERE car_id=? ORDER BY date DESC LIMIT ?", (car_id, limit)).fetchall()
        conn.close()
        return rows

    def get_pending_alerts(self, car_id):
        alerts = []
        car = self.get_car(car_id)
        if not car:
            return alerts
        today = datetime.now()
        current_km = car['km']
        conn = self._conn()
        events = conn.execute(
            "SELECT * FROM events WHERE car_id=? AND (next_date IS NOT NULL OR next_km IS NOT NULL)", (car_id,)
        ).fetchall()
        for e in events:
            if e['next_date']:
                try:
                    days = (datetime.strptime(e['next_date'], "%d/%m/%Y") - today).days
                    if days < 0:
                        alerts.append(f"⛔ {e['event_type']}: venció el {e['next_date']}")
                    elif days <= 7:
                        alerts.append(f"🔴 {e['event_type']}: vence en {days} días")
                    elif days <= 30:
                        alerts.append(f"🟡 {e['event_type']}: vence en {days} días")
                except: pass
            if e['next_km'] and current_km:
                left = e['next_km'] - current_km
                if left < 0:
                    alerts.append(f"⛔ {e['event_type']}: sobrepasado por {abs(left):,} km")
                elif left <= 500:
                    alerts.append(f"🔴 {e['event_type']}: faltan {left:,} km")
                elif left <= 1000:
                    alerts.append(f"🟡 {e['event_type']}: faltan {left:,} km")
        ins = conn.execute("SELECT * FROM insurance WHERE car_id=? ORDER BY created_at DESC LIMIT 1", (car_id,)).fetchone()
        if ins and ins['expiry']:
            try:
                days = (datetime.strptime(ins['expiry'], "%d/%m/%Y") - today).days
                if days < 0:
                    alerts.append(f"⛔ Seguro {ins['company']}: venció el {ins['expiry']}")
                elif days <= 30:
                    alerts.append(f"{'🔴' if days<=7 else '🟡'} Seguro {ins['company']}: vence en {days} días")
            except: pass
        tax = conn.execute("SELECT * FROM taxes WHERE car_id=? ORDER BY created_at DESC LIMIT 1", (car_id,)).fetchone()
        conn.close()
        if tax and tax['expiry']:
            try:
                days = (datetime.strptime(tax['expiry'], "%d/%m/%Y") - today).days
                if days < 0:
                    alerts.append(f"⛔ Impuesto circulación: venció el {tax['expiry']}")
                elif days <= 30:
                    alerts.append(f"{'🔴' if days<=7 else '🟡'} Impuesto circulación: vence en {days} días")
            except: pass
        return alerts

    def add_insurance(self, car_id, company, policy, expiry, cost):
        conn = self._conn()
        conn.execute("INSERT INTO insurance (car_id,company,policy,expiry,cost) VALUES (?,?,?,?,?)",
                     (car_id, company, policy, expiry, cost))
        conn.commit()
        conn.close()

    def get_insurance(self, car_id):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM insurance WHERE car_id=? ORDER BY created_at DESC", (car_id,)).fetchall()
        conn.close()
        return rows

    def add_tax(self, car_id, amount, expiry):
        conn = self._conn()
        conn.execute("INSERT INTO taxes (car_id,amount,expiry) VALUES (?,?,?)", (car_id, amount, expiry))
        conn.commit()
        conn.close()

    def add_claim(self, car_id, date, description, claim_number, status):
        conn = self._conn()
        conn.execute("INSERT INTO claims (car_id,date,description,claim_number,status) VALUES (?,?,?,?,?)",
                     (car_id, date, description, claim_number, status))
        conn.commit()
        conn.close()

    def get_claims(self, car_id):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM claims WHERE car_id=? ORDER BY date DESC", (car_id,)).fetchall()
        conn.close()
        return rows
