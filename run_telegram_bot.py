# run_telegram_bot.py (Versión para Producción con Webhook)
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from app.bot.telegram_controller import setup_telegram_app, handle_telegram_update

# Crea la aplicación FastAPI
api = FastAPI(title="TradingBot Telegram Webhook")

# Configura el bot de Telegram y el dispatcher
application = setup_telegram_app()

@api.post("/webhook")
async def telegram_webhook(request: Request):
    """Este endpoint recibe las actualizaciones de Telegram."""
    json_data = await request.json()
    update = Update.de_json(json_data, application.bot)
    await handle_telegram_update(update, application)
    return {"status": "ok"}

@api.get("/")
def index():
    return {"message": "El webhook del bot de Telegram está activo."}

# Esta parte es solo para pruebas locales, no se usará en PythonAnywhere
if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)