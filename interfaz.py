"""
interfaz.py - Panel de Control con Streamlit
=============================================
Muestra el estado de los sensores y actuadores en tiempo real
y permite enviar comandos a los nodos con un clic.

Ejecutar (con los nodos ya corriendo):
    cd "c:\\Users\\josem\\Desktop\\CursoTecnologias emergentes\\SistemaUbicuo"
    streamlit run interfaz.py
"""

import json           # para convertir la respuesta HTTP (texto) a diccionario Python
import time           # para sleep (pausa antes del auto-refresh) y strftime (hora actual)
import urllib.request # para hacer peticiones HTTP a los nodos sin pip install
import streamlit as st # libreria que convierte codigo Python en una pagina web interactiva

import config         # URLs de los nodos, umbrales y configuracion global

# ===== CONFIGURACION DE LA PAGINA =====
st.set_page_config(
    page_title="Sistema Ubicuo - Panel de Control",  # titulo en la pestana del navegador
    layout="wide",                                    # usa todo el ancho de la pantalla
    initial_sidebar_state="collapsed",               # oculta la barra lateral al inicio
)

# ===== FUNCIONES DE COMUNICACION =====

def consultar_nodo(url):
    """
    Hace GET /datos al nodo en la URL indicada.
    Retorna un diccionario con los datos del nodo, o None si no responde.
    """
    try:
        req = urllib.request.Request(f"{url}/datos")  # construye la peticion GET a /datos
        with urllib.request.urlopen(req, timeout=3) as resp:  # espera max 3 segundos
            return json.loads(resp.read().decode("utf-8"))     # convierte JSON a dict
    except Exception:
        return None   # si el nodo no responde o hay error, retorna None


def enviar_comando(url, comando):
    """
    Hace POST /comando al nodo en la URL indicada.
    Envia el comando como JSON en el body: {"comando": "LED_ON"}.
    Retorna la respuesta del nodo, o None si falla.
    """
    try:
        data = json.dumps({"comando": comando}).encode("utf-8")  # serializa el comando a bytes JSON
        req = urllib.request.Request(
            f"{url}/comando", data=data,                          # POST a /comando con body
            headers={"Content-Type": "application/json"}          # indica que el body es JSON
        )
        with urllib.request.urlopen(req, timeout=3) as resp:      # espera max 3 segundos
            return json.loads(resp.read().decode("utf-8"))         # retorna la respuesta del nodo
    except Exception:
        return None   # si el nodo no responde o hay error, retorna None


# ===== INTERFAZ =====

st.title("Sistema de Computacion Ubicua")                              # titulo principal de la pagina
st.caption("Panel de control en tiempo real — se actualiza cada 3 segundos")  # subtitulo
st.divider()                                                           # linea horizontal separadora

# Consultar datos de ambos nodos antes de dibujar la interfaz
datos1 = consultar_nodo(config.NODO_1_URL)   # dict con temp, humedad, led, motor — o None
datos2 = consultar_nodo(config.NODO_2_URL)   # dict con movimiento, presencia, led  — o None

# ===== FILA DE ESTADO GENERAL =====
col_n1, col_n2 = st.columns(2)   # divide la pantalla en 2 columnas iguales

