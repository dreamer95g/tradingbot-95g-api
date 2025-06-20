# main_runner.py
import time
import sys
import os

# --- Configuración del Path ---
# Esto asegura que el script puede encontrar los otros módulos
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# --- Importaciones de nuestros Módulos ---
from app.db.db_manager import get_user_settings, record_trade, get_asset_id_by_name, get_daily_profit_loss
from app.logic.indicator_calculator import check_for_signal
from app.logic.pocket_option_executor import place_trade
from app.bot.notifier import send_telegram_message

# --- Constantes ---
# Asumimos que solo hay un admin. En el futuro, esto podría cambiar.
ADMIN_TELEGRAM_ID = 888319060 # Tu ID de Telegram

def main_cycle():
    """
    Realiza un ciclo completo de la lógica del bot:
    1. Verifica el estado y la gestión de riesgo.
    2. Analiza el mercado en busca de señales.
    3. Si hay señal, ejecuta la operación (simulada).
    4. Registra el resultado en la base de datos.
    5. Notifica al usuario.
    """
    print(f"\n--- INICIANDO CICLO DE ANÁLISIS: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")

    # 1. Obtener Configuración y Verificar Estado
    settings = get_user_settings(ADMIN_TELEGRAM_ID)
    if not settings or not settings['is_active']:
        print("Bot detenido o sin configuración. Ciclo finalizado.")
        return

    # 2. Verificar Gestión de Riesgo (SL/TP Diario)
    user_id = settings['user_id']
    daily_pl = get_daily_profit_loss(user_id)
    stop_loss = settings['stop_loss']
    take_profit = settings['take_profit']

    if daily_pl <= -stop_loss:
        print(f"🛑 STOP LOSS DIARIO ALCANZADO (${daily_pl:.2f}). El bot no operará más hoy.")
        return
    
    if daily_pl >= take_profit:
        print(f"🎯 TAKE PROFIT DIARIO ALCANZADO (${daily_pl:.2f}). El bot no operará más hoy.")
        return

    # 3. Analizar el Mercado
    active_asset = settings.get('active_asset_name')
    db_timeframe = settings.get('timeframe')
    if not active_asset:
        print("⚠️ No hay un activo seleccionado para operar.")
        return
        
    yf_timeframe = db_timeframe.replace('M', '').lower() + 'm'
    print(f"Analizando {active_asset} en {db_timeframe}...")
    yf_ticker = f"{active_asset.replace('/', '')}=X"
    signal = check_for_signal(asset=yf_ticker, timeframe=yf_timeframe)

    # 4. Ejecutar si hay Señal
    if signal:
        print(f"🔥🔥🔥 ¡SEÑAL ENCONTRADA!: {signal} en {active_asset} 🔥🔥🔥")
        
        asset_id = get_asset_id_by_name(user_id, active_asset)
        payout = settings['payout_min']
        po_token = settings['po_token']
        account_type = settings['account_type']
        sequence_id = int(time.time())
        
        # --- Lógica de Ejecución G0 ---
        amount_g0 = settings['base_amount']
        win_g0 = place_trade(active_asset, amount_g0, signal, db_timeframe, po_token, account_type)
        
        if win_g0:
            profit = amount_g0 * (payout / 100.0)
            record_trade(user_id, asset_id, signal, 'G0', amount_g0, payout, 'WIN', profit, sequence_id)
            send_telegram_message(ADMIN_TELEGRAM_ID, f"✅ G0 en {active_asset} | Profit: ${profit:.2f}")
        else:
            loss = -amount_g0
            record_trade(user_id, asset_id, signal, 'G0', amount_g0, payout, 'LOSS', loss, sequence_id)
            send_telegram_message(ADMIN_TELEGRAM_ID, f"❌ G0 en {active_asset} | Loss: ${loss:.2f}")

            # --- Lógica de Martingale (G1) ---
            if settings['risk_strategy'] == 'MARTINGALE':
                send_telegram_message(ADMIN_TELEGRAM_ID, "Iniciando recuperación G1...")
                amount_g1 = amount_g0 * 2
                win_g1 = place_trade(active_asset, amount_g1, signal, db_timeframe, po_token, account_type)
                
                if win_g1:
                    profit = amount_g1 * (payout / 100.0)
                    record_trade(user_id, asset_id, signal, 'G1', amount_g1, payout, 'WIN', profit, sequence_id)
                    send_telegram_message(ADMIN_TELEGRAM_ID, f"✅ G1 en {active_asset} | Profit: ${profit:.2f} (Recuperada)")
                else:
                    loss = -amount_g1
                    record_trade(user_id, asset_id, signal, 'G1', amount_g1, payout, 'LOSS', loss, sequence_id)
                    send_telegram_message(ADMIN_TELEGRAM_ID, f"❌ G1 en {active_asset} | Loss: ${loss:.2f}")
    else:
        print("No se encontró ninguna señal válida en este ciclo.")

    print(f"--- CICLO FINALIZADO: {time.strftime('%H:%M:%S')} ---")

if __name__ == "__main__":
    main_cycle()