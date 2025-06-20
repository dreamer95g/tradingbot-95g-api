# main_runner.py
import time, sys, os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
from app.db.db_manager import get_user_settings, record_trade, get_asset_id_by_name, get_daily_profit_loss
from app.logic.indicator_calculator import check_for_signal
from app.logic.pocket_option_executor import place_trade
from app.bot.notifier import send_telegram_message

ADMIN_TELEGRAM_ID = 888319060

def main_cycle():
    print(f"\n--- Ciclo: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    settings = get_user_settings(ADMIN_TELEGRAM_ID)
    if not settings or not settings['is_active']:
        print("Bot detenido o sin configuración.")
        return

    user_id, daily_pl = settings['user_id'], get_daily_profit_loss(settings['user_id'])
    if daily_pl <= -settings['stop_loss']: print(f"🛑 STOP LOSS ALCANZADO (${daily_pl:.2f})."); return
    if daily_pl >= settings['take_profit']: print(f"🎯 TAKE PROFIT ALCANZADO (${daily_pl:.2f})."); return

    active_asset, db_timeframe = settings.get('active_asset_name'), settings.get('timeframe')
    if not active_asset: print("⚠️ No hay activo seleccionado."); return
        
    yf_timeframe = db_timeframe.replace('M', '').lower() + 'm'
    print(f"Analizando {active_asset} en {db_timeframe}...")
    yf_ticker = f"{active_asset.replace('/', '')}=X"
    signal = check_for_signal(asset=yf_ticker, timeframe=yf_timeframe)

    if signal:
        print(f"🔥🔥🔥 ¡SEÑAL ENCONTRADA!: {signal} en {active_asset} 🔥🔥🔥")
        
        asset_id, payout, po_token = get_asset_id_by_name(user_id, active_asset), settings['payout_min'], settings['po_token']
        account_type = settings['account_type']
        sequence_id = int(time.time())
        
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

            if settings['risk_strategy'] == 'MARTINGALE':
                send_telegram_message(ADMIN_TELEGRAM_ID, "Iniciando G1...")
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
        print("No se encontró señal.")

if __name__ == "__main__":
    while True:
        main_cycle()
        print("Esperando 60 segundos...")
        time.sleep(60)