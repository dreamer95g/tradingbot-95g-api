# app/bot/notifier.py
import requests

# ¡IMPORTANTE! Reemplaza este token con el token real de tu bot de Telegram
TELEGRAM_BOT_TOKEN = "7662615802:AAEh3sZIJUbLKxzqzBGm7-jQ_1DLDsFhyXA"

def send_telegram_message(chat_id: int, message: str):
    """
    Envía un mensaje a un chat de Telegram específico usando la API de Telegram.
    """
    # Usamos la API HTTP de Telegram, que es simple y no requiere la librería completa.
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Lanza un error si la petición falla
        print(f"Mensaje de notificación enviado a {chat_id}.")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar notificación a Telegram: {e}")