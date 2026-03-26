"""
nodo_sensor_2.py - Nodo Sensor 2
==================================
Simula un nodo IoT con:
  - Sensor PIR de MOVIMIENTO (True/False)
  - Sensor de PRESENCIA (contador de objetos detectados)
  - Actuador LED (estado: ON / OFF)

Servidor HTTP escuchando en el puerto 5002.
El nodo central se comunica con este nodo via HTTP.

ENDPOINTS:
  GET  /datos      -> Retorna JSON con movimiento, presencia y estado del LED
  POST /comando    -> Recibe un comando y modifica el estado del LED
                      Body JSON: {"comando": "LED_ON"}

COMANDOS ACEPTADOS:
  LED_ON   - Enciende el LED de alerta
  LED_OFF  - Apaga el LED de alerta

Ejecutar:
  python nodo_sensor_2.py
"""

import json
import random
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ===== ESTADO GLOBAL DEL NODO =====
estado = {
    "led": False,    # LED de alerta: False = apagado, True = encendido
}

# Contador acumulado de detecciones de movimiento en la sesion
_detecciones_movimiento = 0
_bloqueo = threading.Lock()


# ===== SIMULACION DE SENSORES =====

def leer_movimiento():
    """
    Simula la lectura de un sensor PIR (Passive Infrared).
    Retorna True si detecta movimiento, False si no.
    La probabilidad de deteccion cambia segun la hora del dia
    para simular mayor actividad durante el dia.
    """
    global _detecciones_movimiento
    hora_actual = datetime.now().hour

    # Mayor probabilidad de movimiento en horario diurno
    if 8 <= hora_actual <= 18:
        probabilidad = 0.25   # 25% durante el dia
    else:
        probabilidad = 0.10   # 10% en horario nocturno (para disparar alertas)

    detectado = random.random() < probabilidad
    if detectado:
        with _bloqueo:
            _detecciones_movimiento += 1
    return detectado


def leer_presencia():
    """
    Simula un sensor de presencia (contador de personas/objetos).
    Retorna el numero de objetos detectados en el campo de vision.
    """
    return random.randint(0, 3)


# ===== MANEJADOR HTTP =====

class ManejadorNodo2(BaseHTTPRequestHandler):
    """
    Manejador de peticiones HTTP para el Nodo Sensor 2.
    """

    def log_message(self, format, *args):
        pass   # Silenciar logs automaticos

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
            # Leer sensores FUERA del lock (leer_movimiento adquiere _bloqueo internamente)
            movimiento = leer_movimiento()
            presencia  = leer_presencia()
            with _bloqueo:
                respuesta  = {
                    "nodo":                  "sensor_2",
                    "timestamp":             datetime.now().isoformat(),
                    "movimiento":            movimiento,
                    "presencia":             presencia,
                    "total_detecciones":     _detecciones_movimiento,
                    "led":                   estado["led"],
                }
            estado_mov = "MOVIMIENTO DETECTADO" if movimiento else "Sin movimiento"
            print(f"  [GET /datos] {estado_mov}  Presencia={presencia}  "
                  f"LED={'ON' if estado['led'] else 'OFF'}")
            self._responder_json(200, respuesta)
        else:
            self._responder_json(404, {"error": "Ruta no encontrada"})

    # ---- POST /comando ----
    def do_POST(self):
        if self.path == "/comando":
            longitud = int(self.headers.get("Content-Length", 0))
            cuerpo_raw = self.rfile.read(longitud)

            try:
                cuerpo  = json.loads(cuerpo_raw.decode("utf-8"))
                comando = cuerpo.get("comando", "").upper().strip()
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._responder_json(400, {"error": "JSON invalido"})
                return

            with _bloqueo:
                if comando == "LED_ON":
                    estado["led"] = True
                    mensaje = "LED de alerta encendido"
                elif comando == "LED_OFF":
                    estado["led"] = False
                    mensaje = "LED de alerta apagado"
                elif comando in ("MOTOR_ON", "MOTOR_OFF"):
                    # Este nodo no tiene motor; respondemos con aviso
                    self._responder_json(400, {
                        "error": f"Nodo 2 no tiene motor. Comando ignorado: {comando}"
                    })
                    return
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
    PUERTO = 5002
    servidor = HTTPServer(("0.0.0.0", PUERTO), ManejadorNodo2)

    print("=" * 55)
    print("  NODO SENSOR 2 - Movimiento / Presencia / LED")
    print("=" * 55)
    print(f"  Escuchando en http://localhost:{PUERTO}")
    print(f"  Endpoints disponibles:")
    print(f"    GET  http://localhost:{PUERTO}/datos")
    print(f"    POST http://localhost:{PUERTO}/comando")
    print(f"  Comandos: LED_ON | LED_OFF")
    print(f"  Presiona Ctrl+C para detener.")
    print("=" * 55)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nNodo Sensor 2 detenido.")
        servidor.server_close()
