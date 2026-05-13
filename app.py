import streamlit as st
from groq import Groq
import time
import sqlite3
import json
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE ESCENA (MODO APP PROFESIONAL) ---
st.set_page_config(
    page_title="Luz - Bienestar Inteligente",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# --- 2. BASE DE DATOS ROBUSTA ---
def inicializar_db():
    conn = sqlite3.connect('memoria_luz.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY, rol TEXT, contenido TEXT, fecha TEXT)')
    c.execute(
        'CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, titulo TEXT, fecha TEXT, completado INTEGER)')
    # Nueva tabla para métricas de humor
    c.execute('CREATE TABLE IF NOT EXISTS humor (id INTEGER PRIMARY KEY, puntuacion INTEGER, fecha TEXT)')
    conn.commit()
    return conn


conn = inicializar_db()

# --- 3. DISEÑO UI PREMIUM (GLASSMORPHISM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'SF Pro Display', -apple-system, sans-serif;
        background: #0f172a !important;
        color: #f8fafc;
    }

    /* Ocultar elementos de Streamlit */
    header, footer, [data-testid="stDecoration"] { display: none !important; }
    .block-container { padding-top: 2rem !important; max-width: 550px !important; }

    /* Título con Neón */
    .titulo-luz {
        font-size: 3rem !important;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 10px 20px rgba(56, 189, 248, 0.2);
    }

    /* Tarjetas de Eventos */
    .evento-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }

    /* Chat Bubbles */
    [data-testid="stChatMessageAssistant"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px 20px 20px 5px !important;
    }
    [data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%) !important;
        border-radius: 20px 20px 5px 20px !important;
    }
    [data-testid="stChatMessageUser"] p { color: #0f172a !important; font-weight: 600; }

    /* Botones Estilo iOS */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5rem;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #38bdf8 !important;
        background: rgba(56, 189, 248, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE INTELIGENCIA ---

# Cliente de IA (Usando Secrets para profesionalidad)
# Si no usas Secrets, pon tu clave aquí: client = Groq(api_key="TU_CLAVE")
try:
    client = Groq(api_key="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")
except:
    st.error("⚠️ Configura la GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()


def analizar_y_guardar_evento(texto):
    prompt = f"Analiza: '{texto}'. Si hay un evento futuro (cita, examen, etc), responde SOLO un JSON: {{\"titulo\": \"...\", \"fecha\": \"YYYY-MM-DD\"}}. Si no, responde 'None'."
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


# --- 5. INTERFAZ Y NAVEGACIÓN ---

if "respirando" not in st.session_state: st.session_state.respirando = False

if st.session_state.respirando:
    # --- MODO ZEN ---
    st.markdown("<h2 style='text-align:center;'>Respira con Luz</h2>", unsafe_allow_html=True)
    placeholder = st.empty()
    if st.button("Finalizar"):
        st.session_state.respirando = False
        st.rerun()

    for _ in range(2):  # 2 ciclos
        for accion, segs, color, m in [("Inhala", 4, "#38bdf8", 1), ("Mantén", 7, "#818cf8", 0),
                                       ("Exhala", 8, "#4ade80", -1)]:
            for s in range(segs):
                size = 150 + (s * 20 if m == 1 else (-s * 20 if m == -1 else 80))
                placeholder.markdown(f"""
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:350px;">
                        <div style="width:{size}px; height:{size}px; background:{color}; border-radius:50%; box-shadow: 0 0 50px {color}; transition: all 0.9s ease;"></div>
                        <h1 style="margin-top:30px; color:{color};">{accion}... {s + 1}</h1>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
    st.session_state.respirando = False
    st.rerun()

else:
    # --- MODO APP ---
    st.markdown('<h1 class="titulo-luz">🌱 Luz</h1>', unsafe_allow_html=True)

    # Menú de acciones rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧘 Zen"):
            st.session_state.respirando = True
            st.rerun()
    with col2:
        with st.popover("📊 Progreso"):
            df = pd.read_sql_query("SELECT puntuacion, fecha FROM humor ORDER BY id DESC LIMIT 7", conn)
            if not df.empty:
                st.line_chart(df.set_index('fecha'))
                st.caption("Tu evolución de ánimo (últimos 7 registros)")
            else:
                st.write("Aún no tengo datos suficientes.")
    with col3:
        with st.popover("👤 Perfil"):
            c = conn.cursor()
            c.execute("SELECT nombre FROM usuarios WHERE id=1")
            res_n = c.fetchone()
            nombre_actual = res_n[0] if res_n else "Usuario"
            nuevo_n = st.text_input("¿Cómo te llamas?", nombre_actual)
            if st.button("Guardar"):
                c.execute("INSERT OR REPLACE INTO usuarios (id, nombre) VALUES (1, ?)", (nuevo_n,))
                conn.commit()
                st.rerun()

    # Gestión de eventos proactivos
    c = conn.cursor()
    c.execute("SELECT id, titulo, fecha FROM eventos WHERE completado = 0")
    evs = c.fetchall()
    if evs:
        with st.expander(f"📌 Tienes {len(evs)} retos próximos", expanded=False):
            for ide, tit, fec in evs:
                col_e1, col_e2 = st.columns([3, 1])
                col_e1.write(f"**{tit}** ({fec})")
                if col_e2.button("Done", key=f"check_{ide}"):
                    c.execute("UPDATE eventos SET completado = 1 WHERE id = ?", (ide,))
                    conn.commit()
                    st.rerun()

    st.divider()

    # Chat
    if "messages" not in st.session_state:
        c.execute("SELECT rol, contenido FROM historial ORDER BY id DESC LIMIT 10")
        st.session_state.messages = [{"role": r, "content": c} for r, c in reversed(c.fetchall())]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Dime qué pasa, tío..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Guardar en DB historial
        c.execute("INSERT INTO historial (rol, contenido, fecha) VALUES (?, ?, ?)",
                  ("user", prompt, datetime.now().strftime("%Y-%m-%d")))

        # Inteligencia en segundo plano
        evento_ok = analizar_y_guardar_evento(prompt)
        registrar_humor(prompt)
        if evento_ok: st.toast(f"Anotado: {evento_ok}")

        # Respuesta de Luz
        with st.chat_message("assistant"):
            c.execute("SELECT titulo FROM eventos WHERE completado=0")
            pendientes = [r[0] for r in c.fetchall()]

            sys_prompt = f"""
            Eres Luz, el mejor colega de {nombre_actual}. Vives en España. 
            Eres empático, directo y usas lenguaje coloquial (tío, vaya tela, guay).
            Sabes que tiene pendiente: {pendientes}.
            No eres un robot, eres un amigo que da consejos reales. Breve (máx 2 frases).
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