# app/bot/telegram_controller.py

import logging
import sys
import os
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURACIÓN DE ADMINISTRADOR ---
# ¡IMPORTANTE! Reemplaza estos valores con tus credenciales reales.
# En un proyecto real, estos valores deberían venir de variables de entorno.
TELEGRAM_BOT_TOKEN = "7662615802:AAEh3sZIJUbLKxzqzBGm7-jQ_1DLDsFhyXA"
ADMIN_TELEGRAM_ID = 888319060 # Este es tu ID numérico
ADMIN_EMAIL = "gabry95g@gmail.com" # El mismo email que usaste en seed_database.py

# --- CONFIGURACIÓN DEL PROYECTO ---
# Añadimos la ruta raíz para poder importar los otros módulos
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Importamos las funciones del gestor de la base de datos
from app.db.db_manager import (
    get_user_settings, 
    update_bot_status, 
    get_user_assets, 
    set_active_asset,
    sync_telegram_id
)

# Configurar logging para ver errores y actividad del bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- FUNCIONES DE AYUDA Y AUTENTICACIÓN ---

async def is_admin(update: Update) -> bool:
    """Verifica si el usuario que interactúa es el administrador definido."""
    user = update.effective_user
    if user.id != ADMIN_TELEGRAM_ID:
        # Responde adecuadamente si es un mensaje o un botón
        if update.message:
            await update.message.reply_text("Lo siento, no tienes permiso para usar este bot.")
        elif update.callback_query:
            await update.callback_query.answer("No tienes permiso.", show_alert=True)
        return False
    return True

# --- FUNCIONES DE COMANDOS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida y la lista de comandos."""
    if not await is_admin(update): return
    
    await update.message.reply_html(
        f"👋 ¡Hola, {update.effective_user.first_name}! Soy tu bot de trading personal.\n\n"
        "<b>Primer Paso:</b> Usa /sync para enlazar este chat a tu cuenta de admin.\n\n"
        "<b>Comandos Principales:</b>\n"
        "/run - Iniciar el análisis de mercado.\n"
        "/stop - Detener el bot.\n"
        "/config - Ver la configuración actual.\n"
        "/assets - Ver y seleccionar el activo a operar."
    )

async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sincroniza el ID de este chat de Telegram con la cuenta del admin en la DB."""
    if not await is_admin(update): return

    if sync_telegram_id(admin_email=ADMIN_EMAIL, telegram_user_id=update.effective_user.id):
        await update.message.reply_text("✅ ¡Sincronización completa! Este chat ahora está enlazado a tu cuenta de admin.")
    else:
        await update.message.reply_text("❌ Error durante la sincronización. Revisa los logs del servidor y asegúrate de que el email de admin es correcto.")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia el bot cambiando su estado en la DB."""
    if not await is_admin(update): return

    if update_bot_status(update.effective_user.id, is_active=True):
        await update.message.reply_text("▶️ Bot iniciado. El próximo ciclo de análisis comenzará a operar.")
    else:
        await update.message.reply_text("❌ Error al intentar iniciar el bot. ¿Estás sincronizado? Usa /sync.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detiene el bot cambiando su estado en la DB."""
    if not await is_admin(update): return

    if update_bot_status(update.effective_user.id, is_active=False):
        await update.message.reply_text("⏹️ Bot detenido. No se realizarán más operaciones.")
    else:
        await update.message.reply_text("❌ Error al intentar detener el bot.")

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la configuración actual del bot desde la base de datos."""
    if not await is_admin(update): return
        
    settings = get_user_settings(update.effective_user.id)
    if not settings:
        await update.message.reply_text("❌ Error: No se encontró tu configuración. Usa /sync primero.")
        return

    is_active_text = "Corriendo ✅" if settings['is_active'] else "Detenido ⏹️"
    strategy_map = {'SIMPLE': 'Simple', 'MARTINGALE': 'Martingale (G1)', 'COMPOUND': 'Compuesto'}
    strategy_text = strategy_map.get(settings['risk_strategy'], 'Desconocida')

    text = (
        f"⚙️ **Configuración Actual** ⚙️\n\n"
        f"**Estado del Bot:** {is_active_text}\n\n"
        f"**Activo en Operación:** `{settings['active_asset_name'] or 'Ninguno'}`\n"
        f"**Temporalidad:** `{settings['timeframe']}`\n\n"
        f"**Importe Base:** `${settings['base_amount']}`\n"
        f"**Payout Mínimo:** `{settings['payout_min']}%`\n\n"
        f"**Gestión de Riesgo:**\n"
        f"  - Estrategia: `{strategy_text}`\n"
        f"  - Stop Loss: `${settings['stop_loss']}`\n"
        f"  - Take Profit: `${settings['take_profit']}`"
    )
    await update.message.reply_html(text)

async def assets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de activos y permite seleccionar uno."""
    if not await is_admin(update): return

    assets = get_user_assets(update.effective_user.id)
    if not assets:
        await update.message.reply_text("No tienes activos configurados. En el futuro, podrás añadirlos desde aquí.")
        return
    
    keyboard = []
    for asset in assets:
        button_text = f"✅ {asset['name']}" if asset['id'] == asset['active_asset_id'] else asset['name']
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"set_asset_{asset['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona el activo que deseas operar:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las pulsaciones de los botones en línea."""
    if not await is_admin(update): return
    
    query = update.callback_query
    await query.answer()

    if query.data.startswith("set_asset_"):
        asset_id = int(query.data.split("_")[2])
        if set_active_asset(query.from_user.id, asset_id):
            await query.edit_message_text(text=f"✅ Activo actualizado.")
            await assets_command(update.callback_query, context) # Reenvía el menú para mostrar el cambio
        else:
            await query.edit_message_text(text="❌ Error al actualizar el activo.")

def main() -> None:
    """Inicia el bot de Telegram y lo mantiene corriendo."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Registra los manejadores de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sync", sync_command))
    application.add_handler(CommandHandler("run", run_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("assets", assets_command))
    
    # Registra el manejador para los botones
    application.add_handler(CallbackQueryHandler(button_handler))

    print("El bot de Telegram está corriendo. Presiona Ctrl-C para detener.")
    application.run_polling()

if __name__ == "__main__":
    main()