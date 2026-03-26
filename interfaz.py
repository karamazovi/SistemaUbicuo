"""
interfaz.py - Panel de Control con Streamlit
=============================================
Muestra el estado de los sensores y actuadores en tiempo real
y permite enviar comandos a los nodos con un clic.

Ejecutar (con los nodos ya corriendo):
    cd "c:\\Users\\josem\\Desktop\\CursoTecnologias emergentes\\SistemaUbicuo"
    streamlit run interfaz.py
"""

import json
import time
import urllib.request
import streamlit as st

import config

# ===== CONFIGURACION =====
st.set_page_config(
    page_title="Sistema Ubicuo - Panel de Control",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== FUNCIONES DE COMUNICACION =====

def consultar_nodo(url):
    try:
        req = urllib.request.Request(f"{url}/datos")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def enviar_comando(url, comando):
    try:
        data = json.dumps({"comando": comando}).encode("utf-8")
        req = urllib.request.Request(
            f"{url}/comando", data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ===== INTERFAZ =====

st.title("Sistema de Computacion Ubicua")
st.caption("Panel de control en tiempo real — se actualiza cada 3 segundos")
st.divider()

# Consultar datos de ambos nodos
datos1 = consultar_nodo(config.NODO_1_URL)
datos2 = consultar_nodo(config.NODO_2_URL)

# ===== FILA DE ESTADO GENERAL =====
col_n1, col_n2 = st.columns(2)

# ---------- NODO 1 ----------
with col_n1:
    if datos1:
        st.subheader("Nodo 1 — Temperatura / LED / Motor")

        # Indicador de conexion
        st.success("Conectado")

        # Metricas de sensores
        m1, m2 = st.columns(2)
        m1.metric("Temperatura", f"{datos1['temperatura']} °C")
        m2.metric("Humedad", f"{datos1['humedad']} %")

        st.divider()

        # --- LED Nodo 1 ---
        st.markdown("**LED**")
        led1_on = datos1["led"]
        color_led1 = "🟢" if led1_on else "⚫"
        st.markdown(f"### {color_led1}  {'ENCENDIDO' if led1_on else 'APAGADO'}")

        b1, b2 = st.columns(2)
        if b1.button("Encender LED", key="led1_on", use_container_width=True):
            enviar_comando(config.NODO_1_URL, "LED_ON")
            st.rerun()
        if b2.button("Apagar LED", key="led1_off", use_container_width=True):
            enviar_comando(config.NODO_1_URL, "LED_OFF")
            st.rerun()

        st.divider()

        # --- Motor Nodo 1 ---
        st.markdown("**Motor**")
        motor_on = datos1["motor"]
        color_motor = "🔵" if motor_on else "⚫"
        st.markdown(f"### {color_motor}  {'ENCENDIDO' if motor_on else 'APAGADO'}")

        b3, b4 = st.columns(2)
        if b3.button("Encender Motor", key="motor_on", use_container_width=True):
            enviar_comando(config.NODO_1_URL, "MOTOR_ON")
            st.rerun()
        if b4.button("Apagar Motor", key="motor_off", use_container_width=True):
            enviar_comando(config.NODO_1_URL, "MOTOR_OFF")
            st.rerun()

    else:
        st.subheader("Nodo 1 — Temperatura / LED / Motor")
        st.error("Sin conexion — asegurate de correr nodo_sensor_1.py")

# ---------- NODO 2 ----------
with col_n2:
    if datos2:
        st.subheader("Nodo 2 — Movimiento / LED")

        st.success("Conectado")

        # Metricas de sensores
        m3, m4 = st.columns(2)
        mov = datos2["movimiento"]
        m3.metric("Movimiento", "SI" if mov else "No")
        m4.metric("Presencia", f"{datos2['presencia']} objeto(s)")

        st.divider()

        # --- LED Nodo 2 ---
        st.markdown("**LED de alerta**")
        led2_on = datos2["led"]
        color_led2 = "🟡" if led2_on else "⚫"
        st.markdown(f"### {color_led2}  {'ENCENDIDO' if led2_on else 'APAGADO'}")

        b5, b6 = st.columns(2)
        if b5.button("Encender LED", key="led2_on", use_container_width=True):
            enviar_comando(config.NODO_2_URL, "LED_ON")
            st.rerun()
        if b6.button("Apagar LED", key="led2_off", use_container_width=True):
            enviar_comando(config.NODO_2_URL, "LED_OFF")
            st.rerun()

        st.divider()

        # Alerta visual si hay movimiento
        if mov:
            st.warning(f"Movimiento detectado — {datos2['total_detecciones']} detecciones en total")
        else:
            st.info(f"Sin movimiento — {datos2['total_detecciones']} detecciones acumuladas")

    else:
        st.subheader("Nodo 2 — Movimiento / LED")
        st.error("Sin conexion — asegurate de correr nodo_sensor_2.py")

# ===== PIE DE PAGINA =====
st.divider()
ts = time.strftime("%H:%M:%S")
st.caption(f"Ultima actualizacion: {ts}")

# Auto-refresh cada 3 segundos
time.sleep(3)
st.rerun()
