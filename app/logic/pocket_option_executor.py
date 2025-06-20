# app/logic/pocket_option_executor.py
import random
import time

def place_trade(asset: str, amount: float, direction: str, timeframe: str, po_token: str, account_type: str) -> bool:
    """
    SIMULADOR de ejecución de operaciones en Pocket Option, respetando el tipo de cuenta.
    """
    print(f"--- SIMULANDO OPERACIÓN ({account_type.upper()}) ---")
    print(f"   Activo: {asset}")
    print(f"   Importe: ${amount}")
    print(f"   Dirección: {direction}")

    # El comando cambia según el tipo de cuenta
    command_prefix = "/demo_binary_bot" if account_type.upper() == 'DEMO' else "/binary_bot"
    
    # Extraemos el número de la temporalidad (ej: 'M1' -> 1)
    expiration_time = int(''.join(filter(str.isdigit, timeframe)))
    
    command_text = f"{command_prefix} token={po_token} asset={asset} amount={amount} type={direction.lower()} time={expiration_time}"
    
    print(f"   Comando a simular: {command_text}")
    print("   (Simulación: Orden enviada a Pocket Option)")
    
    time.sleep(2)
    is_win = random.random() < 0.70
    
    print(f"   Resultado de la Simulación: {'WIN' if is_win else 'LOSS'}")
    print(f"--------------------------")
    
    return is_win