"""
nodo_central.py - Nodo Central del Sistema Ubicuo
===================================================
Es el cerebro del sistema. Realiza tres tareas en paralelo:

  1. MONITOREO PERIODICO
     Cada INTERVALO_POLLING_SEG segundos consulta a los nodos sensores,
     verifica umbrales y detecta si algun nodo dejo de responder.

  2. BOT DE TELEGRAM
     Escucha comandos del usuario via Telegram y envia alertas automaticas.

  3. MENU DE CONSOLA
     Permite enviar comandos manualmente desde la terminal.

COMANDOS DE TELEGRAM:
  /estado           - Ver temperatura, movimiento y estado de actuadores
  /led1_on          - Encender LED del Nodo 1
  /led1_off         - Apagar LED del Nodo 1
  /motor_on         - Encender motor del Nodo 1
  /motor_off        - Apagar motor del Nodo 1
  /led2_on          - Encender LED del Nodo 2
  /led2_off         - Apagar LED del Nodo 2
  /ayuda            - Ver todos los comandos disponibles

ALERTAS AUTOMATICAS:
  - Temperatura superior a TEMP_MAX_C
  - Temperatura inferior a TEMP_MIN_C
  - Movimiento detectado fuera del horario definido
  - Nodo sin respuesta por MAX_SIN_RESPUESTA ciclos consecutivos

Ejecutar:
  python nodo_central.py

IMPORTANTE: Edita config.py con tu TELEGRAM_TOKEN y TELEGRAM_CHAT_ID.
"""

import json
import sys
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

import config

# ====================================================================
# MODULO TELEGRAM - Comunicacion con la API de Telegram via requests
# ====================================================================

