"""
nodo_sensor_1.py - Nodo Sensor 1
==================================
Simula un nodo IoT con:
  - Sensor de TEMPERATURA y HUMEDAD (valores simulados)
  - Actuador LED  (estado: ON / OFF)
  - Actuador MOTOR (estado: ON / OFF)

Servidor HTTP escuchando en el puerto 5001.
El nodo central se comunica con este nodo via HTTP.

ENDPOINTS:
  GET  /datos      -> Retorna JSON con temperatura, humedad y estado de actuadores
  POST /comando    -> Recibe un comando y modifica el estado de un actuador
                      Body JSON: {"comando": "LED_ON"}

COMANDOS ACEPTADOS:
  LED_ON    - Enciende el LED
  LED_OFF   - Apaga el LED
  MOTOR_ON  - Enciende el motor
  MOTOR_OFF - Apaga el motor

Ejecutar:
  python nodo_sensor_1.py
"""

import json
import random
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ===== ESTADO GLOBAL DEL NODO =====
# Estos diccionarios representan el estado fisico del nodo en todo momento
estado = {
    "led":   False,    # False = apagado, True = encendido
    "motor": False,    # False = apagado, True = encendido
}

# Sensor de temperatura: valor base que fluctua ligeramente con el tiempo
_temperatura_base = 22.0
_bloqueo = threading.Lock()   # Evita condiciones de carrera entre hilos


# ===== SIMULACION DE SENSORES =====

def leer_temperatura():
    """
    Simula la lectura de un sensor de temperatura DHT22 o similar.
    El valor oscila alrededor de _temperatura_base con ruido aleatorio.
    Ocasionalmente genera un pico (simula sol directo, calefactor, etc.)
    """
    global _temperatura_base
    # Fluctuacion lenta del ambiente
    _temperatura_base += random.uniform(-0.3, 0.3)
    _temperatura_base = max(10.0, min(45.0, _temperatura_base))

    # Pico esporadico para disparar alertas durante la demo
    if random.random() < 0.05:   # 5% de probabilidad
        return round(_temperatura_base + random.uniform(10, 15), 1)

    return round(_temperatura_base + random.uniform(-0.5, 0.5), 1)


def leer_humedad():
    """Simula la lectura de humedad relativa (%)."""
    return round(random.uniform(40.0, 80.0), 1)


# ===== MANEJADOR HTTP =====

class ManejadorNodo1(BaseHTTPRequestHandler):
    """
    Manejador de peticiones HTTP para el Nodo Sensor 1.
    Hereda de BaseHTTPRequestHandler de la libreria estandar de Python.
    """

    # Silenciar los logs de acceso en la consola (los reemplazamos con los nuestros)
    def log_message(self, format, *args):
        pass

    def _responder_json(self, codigo_http, datos):
        """Metodo auxiliar para enviar una respuesta JSON."""
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo_http)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(cuerpo))
        self.end_headers()
        self.wfile.write(cuerpo)

    # ---- GET /datos ----
    def do_GET(self):
        if self.path == "/datos":
            with _bloqueo:
                temp = leer_temperatura()
                hum  = leer_humedad()
                respuesta = {
                    "nodo":        "sensor_1",
                    "timestamp":   datetime.now().isoformat(),
                    "temperatura": temp,
                    "humedad":     hum,
                    "led":         estado["led"],
                    "motor":       estado["motor"],
                }
            print(f"  [GET /datos] Temp={temp}°C  Hum={hum}%  "
                  f"LED={'ON' if estado['led'] else 'OFF'}  "
                  f"MOTOR={'ON' if estado['motor'] else 'OFF'}")
            self._responder_json(200, respuesta)
        else:
            self._responder_json(404, {"error": "Ruta no encontrada"})

    # ---- POST /comando ----
    def do_POST(self):
        if self.path == "/comando":
            # Leer el cuerpo de la peticion
            longitud = int(self.headers.get("Content-Length", 0))
            cuerpo_raw = self.rfile.read(longitud)

            try:
                cuerpo = json.loads(cuerpo_raw.decode("utf-8"))
                comando = cuerpo.get("comando", "").upper().strip()
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._responder_json(400, {"error": "JSON invalido"})
                return

            # Procesar el comando
            with _bloqueo:
                if comando == "LED_ON":
                    estado["led"] = True
                    mensaje = "LED encendido"
                elif comando == "LED_OFF":
                    estado["led"] = False
                    mensaje = "LED apagado"
                elif comando == "MOTOR_ON":
                    estado["motor"] = True
                    mensaje = "Motor encendido"
                elif comando == "MOTOR_OFF":
                    estado["motor"] = False
                    mensaje = "Motor apagado"
                else:
                    self._responder_json(400, {"error": f"Comando desconocido: {comando}"})
                    return

            ts = datetime.now().strftime("%H:%M:%S")
            print(f"  [POST /comando] [{ts}] Comando recibido: {comando} -> {mensaje}")
            self._responder_json(200, {
                "ok":      True,
                "comando": comando,
                "mensaje": mensaje,
                "estado":  estado.copy(),
            })
        else:
            self._responder_json(404, {"error": "Ruta no encontrada"})


# ===== INICIO DEL SERVIDOR =====

if __name__ == "__main__":
    PUERTO = 5001
    servidor = HTTPServer(("0.0.0.0", PUERTO), ManejadorNodo1)

    print("=" * 55)
    print("  NODO SENSOR 1 - Temperatura / LED / Motor")
    print("=" * 55)
    print(f"  Escuchando en http://localhost:{PUERTO}")
    print(f"  Endpoints disponibles:")
    print(f"    GET  http://localhost:{PUERTO}/datos")
    print(f"    POST http://localhost:{PUERTO}/comando")
    print(f"  Comandos: LED_ON | LED_OFF | MOTOR_ON | MOTOR_OFF")
    print(f"  Presiona Ctrl+C para detener.")
    print("=" * 55)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nNodo Sensor 1 detenido.")
        servidor.server_close()
