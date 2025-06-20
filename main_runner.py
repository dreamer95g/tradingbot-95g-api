# main_runner.py
import time
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from app.db.db_manager import get_user_settings, record_trade, get_asset_id_by_name, get_daily_profit_loss
from app.logic.indicator_calculator import check_for_signal
from app.logic.pocket_option_executor import place_trade
from app.bot.notifier import send_telegram_message

ADMIN_TELEGRAM_ID = 888319060 # Tu ID de Telegram

def main_cycle():
    """Realiza un ciclo completo de la lógica del bot, incluyendo gestión de riesgo."""
    print("\n-----------------------------------------")
    print(f"Iniciando ciclo: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    settings = get_user_settings(ADMIN_TELEGRAM_ID)
    if not settings or not settings['is_active']:
        print("Bot detenido o sin configuración. Ciclo finalizado.")
        return

    # 1. GESTIÓN DE RIESGO: Verificar SL y TP diarios
    user_id = settings['user_id']
    daily_pl = get_daily_profit_loss(user_id)
    stop_loss = settings['stop_loss']
    take_profit = settings['take_profit']

    if daily_pl <= -stop_loss:
        print(f"🛑 STOP LOSS DIARIO ALCANZADO (${daily_pl:.2f}). El bot no operará más hoy.")
        # Opcional: Podríamos añadir lógica para detener el bot automáticamente en la DB.
        return
    
    if daily_pl >= take_profit:
        print(f"🎯 TAKE PROFIT DIARIO ALCANZADO (${daily_pl:.2f}). ¡Felicidades! El bot no operará más hoy.")
        return

    # 2. ANÁLISIS DE SEÑAL
    active_asset_name = settings.get('active_asset_name')
    if not active_asset_name:
        print("⚠️ No hay un activo seleccionado para operar.")
        return
        
    db_timeframe = settings.get('timeframe')
    yf_timeframe = db_timeframe.replace('M', '').lower() + 'm'
    
    print(f"Analizando {active_asset_name} en {db_timeframe}...")
    yf_ticker = f"{active_asset_name.replace('/', '')}=X"
    signal = check_for_signal(asset=yf_ticker, timeframe=yf_timeframe)

    # 3. EJECUCIÓN DE OPERACIÓN
    if signal:
        print(f"🔥🔥🔥 ¡SEÑAL ENCONTRADA! -> {signal} en {active_asset_name} 🔥🔥🔥")
        
        asset_id = get_asset_id_by_name(user_id, active_asset_name)
        payout = settings['payout_min']
        po_token = settings['po_token']
        sequence_id = int(time.time())
        
        # --- Ejecución de G0 ---
        trade_amount_g0 = settings['base_amount']
        is_win_g0 = place_trade(active_asset_name, trade_amount_g0, signal, db_timeframe, po_token)
        
        if is_win_g0:
            profit = trade_amount_g0 * (payout / 100.0)
            record_trade(user_id, asset_id, signal, 'G0', trade_amount_g0, payout, 'WIN', profit, sequence_id)
            send_telegram_message(ADMIN_TELEGRAM_ID, f"✅ G0 en {active_asset_name} | Profit: ${profit:.2f}")
        else:
            loss = -trade_amount_g0
            record_trade(user_id, asset_id, signal, 'G0', trade_amount_g0, payout, 'LOSS', loss, sequence_id)
            send_telegram_message(ADMIN_TELEGRAM_ID, f"❌ G0 en {active_asset_name} | Loss: ${loss:.2f}")

            if settings['risk_strategy'] == 'MARTINGALE':
                print("Estrategia Martingale activa. Iniciando G1...")
                send_telegram_message(ADMIN_TELEGRAM_ID, "Iniciando recuperación G1...")
                
                trade_amount_g1 = trade_amount_g0 * 2
                is_win_g1 = place_trade(active_asset_name, trade_amount_g1, signal, db_timeframe, po_token)
                
                if is_win_g1:
                    profit = trade_amount_g1 * (payout / 100.0)
                    record_trade(user_id, asset_id, signal, 'G1', trade_amount_g1, payout, 'WIN', profit, sequence_id)
                    send_telegram_message(ADMIN_TELEGRAM_ID, f"✅ G1 en {active_asset_name} | Profit: ${profit:.2f} (¡Recuperada!)")
                else:
                    loss = -trade_amount_g1
                    record_trade(user_id, asset_id, signal, 'G1', trade_amount_g1, payout, 'LOSS', loss, sequence_id)
                    send_telegram_message(ADMIN_TELEGRAM_ID, f"❌ G1 en {active_asset_name} | Loss: ${loss:.2f}")
    else:
        print("No se encontró ninguna señal válida.")

    print(f"Ciclo finalizado: {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    # Bucle infinito para simular la ejecución continua en el servidor
    while True:
        main_cycle()
        print("Esperando 60 segundos para el próximo ciclo...")
        time.sleep(60)