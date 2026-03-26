"""
config.py - Configuracion global del Sistema Ubicuo
====================================================
Edita este archivo antes de ejecutar el sistema.

PASOS PARA OBTENER TU TOKEN DE TELEGRAM:
1. Abre Telegram y busca @BotFather
2. Escribe /newbot y sigue las instrucciones
3. Copia el token que te da (formato: 123456789:AABBccdd...)
4. Para obtener tu CHAT_ID:
   - Envia un mensaje a tu bot
   - Visita: https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   - Busca el campo "id" dentro de "chat"
"""

# ===== TELEGRAM =====
# Los secretos se cargan desde secretos.py (no está en git)
try:
    import secretos
    TELEGRAM_TOKEN   = secretos.TELEGRAM_TOKEN
    TELEGRAM_CHAT_ID = secretos.TELEGRAM_CHAT_ID
except ImportError:
    raise SystemExit(
        "ERROR: Falta el archivo secretos.py\n"
        "Copia secretos.example.py como secretos.py y completa tus valores."
    )

# ===== NODOS SENSORES =====
NODO_1_URL = "http://localhost:5001"      # Temperatura + LED + Motor
NODO_2_URL = "http://localhost:5002"      # Movimiento + LED

# ===== UMBRALES DE ALERTA =====
TEMP_MAX_C  = 30.0   # Alerta si temperatura SUPERA este valor (°C)
TEMP_MIN_C  = 15.0   # Alerta si temperatura es INFERIOR a este valor (°C)

# ===== HORARIO DE MONITOREO DE MOVIMIENTO =====
# Alerta si se detecta movimiento fuera del horario laboral
HORA_ALERTA_INICIO = 22   # 10:00 PM
HORA_ALERTA_FIN    = 6    # 6:00 AM

# ===== TIEMPOS =====
INTERVALO_POLLING_SEG = 5   # Cada cuantos segundos el central consulta los nodos
TIMEOUT_NODO_SEG      = 3   # Segundos de espera maxima por respuesta de un nodo
MAX_SIN_RESPUESTA     = 3   # Alertar si un nodo falla N veces seguidas

# ===== COMANDOS VALIDOS =====
COMANDOS_VALIDOS = ["LED_ON", "LED_OFF", "MOTOR_ON", "MOTOR_OFF"]
