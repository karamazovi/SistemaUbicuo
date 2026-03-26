"""
obtener_chat_id.py
==================
Obtiene tu Chat ID de Telegram usando solo el token del bot.

Pasos:
  1. Corre este script:
       python obtener_chat_id.py
  2. Cuando veas "Esperando mensaje...", abre Telegram y escribele
     cualquier cosa a tu bot (por ejemplo: hola)
  3. El script muestra tu Chat ID automaticamente
  4. Copia el numero y pegalo en secretos.py como TELEGRAM_CHAT_ID
"""

import json
import time
import urllib.request
import config

BASE = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"


def get_updates(offset=None, timeout=20):
    url = f"{BASE}/getUpdates?timeout={timeout}"
    if offset is not None:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout + 5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Verificar que el token es valido
print("Verificando token...")
resp = get_updates(timeout=1)
if not resp.get("ok"):
    print()
    print("ERROR: No se pudo conectar con Telegram.")
    print("Verifica que TELEGRAM_TOKEN en secretos.py sea correcto.")
    print(f"Detalle: {resp.get('error', resp)}")
    input("\nPresiona Enter para salir...")
    exit(1)

# Calcular offset para ignorar mensajes viejos
updates = resp.get("result", [])
offset = (updates[-1]["update_id"] + 1) if updates else 0

print("Token valido.")
print()
print("=" * 50)
print("  Esperando mensaje en Telegram...")
print("  Escribele cualquier cosa a tu bot ahora.")
print("=" * 50)

# Esperar el proximo mensaje nuevo
while True:
    resp = get_updates(offset=offset, timeout=20)
    if not resp.get("ok"):
        print(f"Error de red, reintentando... ({resp.get('error', '')})")
        time.sleep(2)
        continue

    for update in resp.get("result", []):
        offset = update["update_id"] + 1
        msg    = update.get("message", {})
        chat   = msg.get("chat", {})

        if not chat:
            continue

        chat_id  = chat.get("id")
        nombre   = (chat.get("first_name", "") + " " + chat.get("last_name", "")).strip()
        username = chat.get("username", "sin username")
        texto    = msg.get("text", "(sin texto)")

        print()
        print("  Mensaje recibido!")
        print(f"  Nombre  : {nombre}")
        print(f"  Username: @{username}")
        print(f"  Mensaje : {texto}")
        print()
        print("=" * 50)
        print(f"  Tu Chat ID es: {chat_id}")
        print()
        print(f"  Ponlo en secretos.py:")
        print(f'  TELEGRAM_CHAT_ID = "{chat_id}"')
        print("=" * 50)
        exit(0)
