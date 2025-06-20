# app/core/config.py

class AlgorithmSettings:
    """
    Constantes de configuración para el algoritmo del indicador.
    Estos valores están definidos en el código para mantener la simplicidad
    en la base de datos, pero se pueden modificar aquí.
    """
    # PARÁMETROS DE FILTROS
    ADX_PERIOD: int = 14
    ADX_THRESHOLD: float = 20.0
    
    EMA_TREND_PERIOD: int = 15
    TREND_FILTER_MODE: str = "ADX-Gated EMA (Hybrid)" # Opciones: "Disabled", "Strict EMA", "ADX-Gated EMA (Hybrid)"

    NO_DOJI_THRESHOLD: float = 0.5
    SYMMETRY_MIN_MAX_RATIO: float = 0.4
    WICK_FILTER_ACTIVE: bool = True
    
    COOLDOWN_BARS: int = 5

# Creamos una instancia para usarla fácilmente en todo el bot
algorithm_settings = AlgorithmSettings()