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
    conn.commit()
    return conn


conn = inicializar_db()

# --- 3. DISEÑO "VISTOSO" (ULTRA-MODERN UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');

    /* Fondo animado y General */
    [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: linear-gradient(-45deg, #0f172a, #1e293b, #111827, #0f172a);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #f1f5f9;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Ocultar basurilla de Streamlit */
    header, footer, [data-testid="stDecoration"] { display: none !important; }
    .block-container { padding-top: 2rem !important; max-width: 500px !important; }

    /* Título Impactante */
    .titulo-luz {
        font-size: 4rem !important;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(to bottom right, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }

    .eslogan {
        text-align: center;
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }

    /* Tarjetas Glassmorphism */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 15px !important;
    }

    /* Mensaje del Usuario */
    [data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.8), rgba(129, 140, 248, 0.8)) !important;
    }

    /* Botones Estilo Cápsula */
    .stButton>button {
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(5px);
        color: white !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .stButton>button:hover {
        transform: scale(1.05);
        border-color: #38bdf8 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
    }

    /* Caja de entrada flotante */
    .stChatInputContainer {
        padding-bottom: 20px !important;
    }
    .stChatInput {
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        background: rgba(15, 23, 42, 0.9) !important;
    }

    /* Ajuste para el expansor de retos */
    .stExpander {
        border-radius: 20px !important;
        border: none !important;
        background: rgba(255, 255, 255, 0.03) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE INTELIGENCIA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ Configura la GROQ_API_KEY en Secrets.")
    st.stop()


def analizar_y_guardar_evento(texto):
    prompt = f"Analiza: '{texto}'. Si hay un evento futuro responde SOLO un JSON: {{\"titulo\": \"...\", \"fecha\": \"YYYY-MM-DD\"}}. Si no, responde 'None'."
    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
    content = res.choices[0].message.content
    if "{" in content:
        try:
            data = json.loads(content[content.find("{"):content.find("}") + 1])
            c = conn.cursor()
            c.execute("INSERT INTO eventos (titulo, fecha, completado) VALUES (?, ?, 0)",
                      (data['titulo'], data['fecha']))
            conn.commit()
            return data['titulo']
        except:
            return None
    return None


def registrar_humor(texto):
    prompt = f"Del 1 al 10, ¿cuán positivo es este mensaje? Responde solo el número: '{texto}'"
    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
    try:
        score = int(res.choices[0].message.content.strip())
        c = conn.cursor()
        c.execute("INSERT INTO humor (puntuacion, fecha) VALUES (?, ?)", (score, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    except:
        pass


# --- 5. INTERFAZ ---

if "respirando" not in st.session_state: st.session_state.respirando = False

if st.session_state.respirando:
    # --- MODO ZEN MEJORADO ---
    st.markdown("<h2 style='text-align:center;'>Respira con calma</h2>", unsafe_allow_html=True)
    placeholder = st.empty()
    if st.button("Salir"):
        st.session_state.respirando = False
        st.rerun()

    for _ in range(2):
        for accion, segs, color, m in [("Inhala", 4, "#38bdf8", 1), ("Mantén", 7, "#818cf8", 0),
                                       ("Exhala", 8, "#4ade80", -1)]:
            for s in range(segs):
                size = 180 + (s * 25 if m == 1 else (-s * 25 if m == -1 else 100))
                placeholder.markdown(f"""
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:400px;">
                        <div style="width:{size}px; height:{size}px; background:{color}; border-radius:50%; filter: blur(2px); box-shadow: 0 0 80px {color}; transition: all 0.9s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                        <h1 style="margin-top:40px; color:white; font-weight:800; text-shadow: 0 0 10px {color};">{accion}</h1>
                        <p style="color:white; opacity:0.6;">{s + 1}</p>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
    st.session_state.respirando = False
    st.rerun()

else:
    # CABECERA VISUAL
    st.markdown('<h1 class="titulo-luz">Luz</h1>', unsafe_allow_html=True)
    st.markdown('<p class="eslogan">Tu espacio seguro para charlar y crecer.</p>', unsafe_allow_html=True)

    # ACCIONES RÁPIDAS
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧘 Zen"):
            st.session_state.respirando = True
            st.rerun()
    with col2:
        with st.popover("📈"):
            df = pd.read_sql_query("SELECT puntuacion, fecha FROM humor ORDER BY id DESC LIMIT 10", conn)
            if not df.empty:
                st.line_chart(df.set_index('fecha'))
            else:
                st.write("Escribe algo para ver tu progreso.")
    with col3:
        with st.popover("👤"):
            c = conn.cursor()
            c.execute("SELECT nombre FROM usuarios WHERE id=1")
            res_n = c.fetchone()
            nombre_actual = res_n[0] if res_n else "Usuario"
            nuevo_n = st.text_input("Nombre", nombre_actual)
            if st.button("OK"):
                c.execute("INSERT OR REPLACE INTO usuarios (id, nombre) VALUES (1, ?)", (nuevo_n,))
                conn.commit()
                st.rerun()

    # RETOS INTELIGENTES
    c = conn.cursor()
    c.execute("SELECT id, titulo, fecha FROM eventos WHERE completado = 0")
    evs = c.fetchall()
    if evs:
        with st.expander(f"✨ Tienes {len(evs)} asuntos pendientes"):
            for ide, tit, fec in evs:
                col_e1, col_e2 = st.columns([3, 1])
                col_e1.write(f"**{tit}**")
                if col_e2.button("✓", key=f"check_{ide}"):
                    c.execute("UPDATE eventos SET completado = 1 WHERE id = ?", (ide,))
                    conn.commit()
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # CHAT
    if "messages" not in st.session_state:
        c.execute("SELECT rol, contenido FROM historial ORDER BY id DESC LIMIT 10")
        st.session_state.messages = [{"role": r, "content": c} for r, c in reversed(c.fetchall())]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Dime lo que sea, tío..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        c.execute("INSERT INTO historial (rol, contenido, fecha) VALUES (?, ?, ?)",
                  ("user", prompt, datetime.now().strftime("%Y-%m-%d")))

        analizar_y_guardar_evento(prompt)
        registrar_humor(prompt)

        with st.chat_message("assistant"):
            c.execute("SELECT titulo FROM eventos WHERE completado=0")
            pendientes = [r[0] for r in c.fetchall()]

            sys_prompt = f"""
            Eres Luz, el mejor colega de {nombre_actual}. 
            Vives en España. Habla natural (tío, guay, tela, me mola).
            Tienes acceso a sus eventos: {pendientes}.
            Dile cosas cortas, como un amigo por WhatsApp. Sé empático pero real.
            """

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages,
                temperature=0.8
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            c.execute("INSERT INTO historial (rol, contenido, fecha) VALUES (?, ?, ?)",
                      ("assistant", ans, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()