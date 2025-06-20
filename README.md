# TradingBot-95g-API v1.0

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688?style=for-the-badge&logo=fastapi)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-2CA5E0?style=for-the-badge&logo=telegram)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite)

Este repositorio contiene el código fuente del backend para un bot de trading autónomo diseñado para ejecutar la estrategia **"Pattern 1x1 BO"** en la plataforma Pocket Option. El sistema es completamente soberano, calculando sus propios indicadores y gestionando su estado sin depender de servicios de alertas externos.

## 🚀 Visión del Proyecto

El objetivo es crear un sistema de trading automatizado, robusto y seguro. La arquitectura está dividida en dos fases principales:
*   **Fase 1 (MVP):** Un bot completamente funcional controlado y monitorizado a través de una interfaz de Telegram.
*   **Fase 2 (Futura):** Desarrollo de un panel de control web profesional utilizando React para una experiencia de usuario avanzada.

---

## 💡 Lógica de la Estrategia: "Pattern 1x1 BO" (Adaptativa)

El algoritmo se basa en la **confluencia** de un patrón de velas con múltiples filtros de calidad para maximizar la probabilidad de acierto.

1.  **Patrón Base (1x1):** Busca un patrón de reversión de 3 velas (`Bajista -> Alcista -> Bajista` para un CALL, y viceversa para un PUT).
2.  **Filtros de Calidad:**
    *   **Cuerpo (No-Doji):** Las velas deben tener un cuerpo significativo.
    *   **Mechas:** Las mechas no pueden ser desproporcionadamente grandes en comparación con el cuerpo.
    *   **Simetría:** El cuerpo de la vela más pequeña debe ser al menos el 40% del cuerpo de la más grande.
3.  **Filtro de Tendencia (Adaptativo):**
    *   Utiliza el **ADX** para medir la fuerza de la tendencia y una **EMA** de 15 períodos para su dirección.
    *   **En Mercado de Tendencia (ADX > 20):** Opera estrictamente a favor de la tendencia marcada por la EMA.
    *   **En Mercado Lateral (ADX < 20):** Actúa como un cazador de reversiones, aceptando señales en ambas direcciones.

---

## 🛠️ Pila Tecnológica (Backend)

| Componente | Tecnología | Versión (Aprox.) |
| :--- | :--- | :--- |
| Lenguaje | **Python** | `3.11` |
| Framework API | **FastAPI** | `0.103.2` |
| Servidor ASGI | **Uvicorn** | `0.23.2` |
| Base de Datos | **SQLite** | `3.x` |
| Interfaz MVP | **python-telegram-bot**| `20.6` |
| Obtención de Datos | **yfinance** | `0.2.28` |
| Análisis de Datos| **pandas** & **pandas-ta**| `2.0.3` & `0.3.14b`|
| Hashing de Contraseñas | **bcrypt** | `4.0.1` |
| Peticiones HTTP | **requests** | `2.31.0` |

---


## ⚙️ Guía de Instalación y Ejecución Local

Sigue estos pasos para poner en marcha el bot en un entorno de desarrollo.

### 1. Prerrequisitos
*   Tener instalado **Python 3.11**.
*   Tener una cuenta de Telegram y un token de Bot generado por `@BotFather`.
*   Tener el token del bot de Telegram de Pocket Option.

### 2. Configuración del Entorno
```bash
# 1. Clona el repositorio
git clone https://github.com/dreamer95g/tradingbot-95g-api.git
cd tradingbot-95g-api

# 2. Crea y activa el entorno virtual de Python 3.11
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instala todas las dependencias
pip install -r requirements.txt

3. Configuración de la Base de Datos

# 1. Edita el archivo `app/db/seed_database.py` con tu email y contraseña de admin.
# (Abre el archivo y modifica las variables ADMIN_EMAIL y ADMIN_PASSWORD)

# 2. Ejecuta el script para crear la base de datos y sembrar los datos iniciales.
python app/db/database_setup.py
python app/db/seed_database.py

4. Ejecución del Bot
El sistema requiere dos procesos corriendo en paralelo.

# En una terminal (con venv activo):
# Inicia el controlador de Telegram para recibir tus comandos.
python run_telegram_bot.py

# En una segunda terminal (con venv activo):
# Inicia el motor de trading que analiza el mercado.
python main_runner.py

5. Primer Uso en Telegram
Abre Telegram y busca a tu bot.
Envía el comando /start.
Importante: Envía el comando /sync para enlazar tu chat de Telegram con tu cuenta de admin en la base de datos.
Usa /config, /assets, /run y /stop para controlar el bot.