def _llamar_api_telegram(metodo, parametros=None):
    """
    Llama a la API de Telegram usando JSON en el body (mas robusto que urlencode).
    Retorna el JSON de respuesta o None si hay error.
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/{metodo}"
    try:
        if parametros:
            data = json.dumps(parametros).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except Exception as e:
        msg = str(e)
        if "409" in msg:
            time.sleep(3)   # otra instancia activa, esperar que libere
        else:
            print(f"  [Telegram ERROR] {metodo}: {e}")
        return None


def enviar_mensaje_telegram(texto):
    """
    Envia un mensaje de texto al chat configurado en config.py.
    Imprime el texto en consola aunque Telegram falle.
    """
    print(f"\n  [TELEGRAM -> TU] {texto}\n")

    if config.TELEGRAM_TOKEN == "TU_TOKEN_AQUI":
        return   # Telegram no configurado, solo consola

    resultado = _llamar_api_telegram("sendMessage", {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text":    texto,
    })
    if resultado and not resultado.get("ok"):
        print(f"  [Telegram] Error al enviar: {resultado}")


def obtener_actualizaciones_telegram(offset=0):
    """
    Obtiene nuevos mensajes/comandos del bot usando long polling.
    'offset' evita recibir el mismo mensaje dos veces.
    """
    resultado = _llamar_api_telegram("getUpdates", {
        "offset":  offset,
        "timeout": 5,
    })
    if resultado and resultado.get("ok"):
        return resultado.get("result", [])
    return []


# ====================================================================
# MODULO HTTP - Comunicacion con los nodos sensores
# ====================================================================

def consultar_nodo(url_nodo, nombre_nodo, timeout=None):
    """
    Hace GET /datos al nodo especificado.
    Retorna el diccionario de datos o None si no responde.
    """
    t = timeout or config.TIMEOUT_NODO_SEG
    try:
        req = urllib.request.Request(f"{url_nodo}/datos")
        with urllib.request.urlopen(req, timeout=t) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def enviar_comando(url_nodo, nombre_nodo, comando):
    """
    Hace POST /comando al nodo especificado con el comando dado.
    Retorna el diccionario de respuesta o None si falla.
    """
    try:
        cuerpo = json.dumps({"comando": comando}).encode("utf-8")
        req = urllib.request.Request(
            f"{url_nodo}/comando",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=config.TIMEOUT_NODO_SEG) as resp:
            resultado = json.loads(resp.read().decode("utf-8"))
            print(f"  [{nombre_nodo}] Comando '{comando}' -> {resultado.get('mensaje','OK')}")
            return resultado
    except Exception as e:
        print(f"  [{nombre_nodo}] ERROR enviando '{comando}': {e}")
        return None


# ====================================================================
# LOGICA DE ALERTAS
# ====================================================================

# Registro de cuantas veces seguidas fallo cada nodo
_fallos_consecutivos = {"nodo_1": 0, "nodo_2": 0}
# Guarda si ya se envio la alerta de temperatura para no repetir
_alerta_temp_enviada = {"alta": False, "baja": False}


def verificar_temperatura(datos_nodo1):
    """
    Verifica si la temperatura supera o esta por debajo de los umbrales.
    Envia alerta por Telegram solo la primera vez (no spam).
    """
    temp = datos_nodo1.get("temperatura")
    if temp is None:
        return

    if temp > config.TEMP_MAX_C and not _alerta_temp_enviada["alta"]:
        msg = (f"ALERTA TEMPERATURA ALTA\n"
               f"Temperatura: {temp}°C\n"
               f"Umbral maximo: {config.TEMP_MAX_C}°C\n"
               f"Hora: {datetime.now().strftime('%H:%M:%S')}")
        enviar_mensaje_telegram(msg)
        _alerta_temp_enviada["alta"] = True

    elif temp <= config.TEMP_MAX_C:
        _alerta_temp_enviada["alta"] = False   # Resetear alerta

    if temp < config.TEMP_MIN_C and not _alerta_temp_enviada["baja"]:
        msg = (f"ALERTA TEMPERATURA BAJA\n"
               f"Temperatura: {temp}°C\n"
               f"Umbral minimo: {config.TEMP_MIN_C}°C\n"
               f"Hora: {datetime.now().strftime('%H:%M:%S')}")
        enviar_mensaje_telegram(msg)
        _alerta_temp_enviada["baja"] = True

    elif temp >= config.TEMP_MIN_C:
        _alerta_temp_enviada["baja"] = False


def verificar_movimiento(datos_nodo2):
    """
    Verifica si hay movimiento detectado fuera del horario permitido.
    """
    if not datos_nodo2.get("movimiento"):
        return

    hora = datetime.now().hour
    inicio = config.HORA_ALERTA_INICIO
    fin    = config.HORA_ALERTA_FIN

    # El rango nocturno puede cruzar la medianoche (ej: 22 a 6)
    fuera_de_horario = (hora >= inicio) or (hora < fin)

    if fuera_de_horario:
        msg = (f"ALERTA MOVIMIENTO NOCTURNO\n"
               f"Movimiento detectado a las {datetime.now().strftime('%H:%M:%S')}\n"
               f"Horario de alerta: {inicio:02d}:00 - {fin:02d}:00\n"
               f"Presencia detectada: {datos_nodo2.get('presencia', '?')} objeto(s)")
        enviar_mensaje_telegram(msg)


def verificar_nodo_caido(nombre_clave, nombre_display):
    """
    Registra un fallo de comunicacion con un nodo.
    Envia alerta si supera el maximo de fallos consecutivos.
    """
    _fallos_consecutivos[nombre_clave] += 1
    fallos = _fallos_consecutivos[nombre_clave]

    if fallos == config.MAX_SIN_RESPUESTA:
        msg = (f"ALERTA NODO SIN RESPUESTA\n"
               f"El nodo '{nombre_display}' no responde\n"
               f"Intentos fallidos: {fallos}\n"
               f"Hora: {datetime.now().strftime('%H:%M:%S')}")
        enviar_mensaje_telegram(msg)

    print(f"  [{nombre_display}] Sin respuesta (fallo #{fallos})")


def nodo_recuperado(nombre_clave, nombre_display):
    """Resetea el contador de fallos cuando el nodo vuelve a responder."""
    if _fallos_consecutivos[nombre_clave] > 0:
        print(f"  [{nombre_display}] Conexion restablecida.")
    _fallos_consecutivos[nombre_clave] = 0


# ====================================================================
# HILO DE MONITOREO PERIODICO
# ====================================================================

_ultimo_estado = {}   # Cache del ultimo estado conocido de los nodos


def ciclo_monitoreo():
    """
    Se ejecuta en un hilo separado.
    Cada INTERVALO_POLLING_SEG segundos:
      1. Consulta datos de ambos nodos
      2. Verifica umbrales y genera alertas
      3. Imprime resumen en consola
    """
    global _ultimo_estado
    while True:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{ts}] Ciclo de monitoreo")

        # --- Nodo 1 ---
        datos1 = consultar_nodo(config.NODO_1_URL, "Nodo1")
        if datos1:
            nodo_recuperado("nodo_1", "Nodo1")
            _ultimo_estado["nodo_1"] = datos1
            temp = datos1["temperatura"]
            hum  = datos1["humedad"]
            print(f"  [Nodo1] Temp={temp}°C  Hum={hum}%  "
                  f"LED={'ON' if datos1['led'] else 'OFF'}  "
                  f"Motor={'ON' if datos1['motor'] else 'OFF'}")
            verificar_temperatura(datos1)
        else:
            verificar_nodo_caido("nodo_1", "Nodo1")

        # --- Nodo 2 ---
        datos2 = consultar_nodo(config.NODO_2_URL, "Nodo2")
        if datos2:
            nodo_recuperado("nodo_2", "Nodo2")
            _ultimo_estado["nodo_2"] = datos2
            mov = "SI" if datos2["movimiento"] else "No"
            print(f"  [Nodo2] Movimiento={mov}  "
                  f"Presencia={datos2['presencia']}  "
                  f"LED={'ON' if datos2['led'] else 'OFF'}")
            verificar_movimiento(datos2)
        else:
            verificar_nodo_caido("nodo_2", "Nodo2")

        time.sleep(config.INTERVALO_POLLING_SEG)


# ====================================================================
# HILO DEL BOT DE TELEGRAM
# ====================================================================

def procesar_comando_telegram(texto):
    """
    Interpreta el texto del mensaje de Telegram y ejecuta la accion
    correspondiente. Retorna el texto de respuesta para el usuario.
    """
    cmd = texto.strip().lower()

    # ----- /ayuda -----
    if cmd == "/ayuda":
        return (
            "Comandos disponibles:\n"
            "/estado      - Ver sensores y actuadores\n"
            "/led1_on     - LED Nodo 1 ON\n"
            "/led1_off    - LED Nodo 1 OFF\n"
            "/motor_on    - Motor Nodo 1 ON\n"
            "/motor_off   - Motor Nodo 1 OFF\n"
            "/led2_on     - LED Nodo 2 ON\n"
            "/led2_off    - LED Nodo 2 OFF\n"
            "/ayuda       - Este menu"
        )

    # ----- /estado -----
    elif cmd == "/estado":
        lineas = [f"Estado del sistema [{datetime.now().strftime('%H:%M:%S')}]"]

        d1 = _ultimo_estado.get("nodo_1")
        if d1:
            lineas.append(
                f"\nNodo 1 (Temperatura):\n"
                f"  Temp : {d1['temperatura']}°C\n"
                f"  Hum  : {d1['humedad']}%\n"
                f"  LED  : {'ON' if d1['led'] else 'OFF'}\n"
                f"  Motor: {'ON' if d1['motor'] else 'OFF'}"
            )
        else:
            lineas.append("\nNodo 1: SIN DATOS (nodo caido?)")

        d2 = _ultimo_estado.get("nodo_2")
        if d2:
            lineas.append(
                f"\nNodo 2 (Movimiento):\n"
                f"  Movimiento: {'SI' if d2['movimiento'] else 'No'}\n"
                f"  Presencia : {d2['presencia']} objeto(s)\n"
                f"  LED       : {'ON' if d2['led'] else 'OFF'}"
            )
        else:
            lineas.append("\nNodo 2: SIN DATOS (nodo caido?)")

        return "\n".join(lineas)

    # ----- Comandos de actuadores -----
    mapa_comandos = {
        "/led1_on":   (config.NODO_1_URL, "Nodo1", "LED_ON"),
        "/led1_off":  (config.NODO_1_URL, "Nodo1", "LED_OFF"),
        "/motor_on":  (config.NODO_1_URL, "Nodo1", "MOTOR_ON"),
        "/motor_off": (config.NODO_1_URL, "Nodo1", "MOTOR_OFF"),
        "/led2_on":   (config.NODO_2_URL, "Nodo2", "LED_ON"),
        "/led2_off":  (config.NODO_2_URL, "Nodo2", "LED_OFF"),
    }

    if cmd in mapa_comandos:
        url, nombre, comando = mapa_comandos[cmd]
        resultado = enviar_comando(url, nombre, comando)
        if resultado and resultado.get("ok"):
            return f"{nombre}: {resultado['mensaje']}"
        else:
            return f"Error al enviar '{comando}' a {nombre}."

    return f"Comando no reconocido: '{texto}'\nEscribe /ayuda para ver los disponibles."


def ciclo_bot_telegram():
    """
    Se ejecuta en un hilo separado.
    Hace long polling a la API de Telegram para recibir mensajes
    y responde a cada comando del usuario.
    """
    if config.TELEGRAM_TOKEN == "TU_TOKEN_AQUI":
        print("  [Telegram] Token no configurado. Bot desactivado.")
        print("  [Telegram] Edita config.py con tu token real.")
        return

    # Saltar mensajes viejos: obtener el ultimo update_id antes de arrancar
    pendientes = obtener_actualizaciones_telegram(offset=0)
    if pendientes:
        offset = pendientes[-1]["update_id"] + 1
        print(f"  [Telegram] Saltando {len(pendientes)} mensaje(s) previo(s).")
    else:
        offset = 0

    print("  [Telegram] Bot activo. Esperando comandos...")

    while True:
        try:
            actualizaciones = obtener_actualizaciones_telegram(offset)
            for update in actualizaciones:
                offset = update["update_id"] + 1
                mensaje = update.get("message", {})
                texto   = mensaje.get("text", "")
                chat_id = str(mensaje.get("chat", {}).get("id", ""))

                if not texto or not chat_id:
                    continue

                print(f"  [Telegram] Recibido de {chat_id}: {texto}")
                respuesta = procesar_comando_telegram(texto)

                # Responder sin parse_mode para evitar errores con caracteres especiales
                resultado = _llamar_api_telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text":    respuesta,
                })
                if resultado and resultado.get("ok"):
                    print(f"  [Telegram] Respuesta enviada OK")
                else:
                    print(f"  [Telegram] Error enviando respuesta: {resultado}")

        except Exception as e:
            print(f"  [Telegram] Error en ciclo: {e}")
            time.sleep(3)


# ====================================================================
# MENU DE CONSOLA (hilo principal)
# ====================================================================

MENU = """
============================================================
  NODO CENTRAL - Sistema de Computacion Ubicua