# ---------- NODO 1 ----------
with col_n1:                      # todo lo que este aqui adentro se dibuja en la columna izquierda
    if datos1:                    # si el nodo respondio (datos1 no es None)
        st.subheader("Nodo 1 — Temperatura / LED / Motor")

        st.success("Conectado")   # caja verde que indica conexion exitosa

        # Metricas de sensores — se muestran como tarjetas con el valor grande
        m1, m2 = st.columns(2)                                    # dos sub-columnas para las metricas
        m1.metric("Temperatura", f"{datos1['temperatura']} °C")   # tarjeta de temperatura
        m2.metric("Humedad",     f"{datos1['humedad']} %")         # tarjeta de humedad

        st.divider()   # separador visual entre sensores y actuadores

        # --- LED Nodo 1 ---
        st.markdown("**LED**")                          # texto en negrita como etiqueta
        led1_on    = datos1["led"]                      # True si el LED esta encendido
        color_led1 = "🟢" if led1_on else "⚫"          # circulo verde = ON, negro = OFF
        st.markdown(f"### {color_led1}  {'ENCENDIDO' if led1_on else 'APAGADO'}")  # indicador visual grande

        b1, b2 = st.columns(2)   # dos botones lado a lado
        if b1.button("Encender LED", key="led1_on", use_container_width=True):   # boton izquierdo
            enviar_comando(config.NODO_1_URL, "LED_ON")   # envia LED_ON al nodo 1
            st.rerun()                                     # recarga la pagina para reflejar el cambio
        if b2.button("Apagar LED", key="led1_off", use_container_width=True):    # boton derecho
            enviar_comando(config.NODO_1_URL, "LED_OFF")  # envia LED_OFF al nodo 1
            st.rerun()                                     # recarga la pagina

        st.divider()   # separador entre LED y Motor

        # --- Motor Nodo 1 ---
        st.markdown("**Motor**")                         # etiqueta
        motor_on    = datos1["motor"]                    # True si el motor esta encendido
        color_motor = "🔵" if motor_on else "⚫"         # circulo azul = ON, negro = OFF
        st.markdown(f"### {color_motor}  {'ENCENDIDO' if motor_on else 'APAGADO'}")  # indicador visual

        b3, b4 = st.columns(2)   # dos botones lado a lado
        if b3.button("Encender Motor", key="motor_on", use_container_width=True):    # boton izquierdo
            enviar_comando(config.NODO_1_URL, "MOTOR_ON")   # envia MOTOR_ON al nodo 1
            st.rerun()                                        # recarga la pagina
        if b4.button("Apagar Motor", key="motor_off", use_container_width=True):     # boton derecho
            enviar_comando(config.NODO_1_URL, "MOTOR_OFF")   # envia MOTOR_OFF al nodo 1
            st.rerun()                                        # recarga la pagina

    else:   # si datos1 es None (el nodo no respondio)
        st.subheader("Nodo 1 — Temperatura / LED / Motor")
        st.error("Sin conexion — asegurate de correr nodo_sensor_1.py")   # caja roja de error

# ---------- NODO 2 ----------
with col_n2:                   # todo lo que este aqui adentro se dibuja en la columna derecha
    if datos2:                 # si el nodo respondio (datos2 no es None)
        st.subheader("Nodo 2 — Movimiento / LED")

        st.success("Conectado")   # caja verde de conexion exitosa

        # Metricas de sensores
        m3, m4 = st.columns(2)                                              # dos sub-columnas
        mov = datos2["movimiento"]                                          # True/False segun sensor PIR
        m3.metric("Movimiento", "SI" if mov else "No")                      # tarjeta de movimiento
        m4.metric("Presencia",  f"{datos2['presencia']} objeto(s)")         # tarjeta de presencia

        st.divider()   # separador

        # --- LED Nodo 2 ---
        st.markdown("**LED de alerta**")               # etiqueta
        led2_on    = datos2["led"]                     # True si el LED de alerta esta encendido
        color_led2 = "🟡" if led2_on else "⚫"         # circulo amarillo = ON, negro = OFF
        st.markdown(f"### {color_led2}  {'ENCENDIDO' if led2_on else 'APAGADO'}")  # indicador visual

        b5, b6 = st.columns(2)   # dos botones lado a lado
        if b5.button("Encender LED", key="led2_on", use_container_width=True):    # boton izquierdo
            enviar_comando(config.NODO_2_URL, "LED_ON")   # envia LED_ON al nodo 2
            st.rerun()                                     # recarga la pagina
        if b6.button("Apagar LED", key="led2_off", use_container_width=True):     # boton derecho
            enviar_comando(config.NODO_2_URL, "LED_OFF")  # envia LED_OFF al nodo 2
            st.rerun()                                     # recarga la pagina

        st.divider()   # separador

        # Alerta visual segun si hay movimiento activo o no
        if mov:   # movimiento detectado en esta lectura
            st.warning(f"Movimiento detectado — {datos2['total_detecciones']} detecciones en total")
        else:     # sin movimiento
            st.info(f"Sin movimiento — {datos2['total_detecciones']} detecciones acumuladas")

    else:   # si datos2 es None (el nodo no respondio)
        st.subheader("Nodo 2 — Movimiento / LED")
        st.error("Sin conexion — asegurate de correr nodo_sensor_2.py")   # caja roja de error

# ===== PIE DE PAGINA =====
st.divider()                                        # linea separadora al fondo
ts = time.strftime("%H:%M:%S")                      # hora actual en formato HH:MM:SS
st.caption(f"Ultima actualizacion: {ts}")           # muestra la hora de la ultima carga

# Auto-refresh: pausa 3 segundos y luego vuelve a ejecutar todo el script desde cero
time.sleep(3)   # espera 3 segundos antes de recargar
st.rerun()      # fuerza a Streamlit a re-ejecutar el script completo (equivale a F5 automatico)
