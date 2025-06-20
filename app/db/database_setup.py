# app/db/database_setup.py
import sqlite3
import os

DB_NAME = "trading-bot95g.db"
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), DB_NAME)

def create_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print(f"Conexión exitosa a SQLite DB en '{DB_FILE}'")
    except sqlite3.Error as e:
        print(f"Error al conectar con SQLite: {e}")
    return conn

def create_tables(conn):
    """Crea las tablas en la base de datos con el esquema final, incluyendo account_type."""
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                profile_photo_url TEXT,
                role TEXT NOT NULL DEFAULT 'admin'
            );
        """)
        print("Tabla 'users' verificada/creada.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                po_token TEXT,
                telegram_user_id INTEGER,
                is_active INTEGER NOT NULL DEFAULT 0,
                account_type TEXT NOT NULL DEFAULT 'DEMO',
                base_amount REAL NOT NULL DEFAULT 10.0,
                active_asset_id INTEGER,
                timeframe TEXT NOT NULL DEFAULT 'M1',
                payout_min INTEGER NOT NULL DEFAULT 80,
                risk_strategy TEXT NOT NULL DEFAULT 'MARTINGALE',
                stop_loss REAL NOT NULL DEFAULT 50.0,
                take_profit REAL NOT NULL DEFAULT 100.0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (active_asset_id) REFERENCES assets (id)
            );
        """)
        print("Tabla 'settings' verificada/creada con campo 'account_type'.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (user_id, name)
            );
        """)
        print("Tabla 'assets' verificada/creada.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asset_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL,
                trade_level TEXT NOT NULL,
                amount REAL NOT NULL,
                payout_used INTEGER NOT NULL,
                result TEXT NOT NULL,
                profit_loss REAL NOT NULL,
                sequence_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (asset_id) REFERENCES assets (id)
            );
        """)
        print("Tabla 'trades' verificada/creada.")
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al crear las tablas: {e}")

if __name__ == '__main__':
    if os.path.exists(DB_FILE):
        print(f"Borrando la base de datos existente '{DB_FILE}' para recrearla...")
        os.remove(DB_FILE)
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()
        print("La base de datos se ha configurado correctamente con el esquema final.")