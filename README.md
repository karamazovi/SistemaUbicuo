# Sistema de Computacion Ubicua
## Evidencia de Aprendizaje - Tecnologias Emergentes

---

## Descripcion del Sistema

Sistema distribuido que simula una red de nodos IoT con comunicacion bidireccional HTTP
y alertas via bot de Telegram.

```
                    +------------------+
                    |  BOT TELEGRAM    |  <- Comandos del usuario
                    +------------------+
                            |
                    +------------------+
                    |  NODO CENTRAL    |  <- nodo_central.py
                    |  localhost       |
                    +------------------+
                       /            \
          HTTP GET/POST            HTTP GET/POST
                     /                \
        +----------------+    +----------------+
        | NODO SENSOR 1  |    | NODO SENSOR 2  |
        | localhost:5001 |    | localhost:5002 |
        | Temperatura    |    | Movimiento     |
        | LED + Motor    |    | LED            |
        +----------------+    +----------------+
```

---

## Archivos del Proyecto

| Archivo | Descripcion |
|---|---|
| `config.py` | Configuracion global (token, URLs, umbrales) |
| `nodo_sensor_1.py` | Servidor HTTP del Nodo 1: temperatura, humedad, LED, motor |
| `nodo_sensor_2.py` | Servidor HTTP del Nodo 2: movimiento, presencia, LED |
| `nodo_central.py` | Nodo central: monitoreo, alertas, bot Telegram, menu consola |

---

## Dependencias

El proyecto usa **solo la libreria estandar de Python** (no requiere pip install):
- `http.server` - Servidor HTTP de los nodos sensores
- `urllib.request` - Llamadas HTTP del nodo central
- `threading` - Ejecucion paralela de hilos
- `json` - Serializacion de datos
- `csv` - (disponible si se necesita log)

```bash
# Solo Python 3.7+ es necesario. Verificar version:
python --version
```

---

## Configuracion del Bot de Telegram

**Paso 1:** Crea un bot con @BotFather en Telegram:
```
/newbot
Nombre: MiSistemaUbicuo
Username: mi_sistema_ubicuo_bot
```

**Paso 2:** Copia el token que te da BotFather (formato: `123456789:AABBccdd...`)

**Paso 3:** Envia un mensaje a tu bot, luego visita:
```
https://api.telegram.org/bot<TU_TOKEN>/getUpdates
```
Busca el campo `"id"` dentro de `"chat"` - ese es tu CHAT_ID.

**Paso 4:** Edita `config.py`:
```python
TELEGRAM_TOKEN   = "123456789:AABBccdd..."
TELEGRAM_CHAT_ID = "987654321"
```

---

## Ejecucion (3 terminales)

**Terminal 1 - Nodo Sensor 1:**
```bash
cd SistemaUbicuo
python nodo_sensor_1.py
```

**Terminal 2 - Nodo Sensor 2:**
```bash
cd SistemaUbicuo
python nodo_sensor_2.py
```

**Terminal 3 - Nodo Central:**
```bash
cd SistemaUbicuo
python nodo_central.py
```

---

## Endpoints HTTP de los Nodos

### Nodo 1 (puerto 5001)

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/datos` | Retorna temperatura, humedad, estado LED y motor |
| POST | `/comando` | Ejecuta LED_ON / LED_OFF / MOTOR_ON / MOTOR_OFF |

Ejemplo GET:
```json
{
  "nodo": "sensor_1",
  "timestamp": "2026-03-26T10:30:00",
  "temperatura": 23.5,
  "humedad": 65.2,
  "led": false,
  "motor": true
}
```

Ejemplo POST (body):
```json
{"comando": "LED_ON"}
```

### Nodo 2 (puerto 5002)

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/datos` | Retorna movimiento, presencia, estado LED |
| POST | `/comando` | Ejecuta LED_ON / LED_OFF |

---

## Tabla de Comandos

| Comando | Nodo | Efecto |
|---|---|---|
| `LED_ON` | 1 y 2 | Enciende el LED |
| `LED_OFF` | 1 y 2 | Apaga el LED |
| `MOTOR_ON` | 1 | Enciende el motor |
| `MOTOR_OFF` | 1 | Apaga el motor |

### Comandos del Bot de Telegram

| Comando | Accion |
|---|---|
| `/estado` | Muestra temperatura, movimiento y estado de actuadores |
| `/led1_on` | Enciende LED del Nodo 1 |
| `/led1_off` | Apaga LED del Nodo 1 |
| `/motor_on` | Enciende motor del Nodo 1 |
| `/motor_off` | Apaga motor del Nodo 1 |
| `/led2_on` | Enciende LED del Nodo 2 |
| `/led2_off` | Apaga LED del Nodo 2 |
| `/ayuda` | Lista todos los comandos |

---

## Umbrales y Logica de Alertas

| Condicion | Umbral | Alerta enviada |
|---|---|---|
| Temperatura alta | > 30.0 °C | "ALERTA TEMPERATURA ALTA" |
| Temperatura baja | < 15.0 °C | "ALERTA TEMPERATURA BAJA" |
| Movimiento nocturno | 22:00 - 06:00 | "ALERTA MOVIMIENTO NOCTURNO" |
| Nodo sin respuesta | 3 fallos seguidos | "ALERTA NODO SIN RESPUESTA" |

Los umbrales se configuran en `config.py`.

---

## Diagrama de Flujo de Alertas

```
Cada 5 segundos:
   |
   +-- Consultar Nodo 1 ----> Responde? --No--> Fallo++ --> >= 3? --> ALERTA NODO CAIDO
   |                                 |
   |                                 Si
   |                                 |
   |                          temp > 30? --> ALERTA TEMP ALTA
   |                          temp < 15? --> ALERTA TEMP BAJA
   |
   +-- Consultar Nodo 2 ----> Responde? --No--> Fallo++ --> >= 3? --> ALERTA NODO CAIDO
                                      |
                                      Si
                                      |
                               movimiento=True AND hora fuera de rango?
                                      |
                                      --> ALERTA MOVIMIENTO NOCTURNO
```
