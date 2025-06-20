# app/db/db_manager.py
import sqlite3
import os
import time

DB_NAME = "trading-bot95g.db"
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), DB_NAME)

# --- Funciones de Conexión ---
def create_connection():
    """Crea y devuelve una conexión a la base de datos."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Error al conectar con SQLite: {e}")
    return conn

# --- Funciones de Lectura (Getters) ---
def get_user_settings(telegram_user_id: int) -> dict | None:
    conn = create_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT s.*, u.email, a.name as active_asset_name
            FROM settings s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN assets a ON s.active_asset_id = a.id
            WHERE s.telegram_user_id = ?
        """
        cursor.execute(query, (telegram_user_id,))
        settings_row = cursor.fetchone()
        return dict(settings_row) if settings_row else None
    except sqlite3.Error as e:
        print(f"Error en DB (get_user_settings): {e}")
        return None
    finally:
        conn.close()

def get_user_assets(telegram_user_id: int) -> list[dict]:
    conn = create_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.name, s.active_asset_id
            FROM assets a
            JOIN users u ON a.user_id = u.id
            JOIN settings s ON u.id = s.user_id
            WHERE u.id = (SELECT user_id FROM settings WHERE telegram_user_id = ?)
        """
        cursor.execute(query, (telegram_user_id,))
        assets = cursor.fetchall()
        return [dict(row) for row in assets]
    except sqlite3.Error as e:
        print(f"Error en DB (get_user_assets): {e}")
        return []
    finally:
        conn.close()

def get_asset_id_by_name(user_id: int, asset_name: str) -> int | None:
    conn = create_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        query = "SELECT id FROM assets WHERE user_id = ? AND name = ?"
        cursor.execute(query, (user_id, asset_name))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error en DB (get_asset_id_by_name): {e}")
        return None
    finally:
        conn.close()

def get_daily_profit_loss(user_id: int) -> float:
    conn = create_connection()
    if not conn: return 0.0
    try:
        cursor = conn.cursor()
        today_date = time.strftime('%Y-%m-%d')
        query = "SELECT SUM(profit_loss) FROM trades WHERE user_id = ? AND date(timestamp) = ?"
        cursor.execute(query, (user_id, today_date))
        result = cursor.fetchone()[0]
        return result if result is not None else 0.0
    except sqlite3.Error as e:
        print(f"Error en DB (get_daily_profit_loss): {e}")
        return 0.0
    finally:
        conn.close()

# --- Funciones de Escritura (Setters/Updaters) ---
def update_bot_status(telegram_user_id: int, is_active: bool) -> bool:
    conn = create_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE settings SET is_active = ? WHERE telegram_user_id = ?"
        cursor.execute(query, (1 if is_active else 0, telegram_user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error en DB (update_bot_status): {e}")
        return False
    finally:
        conn.close()

def set_active_asset(telegram_user_id: int, asset_id: int) -> bool:
    conn = create_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE settings SET active_asset_id = ? WHERE telegram_user_id = ?"
        cursor.execute(query, (asset_id, telegram_user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error en DB (set_active_asset): {e}")
        return False
    finally:
        conn.close()

def record_trade(user_id, asset_id, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id):
    conn = create_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO trades (user_id, asset_id, timestamp, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(query, (user_id, asset_id, timestamp, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id))
        conn.commit()
        print(f"Operación registrada en la DB: {result} de ${profit_loss:.2f}")
    except sqlite3.Error as e:
        print(f"Error en DB (record_trade): {e}")
    finally:
        conn.close()

def sync_telegram_id(admin_email: str, telegram_user_id: int) -> bool:
    conn = create_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        user_row = cursor.fetchone()
        
        if not user_row:
            print(f"Error de sincronización: No se encontró un usuario con el email {admin_email}")
            return False
        
        user_id = user_row[0]
        query = "UPDATE settings SET telegram_user_id = ? WHERE user_id = ?"
        cursor.execute(query, (telegram_user_id, user_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Sincronización exitosa: ID de Telegram {telegram_user_id} asociado al usuario {admin_email}.")
            return True
        else:
            print(f"Error de sincronización: No se encontró una fila de settings para el user_id {user_id}.")
            return False
    except sqlite3.Error as e:
        print(f"Error en DB (sync_telegram_id): {e}")
        return False
    finally:
        conn.close()