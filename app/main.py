from fastapi import FastAPI

# Crea una instancia de la aplicación FastAPI
app = FastAPI(
    title="TradingBot-95g-API",
    description="El backend para el bot de trading autónomo de la estrategia Pattern 1x1 BO.",
    version="1.0.0"
)

# Define el endpoint raíz (la página de inicio de la API)
@app.get("/")
def read_root():
    """
    Endpoint de bienvenida para verificar que la API está viva.
    """
    return {"message": "TradingBot-95g-API está en funcionamiento."}

# Aquí añadiremos más endpoints en el futuro (ej: /config, /status, etc.)