import sqlite3
import bcrypt
import os
import sys

# Añadimos la ruta raíz del proyecto al path para poder importar desde database_setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.db.database_setup import create_connection

# --- CONFIGURACIÓN INICIAL DEL ADMIN ---
# Modifica estos valores con tu información real
ADMIN_EMAIL = "gabry95g@gmail.com"
ADMIN_PASSWORD = "Segur100.." # ¡Cámbiala!

def seed_data():
    """Inserta los datos iniciales (admin, settings, assets) si la DB está vacía."""
    conn = create_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # 1. Verificar si el usuario admin ya existe
        cursor.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
        user = cursor.fetchone()

        if user:
            print(f"El usuario admin '{ADMIN_EMAIL}' ya existe. No se realizarán acciones.")
            return

        print("Base de datos vacía. Sembrando datos iniciales...")

        # 2. Si no existe, crear el usuario admin
        print(f"Creando usuario admin para '{ADMIN_EMAIL}'...")
        # Encriptar la contraseña (hashing)
        password_bytes = ADMIN_PASSWORD.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        cursor.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (ADMIN_EMAIL, hashed_password.decode('utf-8'), 'admin')
        )
        user_id = cursor.lastrowid # Obtenemos el ID del usuario recién creado

        # 3. Añadir activos por defecto para este usuario
        print("Añadiendo activos por defecto (EUR/USD, BTC/USD)...")
        default_assets = ['EUR/USD', 'BTC/USD']
        for asset_name in default_assets:
            cursor.execute(
                "INSERT INTO assets (user_id, name) VALUES (?, ?)",
                (user_id, asset_name)
            )
        
        # Obtenemos el ID del primer activo para ponerlo como activo por defecto
        cursor.execute("SELECT id FROM assets WHERE user_id = ? AND name = ?", (user_id, default_assets[0]))
        active_asset_id = cursor.fetchone()[0]

        # 4. Crear la fila de configuración por defecto para este usuario
        print(f"Creando configuración por defecto para el usuario con ID: {user_id}")
        cursor.execute(
            "INSERT INTO settings (user_id, active_asset_id) VALUES (?, ?)",
            (user_id, active_asset_id)
        )

        conn.commit()
        print("¡Datos iniciales sembrados con éxito!")

    except sqlite3.Error as e:
        print(f"Error al sembrar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    seed_data()