============================================================
  [1] Ver estado de los nodos
  [2] Enviar comando a Nodo 1
  [3] Enviar comando a Nodo 2
  [4] Enviar mensaje de prueba a Telegram
  [5] Ver umbrales configurados
  [0] Salir
------------------------------------------------------------
"""

COMANDOS_NODO1 = ["LED_ON", "LED_OFF", "MOTOR_ON", "MOTOR_OFF"]
COMANDOS_NODO2 = ["LED_ON", "LED_OFF"]


def mostrar_estado():
    """Imprime el ultimo estado conocido de ambos nodos."""
    print("\n--- Estado actual ---")
    d1 = _ultimo_estado.get("nodo_1")
    if d1:
        print(f"  Nodo 1 | Temp: {d1['temperatura']}°C  Hum: {d1['humedad']}%  "
              f"LED: {'ON' if d1['led'] else 'OFF'}  Motor: {'ON' if d1['motor'] else 'OFF'}")
    else:
        print("  Nodo 1 | Sin datos (nodo no disponible)")

    d2 = _ultimo_estado.get("nodo_2")
    if d2:
        mov = "SI" if d2["movimiento"] else "No"
        print(f"  Nodo 2 | Movimiento: {mov}  Presencia: {d2['presencia']}  "
              f"LED: {'ON' if d2['led'] else 'OFF'}")
    else:
        print("  Nodo 2 | Sin datos (nodo no disponible)")
    print()


def seleccionar_comando(comandos_disponibles):
    """Muestra lista de comandos y pide seleccion al usuario."""
    print("\n  Comandos disponibles:")
    for i, cmd in enumerate(comandos_disponibles, 1):
        print(f"    [{i}] {cmd}")
    try:
        idx = int(input("  Selecciona numero de comando: ")) - 1
        if 0 <= idx < len(comandos_disponibles):
            return comandos_disponibles[idx]
    except ValueError:
        pass
    print("  Seleccion invalida.")
    return None


def menu_consola():
    """Bucle principal del menu interactivo en consola."""
    print(MENU)
    while True:
        try:
            opcion = input("Opcion: ").strip()

            if opcion == "1":
                mostrar_estado()

            elif opcion == "2":
                cmd = seleccionar_comando(COMANDOS_NODO1)
                if cmd:
                    enviar_comando(config.NODO_1_URL, "Nodo1", cmd)

            elif opcion == "3":
                cmd = seleccionar_comando(COMANDOS_NODO2)
                if cmd:
                    enviar_comando(config.NODO_2_URL, "Nodo2", cmd)

            elif opcion == "4":
                enviar_mensaje_telegram(
                    f"Prueba de conectividad desde el Nodo Central\n"
                    f"Hora: {datetime.now().strftime('%H:%M:%S')}"
                )

            elif opcion == "5":
                print(f"\n  Umbral temperatura maxima : {config.TEMP_MAX_C}°C")
                print(f"  Umbral temperatura minima : {config.TEMP_MIN_C}°C")
                print(f"  Alerta movimiento nocturno: "
                      f"{config.HORA_ALERTA_INICIO:02d}:00 - {config.HORA_ALERTA_FIN:02d}:00")
                print(f"  Max fallos antes de alerta: {config.MAX_SIN_RESPUESTA}\n")

            elif opcion == "0":
                print("Cerrando Nodo Central...")
                sys.exit(0)

            else:
                print("  Opcion no valida. Escribe 0-5.")

        except KeyboardInterrupt:
            print("\nCerrando Nodo Central...")
            sys.exit(0)
        except Exception as e:
            print(f"  Error: {e}")


# ====================================================================
# INICIO DEL SISTEMA
# ====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  NODO CENTRAL - Sistema de Computacion Ubicua")
    print("=" * 60)
    print(f"  Nodo 1: {config.NODO_1_URL}")
    print(f"  Nodo 2: {config.NODO_2_URL}")
    print(f"  Intervalo de monitoreo: {config.INTERVALO_POLLING_SEG}s")
    print(f"  Telegram: {'CONFIGURADO' if config.TELEGRAM_TOKEN != 'TU_TOKEN_AQUI' else 'NO CONFIGURADO (edita config.py)'}")
    print("=" * 60)

    # Hilo 1: Monitoreo periodico de nodos
    hilo_monitoreo = threading.Thread(target=ciclo_monitoreo, daemon=True)
    hilo_monitoreo.start()

    # Hilo 2: Bot de Telegram
    hilo_telegram = threading.Thread(target=ciclo_bot_telegram, daemon=True)
    hilo_telegram.start()

    # Hilo principal: Menu de consola (bloquea hasta que el usuario salga)
    time.sleep(1)   # Dar tiempo a los hilos para inicializar
    print(MENU)
    menu_consola()
