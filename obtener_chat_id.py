"""
obtener_chat_id.py
==================
Ejecuta este script DESPUES de enviarle un mensaje a tu bot en Telegram.
Te muestra el Chat ID que debes poner en config.py

Pasos:
  1. Abre Telegram y busca tu bot (el username que le diste en BotFather)
  2. Enviole cualquier mensaje, por ejemplo: hola
  3. Corre este script:
       python obtener_chat_id.py
  4. Copia el numero que aparece y pegalo en config.py como TELEGRAM_CHAT_ID
"""

import json
import urllib.request
import config

URL = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"

print("Consultando mensajes del bot...")
print()

try:
    with urllib.request.urlopen(URL, timeout=10) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"Error al contactar Telegram: {e}")
    print("Verifica que TELEGRAM_TOKEN en config.py sea correcto.")
    input("\nPresiona Enter para salir...")
    exit(1)

if not datos.get("ok"):
    print("Respuesta inesperada de Telegram:", datos)
    input("\nPresiona Enter para salir...")
    exit(1)

mensajes = datos.get("result", [])

if not mensajes:
    print("=" * 50)
    print("  No hay mensajes nuevos.")
    print("=" * 50)
    print()
    print("Haz lo siguiente:")
    print("  1. Abre Telegram")
    print("  2. Busca tu bot y enviale un mensaje (cualquier texto)")
    print("  3. Vuelve a correr este script")
    input("\nPresiona Enter para salir...")
    exit(0)

print("=" * 50)
print("  Mensajes encontrados:")
print("=" * 50)

for update in mensajes:
    msg = update.get("message", {})
    chat = msg.get("chat", {})
    chat_id   = chat.get("id", "?")
    nombre    = chat.get("first_name", "") + " " + chat.get("last_name", "")
    username  = chat.get("username", "sin username")
    texto     = msg.get("text", "(sin texto)")
    print(f"  Nombre  : {nombre.strip()}")
    print(f"  Username: @{username}")
    print(f"  Chat ID : {chat_id}   <-- este es el que necesitas")
    print(f"  Mensaje : {texto}")
    print()

print("=" * 50)
ultimo_id = mensajes[-1]["message"]["chat"]["id"]
print(f"  Pon este valor en config.py:")
print(f'  TELEGRAM_CHAT_ID = "{ultimo_id}"')
print("=" * 50)
input("\nPresiona Enter para salir...")
