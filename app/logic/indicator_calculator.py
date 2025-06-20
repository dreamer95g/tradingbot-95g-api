# app/logic/indicator_calculator.py

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import sys
import os

# Añadimos la ruta raíz para poder importar la configuración
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.core.config import algorithm_settings

def _is_quality_candle(row: pd.Series) -> bool:
    """Función de ayuda para validar una vela individualmente."""
    # Los nombres de columna de yfinance empiezan con mayúscula
    body_size = abs(row['Close'] - row['Open'])
    total_range = row['High'] - row['Low']
    if total_range > 0:
        if (body_size / total_range) < algorithm_settings.NO_DOJI_THRESHOLD:
            return False
    else:
        return False

    if algorithm_settings.WICK_FILTER_ACTIVE:
        upper_wick = row['High'] - max(row['Open'], row['Close'])
        lower_wick = min(row['Open'], row['Close']) - row['Low']
        if upper_wick > body_size or lower_wick > body_size:
            return False
    return True

def _is_symmetric(c1: pd.Series, c2: pd.Series, c3: pd.Series) -> bool:
    """Función de ayuda para validar la simetría entre las 3 velas."""
    b1 = abs(c1['Close'] - c1['Open'])
    b2 = abs(c2['Close'] - c2['Open'])
    b3 = abs(c3['Close'] - c3['Open'])
    
    max_body = max(b1, b2, b3)
    min_body = min(b1, b2, b3)
    if max_body > 0:
        return min_body >= max_body * algorithm_settings.SYMMETRY_MIN_MAX_RATIO
    return False

def check_for_signal(asset: str, timeframe: str) -> str | None:
    """
    Función principal que analiza un activo y devuelve una señal si se cumplen las condiciones.
    """
    try:
        # 1. Descargar datos históricos (LÍNEA CORREGIDA)
        ticker = yf.Ticker(asset)
        # Se ha eliminado el argumento 'progress=False' que causaba el error.
        data = ticker.history(period="5d", interval=timeframe, auto_adjust=False)
        
        if data.empty:
            print(f"No se pudieron descargar datos para {asset}")
            return None

        # 2. Calcular los indicadores técnicos necesarios
        # pandas_ta es inteligente y funciona con columnas en mayúscula o minúscula.
        custom_strategy = ta.Strategy(
            name="Pattern1x1BOStrategy",
            description="ADX y EMA para la estrategia Pattern 1x1 BO",
            ta=[
                {"kind": "adx", "length": algorithm_settings.ADX_PERIOD},
                {"kind": "ema", "length": algorithm_settings.EMA_TREND_PERIOD, "col_names": ("ema_trend",)},
            ]
        )
        data.ta.strategy(custom_strategy)
        
        if len(data) < 4:
            return None 

        candle1, candle2, candle3 = data.iloc[-2], data.iloc[-3], data.iloc[-4]
        
        if not all([_is_quality_candle(c) for c in [candle1, candle2, candle3]]):
            return None

        if not _is_symmetric(candle1, candle2, candle3):
            return None

        is_call_pattern = (candle3['Close'] < candle3['Open'] and 
                           candle2['Close'] > candle2['Open'] and
                           candle1['Close'] < candle1['Open'])
        
        is_put_pattern = (candle3['Close'] > candle3['Open'] and 
                          candle2['Close'] < candle2['Open'] and 
                          candle1['Close'] > candle1['Open'])

        signal = 'CALL' if is_call_pattern else 'PUT' if is_put_pattern else None
        if not signal:
            return None

        # 7. Aplicar el Filtro de Tendencia Adaptativo
        allow_call, allow_put = True, True
        adx_col_name = f'ADX_{algorithm_settings.ADX_PERIOD}'
        market_is_trending = candle1[adx_col_name] > algorithm_settings.ADX_THRESHOLD
        
        filter_mode = algorithm_settings.TREND_FILTER_MODE
        if filter_mode == "Strict EMA" or (filter_mode == "ADX-Gated EMA (Hybrid)" and market_is_trending):
            if candle1['Close'] > candle1['ema_trend']: allow_put = False
            else: allow_call = False
        
        if signal == 'CALL' and allow_call: return 'CALL'
        if signal == 'PUT' and allow_put: return 'PUT'
            
        return None

    except Exception as e:
        print(f"Error inesperado al calcular la señal para {asset}: {e}")
        return None

# --- Bloque de Prueba ---
if __name__ == '__main__':
    print("Ejecutando prueba del calculador de indicador...")
    test_asset = "EURUSD=X"
    test_timeframe = "1m"
    result = check_for_signal(test_asset, test_timeframe)
    
    if result:
        print(f"RESULTADO DE LA PRUEBA: ¡Señal encontrada! -> {result} en {test_asset} ({test_timeframe})")
    else:
        print(f"RESULTADO DE LA PRUEBA: No se encontró señal para {test_asset} ({test_timeframe}) en la última vela cerrada.")