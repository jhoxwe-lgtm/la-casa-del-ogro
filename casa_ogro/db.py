from __future__ import annotations
import hashlib, hmac, os, sqlite3
from pathlib import Path

SCHEMA = r'''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','recepcion','limpieza')),
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS guests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
 phone TEXT NOT NULL, email TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rooms (
 id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT UNIQUE NOT NULL,
 room_type TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity > 0),
 state TEXT NOT NULL DEFAULT 'disponible' CHECK(state IN ('disponible','ocupada','en limpieza')),
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS reservations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guest_id INTEGER NOT NULL REFERENCES guests(id),
 room_id INTEGER NOT NULL REFERENCES rooms(id), checkin TEXT NOT NULL, checkout TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'confirmada', created_by INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS cleanings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER NOT NULL REFERENCES rooms(id),
 started_at TEXT NOT NULL, finished_at TEXT, user_id INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS spaces (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, kind TEXT NOT NULL,
 room_id INTEGER REFERENCES rooms(id), capacity INTEGER NOT NULL CHECK(capacity > 0)
);
CREATE TABLE IF NOT EXISTS sensors (
 sensor_id TEXT PRIMARY KEY, space_id INTEGER NOT NULL REFERENCES spaces(id), active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS readings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id TEXT NOT NULL REFERENCES sensors(sensor_id),
 space_id INTEGER NOT NULL REFERENCES spaces(id), people_count INTEGER NOT NULL CHECK(people_count >= 0),
 received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, space_id INTEGER NOT NULL REFERENCES spaces(id),
 reading_id INTEGER NOT NULL REFERENCES readings(id), people_count INTEGER NOT NULL,
 capacity INTEGER NOT NULL, level TEXT NOT NULL CHECK(level IN ('completo','excedido')),
 created_at TEXT NOT NULL, reviewed_by INTEGER REFERENCES users(id), reviewed_at TEXT, observation TEXT
);
CREATE INDEX IF NOT EXISTS idx_reservations_room_dates ON reservations(room_id, checkin, checkout, status);
CREATE INDEX IF NOT EXISTS idx_readings_space_time ON readings(space_id, received_at);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
CREATE TABLE IF NOT EXISTS admin_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER REFERENCES users(id), username TEXT NOT NULL,
 action TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT,
 detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit(created_at);

'''

def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 10000')
    return conn

def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 180_000)
    return salt.hex() + ':' + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(':', 1)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), 180_000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def init_db(db_path: str | Path, demo: bool = True) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        # Migraciones compatibles con bases creadas en versiones anteriores.
        room_columns = {r['name'] for r in conn.execute('PRAGMA table_info(rooms)').fetchall()}
        if 'active' not in room_columns:
            conn.execute('ALTER TABLE rooms ADD COLUMN active INTEGER NOT NULL DEFAULT 1')
        if demo:
            _seed(conn)
        conn.commit()
    finally:
        conn.close()

def _seed(conn: sqlite3.Connection) -> None:
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        conn.executemany('INSERT INTO users(username,password_hash,role,active) VALUES(?,?,?,1)', [
            ('admin', password_hash('admin123'), 'admin'),
            ('recepcion', password_hash('recep123'), 'recepcion'),
            ('limpieza', password_hash('limp123'), 'limpieza'),
        ])
    if conn.execute('SELECT COUNT(*) FROM rooms').fetchone()[0] == 0:
        conn.executemany('INSERT INTO rooms(number,room_type,capacity,state) VALUES(?,?,?,?)', [
            ('101','Doble',2,'disponible'),('102','Triple',3,'disponible'),('201','Familiar',4,'disponible')
        ])
    pool = conn.execute("SELECT id FROM spaces WHERE kind='piscina' LIMIT 1").fetchone()
    if pool is None:
        cur = conn.execute("INSERT INTO spaces(name,kind,room_id,capacity) VALUES('Piscina','piscina',NULL,20)")
        conn.execute('INSERT INTO sensors(sensor_id,space_id,active) VALUES(?,?,1)', ('sensor-piscina', cur.lastrowid))
    for room in conn.execute('SELECT id,number,capacity FROM rooms').fetchall():
        exists = conn.execute('SELECT id FROM spaces WHERE room_id=?', (room['id'],)).fetchone()
        if not exists:
            cur = conn.execute('INSERT INTO spaces(name,kind,room_id,capacity) VALUES(?,?,?,?)',
                               (f"Habitación {room['number']}", 'habitacion', room['id'], room['capacity']))
            conn.execute('INSERT INTO sensors(sensor_id,space_id,active) VALUES(?,?,1)',
                         (f"sensor-hab-{room['id']}", cur.lastrowid))
