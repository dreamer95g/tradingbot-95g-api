# app/db/db_manager.py
import sqlite3
import os
import time

DB_NAME = "trading-bot95g.db"
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), DB_NAME)

def create_connection():
    try:
        conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; return conn
    except sqlite3.Error as e: print(f"Error al conectar con SQLite: {e}")

def get_user_settings(telegram_user_id: int):
    conn = create_connection();
    if not conn: return None
    try:
        cursor = conn.cursor(); query = "SELECT s.*, u.email, a.name as active_asset_name FROM settings s JOIN users u ON s.user_id = u.id LEFT JOIN assets a ON s.active_asset_id = a.id WHERE s.telegram_user_id = ?"
        cursor.execute(query, (telegram_user_id,)); row = cursor.fetchone(); return dict(row) if row else None
    finally: conn.close()

def update_bot_status(telegram_user_id: int, is_active: bool):
    conn = create_connection();
    if not conn: return False
    try:
        cursor = conn.cursor(); cursor.execute("UPDATE settings SET is_active = ? WHERE telegram_user_id = ?", (1 if is_active else 0, telegram_user_id)); conn.commit(); return cursor.rowcount > 0
    finally: conn.close()

def get_user_assets(telegram_user_id: int):
    conn = create_connection();
    if not conn: return []
    try:
        cursor = conn.cursor(); query = "SELECT a.id, a.name, s.active_asset_id FROM assets a JOIN users u ON a.user_id = u.id JOIN settings s ON u.id = s.user_id WHERE u.id = (SELECT user_id FROM settings WHERE telegram_user_id = ?)"
        cursor.execute(query, (telegram_user_id,)); assets = cursor.fetchall(); return [dict(row) for row in assets]
    finally: conn.close()

def set_active_asset(telegram_user_id: int, asset_id: int):
    conn = create_connection();
    if not conn: return False
    try:
        cursor = conn.cursor(); cursor.execute("UPDATE settings SET active_asset_id = ? WHERE telegram_user_id = ?", (asset_id, telegram_user_id)); conn.commit(); return cursor.rowcount > 0
    finally: conn.close()

def get_asset_id_by_name(user_id: int, asset_name: str):
    conn = create_connection();
    if not conn: return None
    try:
        cursor = conn.cursor(); cursor.execute("SELECT id FROM assets WHERE user_id = ? AND name = ?", (user_id, asset_name)); result = cursor.fetchone(); return result[0] if result else None
    finally: conn.close()

def record_trade(user_id, asset_id, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id):
    conn = create_connection();
    if not conn: return
    try:
        cursor = conn.cursor(); timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO trades (user_id, asset_id, timestamp, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(query, (user_id, asset_id, timestamp, direction, trade_level, amount, payout_used, result, profit_loss, sequence_id)); conn.commit(); print(f"Operación registrada: {result} de ${profit_loss:.2f}")
    finally: conn.close()

def get_daily_profit_loss(user_id: int):
    conn = create_connection();
    if not conn: return 0.0
    try:
        cursor = conn.cursor(); today_date = time.strftime('%Y-%m-%d'); query = "SELECT SUM(profit_loss) FROM trades WHERE user_id = ? AND date(timestamp) = ?"
        cursor.execute(query, (user_id, today_date)); result = cursor.fetchone()[0]; return result if result is not None else 0.0
    finally: conn.close()

def sync_telegram_id(admin_email: str, telegram_user_id: int):
    conn = create_connection();
    if not conn: return False
    try:
        cursor = conn.cursor(); cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,)); user_row = cursor.fetchone()
        if not user_row: print(f"Sync Error: No user with email {admin_email}"); return False
        user_id = user_row[0]; query = "UPDATE settings SET telegram_user_id = ? WHERE user_id = ?"
        cursor.execute(query, (telegram_user_id, user_id)); conn.commit()
        if cursor.rowcount > 0: print(f"Sync OK: Telegram ID {telegram_user_id} -> {admin_email}"); return True
        else: print(f"Sync Error: No settings row for user_id {user_id}"); return False
    finally: conn.close()

def update_account_type(telegram_user_id: int, new_type: str) -> bool:
    """Actualiza el tipo de cuenta (DEMO o REAL) para un usuario."""
    conn = create_connection();
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE settings SET account_type = ? WHERE telegram_user_id = ?"
        cursor.execute(query, (new_type.upper(), telegram_user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error en DB (update_account_type): {e}")
        return False
    finally:
        conn.close()