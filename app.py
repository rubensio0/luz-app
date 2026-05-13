import streamlit as st
from groq import Groq
import time
import sqlite3
import json
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE ESCENA ---
st.set_page_config(
    page_title="Luz",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# --- 2. BASE DE DATOS ---
def inicializar_db():
    conn = sqlite3.connect('memoria_luz.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY, rol TEXT, contenido TEXT, fecha TEXT)')
    c.execute(
        'CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, titulo TEXT, fecha TEXT, completado INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS humor (id INTEGER PRIMARY KEY, puntuacion INTEGER, fecha TEXT)')
    try:
        c.execute('ALTER TABLE historial ADD COLUMN fecha TEXT')
    except:
        pass
    conn.commit()
    return conn


conn = inicializar_db()

# --- 3. DISEÑO "ANTI-RECARGA" Y MÁXIMO CONTRASTE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');

    /* BLOQUEO DE RECARGA (PULL-TO-REFRESH) */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        overscroll-behavior: none !important;
        position: fixed;
        overflow: hidden;
        width: 100%;
        height: 100%;
    }

    /* Permitir scroll solo en el contenedor de la app */
    .main .block-container {
        overflow-y: auto;
        height: 100vh;
        overscroll-behavior-y: contain;
    }

    /* FONDO Y TEXTO */
    [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: #0f172a !important; /* Fondo sólido muy oscuro para evitar líos de contraste */
        color: #FFFFFF !important;
    }

    /* Forzar visibilidad de letras */
    p, span, h1, h2, h3, label, .stMarkdown {
        color: #FFFFFF !important;
        font-weight: 500;
    }

    /* Título con brillo */
    .titulo-luz {
        font-size: 3.5rem !important;
        font-weight: 800;
        color: #38bdf8 !important;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0px 0px 15px rgba(56, 189, 248, 0.5);
    }

    /* Burbujas de Chat */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }

    [data-testid="stChatMessageUser"] {
        background: #0284c7 !important;
    }

    /* Botones Pro */
    .stButton>button {
        background: #1e293b !important;
        color: white !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }

    header, footer, [data-testid="stDecoration"] { display: none !important; }
    </style>

    <script>
    // SCRIPT PARA BLOQUEAR EL GESTO DE RECARGA EN TABLETS
    var lastY = 0;
    document.addEventListener('touchstart', function(e) {
        lastY = e.touches[0].clientY;
    }, {passive: false});

    document.addEventListener('touchmove', function(e) {
        var top = window.pageYOffset || document.documentElement.scrollTop;
        var y = e.touches[0].clientY;
        if (top === 0 && y > lastY) {
            e.preventDefault(); // Bloquea el tirón hacia abajo
        }
        lastY = y;
    }, {passive: false});
    </script>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ Falta API KEY en Secrets.")
    st.stop()

# --- 5. INTERFAZ ---

if "respirando" not in st.session_state: st.session_state.respirando = False

if st.session_state.respirando:
    st.markdown("<h1 style='text-align:center;'>Respira...</h1>", unsafe_allow_html=True)
    ph = st.empty()
    if st.button("Terminar"):
        st.session_state.respirando = False
        st.rerun()

    for _ in range(2):
        for accion, segs, color in [("Inhala", 4, "#38bdf8"), ("Mantén", 7, "#818cf8"), ("Exhala", 8, "#4ade80")]:
            for s in range(segs):
                ph.markdown(
                    f"<div style='display:flex; justify-content:center; align-items:center; height:300px;'><div style='width:200px; height:200px; background:{color}; border-radius:50%; box-shadow: 0 0 50px {color}; display:flex; align-items:center; justify-content:center;'><h2>{s + 1}</h2></div></div><h2 style='text-align:center; color:{color};'>{accion}</h2>",
                    unsafe_allow_html=True)
                time.sleep(1)
    st.session_state.respirando = False
    st.rerun()

else:
    st.markdown('<h1 class="titulo-luz">Luz</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧘 Zen"):
            st.session_state.respirando = True
            st.rerun()
    with col2:
        with st.popover("📈"):
            df = pd.read_sql_query("SELECT puntuacion, fecha FROM humor ORDER BY id DESC LIMIT 10", conn)
            if not df.empty: st.line_chart(df.set_index('fecha'))
    with col3:
        with st.popover("👤"):
            c = conn.cursor();
            c.execute("SELECT nombre FROM usuarios WHERE id=1")
            res_n = c.fetchone();
            nombre_actual = res_n[0] if res_n else "Colega"
            nuevo_n = st.text_input("Nombre", nombre_actual)
            if st.button("Ok"):
                c.execute("INSERT OR REPLACE INTO usuarios (id, nombre) VALUES (1, ?)", (nuevo_n,))
                conn.commit();
                st.rerun()

    # EVENTOS
    c = conn.cursor();
    c.execute("SELECT id, titulo FROM eventos WHERE completado = 0")
    evs = c.fetchall()
    if evs:
        with st.expander("🔔 Recordatorios"):
            for ide, tit in evs:
                if st.button(f"Hecho: {tit}", key=f"e_{ide}"):
                    c.execute("UPDATE eventos SET completado = 1 WHERE id = ?", (ide,))
                    conn.commit();
                    st.rerun()

    st.markdown("---")

    # CHAT
    if "messages" not in st.session_state:
        c.execute("SELECT rol, contenido FROM historial ORDER BY id DESC LIMIT 15")
        st.session_state.messages = [{"role": r, "content": con} for r, con in reversed(c.fetchall())]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        c.execute("INSERT INTO historial (rol, contenido, fecha) VALUES (?, ?, ?)",
                  ("user", prompt, datetime.now().strftime("%Y-%m-%d")))

        # Inteligencia proactiva
        with st.chat_message("assistant"):
            sys_prompt = f"Eres Luz, colega de {nombre_actual}. Vives en España. Habla natural. Responde muy corto (1-2 frases)."
            response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "system",
                                                                                               "content": sys_prompt}] + st.session_state.messages)
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            c.execute("INSERT INTO historial (rol, contenido, fecha) VALUES (?, ?, ?)",
                      ("assistant", ans, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()