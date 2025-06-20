# app/bot/telegram_controller.py
import logging, sys, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TELEGRAM_BOT_TOKEN = "7662615802:AAEh3sZIJUbLKxzqzBGm7-jQ_1DLDsFhyXA"
ADMIN_TELEGRAM_ID = 888319060
ADMIN_EMAIL = "gabry95g@gmail.com"

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
    
from app.db.db_manager import (get_user_settings, update_bot_status, get_user_assets, 
                             set_active_asset, sync_telegram_id, update_account_type)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_admin(update: Update) -> bool:
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        if update.message: await update.message.reply_text("No tienes permiso.")
        elif update.callback_query: await update.callback_query.answer("No tienes permiso.", show_alert=True)
        return False
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    await update.message.reply_html(
        f"👋 ¡Hola, {update.effective_user.first_name}! Soy tu bot de trading personal.\n\n"
        "<b>Primer Paso:</b> Usa /sync para enlazar este chat a tu cuenta.\n\n"
        "<b>Comandos Principales:</b>\n"
        "/run - Iniciar el bot\n"
        "/stop - Detener el bot\n"
        "/config - Ver la configuración actual\n"
        "/assets - Seleccionar el activo a operar\n"
        "/account - Cambiar entre cuenta DEMO y REAL"
    )

async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    if sync_telegram_id(admin_email=ADMIN_EMAIL, telegram_user_id=update.effective_user.id):
        await update.message.reply_text("✅ ¡Sincronización completa!")
    else:
        await update.message.reply_text("❌ Error durante la sincronización.")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    if update_bot_status(update.effective_user.id, is_active=True):
        await update.message.reply_text("▶️ Bot iniciado.")
    else:
        await update.message.reply_text("❌ Error al iniciar. ¿Estás sincronizado? (/sync)")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    if update_bot_status(update.effective_user.id, is_active=False):
        await update.message.reply_text("⏹️ Bot detenido.")
    else:
        await update.message.reply_text("❌ Error al detener.")

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    settings = get_user_settings(update.effective_user.id)
    if not settings:
        await update.message.reply_text("❌ Error: No se encontró tu configuración. Usa /sync primero.")
        return

    is_active_text = "Corriendo ✅" if settings['is_active'] else "Detenido ⏹️"
    account_type_text = "DEMO 🧪" if settings['account_type'] == 'DEMO' else "REAL 💰"
    strategy_map = {'SIMPLE': 'Simple', 'MARTINGALE': 'Martingale (G1)', 'COMPOUND': 'Compuesto'}
    strategy_text = strategy_map.get(settings['risk_strategy'], 'Desconocida')

    text = (f"⚙️ **Configuración Actual** ⚙️\n\n"
            f"**Estado del Bot:** {is_active_text}\n"
            f"**Modo de Cuenta:** {account_type_text}\n\n"
            f"**Activo en Operación:** `{settings['active_asset_name'] or 'Ninguno'}`\n"
            f"**Temporalidad:** `{settings['timeframe']}`\n\n"
            f"**Importe Base:** `${settings['base_amount']}`\n"
            f"**Payout Mínimo:** `{settings['payout_min']}%`\n\n"
            f"**Gestión de Riesgo:**\n"
            f"  - Estrategia: `{strategy_text}`\n"
            f"  - Stop Loss: `${settings['stop_loss']}`\n"
            f"  - Take Profit: `${settings['take_profit']}`")
    await update.message.reply_html(text)

async def assets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    assets = get_user_assets(update.effective_user.id)
    if not assets:
        await update.message.reply_text("No tienes activos configurados.")
        return
    keyboard = [[InlineKeyboardButton(f"✅ {a['name']}" if a['id']==a['active_asset_id'] else a['name'], callback_data=f"set_asset_{a['id']}")] for a in assets]
    await update.message.reply_text('Selecciona el activo a operar:', reply_markup=InlineKeyboardMarkup(keyboard))

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    settings = get_user_settings(update.effective_user.id)
    current_type = settings.get('account_type', 'DEMO')
    keyboard = [
        [InlineKeyboardButton("Cambiar a REAL 💰" if current_type == 'DEMO' else "Cambiar a DEMO 🧪", callback_data="toggle_account_type")]
    ]
    await update.message.reply_text(f"Modo de cuenta actual: **{current_type}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update): return
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("set_asset_"):
        asset_id = int(query.data.split("_")[2])
        if set_active_asset(query.from_user.id, asset_id):
            await query.edit_message_text(text="✅ Activo actualizado.")
        else: await query.edit_message_text(text="❌ Error al actualizar.")
    elif query.data == "toggle_account_type":
        settings = get_user_settings(query.from_user.id)
        current_type = settings.get('account_type', 'DEMO')
        new_type = 'REAL' if current_type == 'DEMO' else 'DEMO'
        if update_account_type(query.from_user.id, new_type):
            await query.edit_message_text(f"✅ Tipo de cuenta cambiado a **{new_type}**.", parse_mode='Markdown')
        else: await query.edit_message_text("❌ Error al cambiar el tipo de cuenta.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sync", sync_command))
    application.add_handler(CommandHandler("run", run_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("assets", assets_command))
    application.add_handler(CommandHandler("account", account_command)) # Nuevo comando
    application.add_handler(CallbackQueryHandler(button_handler))
    print("El bot de Telegram está corriendo...")
    application.run_polling()

if __name__ == "__main__":
    main()