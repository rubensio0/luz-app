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


# --- 2. BASE DE DATOS ROBUSTA ---
def inicializar_db():
    conn = sqlite3.connect('memoria_luz.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY, rol TEXT, contenido TEXT, fecha TEXT)')
    c.execute(
        'CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, titulo TEXT, fecha TEXT, completado INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS humor (id INTEGER PRIMARY KEY, puntuacion INTEGER, fecha TEXT)')

    # Parche por si la tabla historial es antigua
    try:
        c.execute('ALTER TABLE historial ADD COLUMN fecha TEXT')
    except:
        pass
    conn.commit()
    return conn


conn = inicializar_db()

# --- 3. DISEÑO "VISTOSO" Y ARREGLO DE UX (TABLÉTS/MÓVIL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');

    /* Bloquear el "Pull-to-refresh" y mejorar scroll */
    html, body {
        overscroll-behavior-y: contain; /* Esto evita que se recargue al tirar hacia arriba */
        background-color: #0f172a;
    }

    [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: linear-gradient(-45deg, #0f172a, #1e293b, #111827);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    /* Forzar que TODO el texto sea legible (Blanco puro) */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #FFFFFF !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.5);
    }

    /* Ocultar elementos de Streamlit */
    header, footer, [data-testid="stDecoration"] { display: none !important; }

    /* Contenedor principal con padding para que no se pegue a los bordes */
    .block-container { 
        padding: 1rem !important; 
        max-width: 550px !important; 
    }

    /* Cabecera FIJA (Sticky) para que los botones no se escapen */
    .stHeader {
        position: fixed;
        top: 0;
        z-index: 999;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(10px);
        width: 100%;
        padding: 10px 0;
    }

    /* Título */
    .titulo-luz {
        font-size: 3.5rem !important;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 1rem;
    }

    /* Burbujas de Chat con alto contraste */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
    }

    [data-testid="stChatMessageUser"] {
        background: #0ea5e9 !important; /* Azul sólido para máximo contraste */
    }

    [data-testid="stChatMessageUser"] p {
        color: #FFFFFF !important;
        font-weight: 600;
    }

    /* Botones estilo App Premium */
    .stButton>button {
        border-radius: 12px !important;
        background: #1e293b !important;
        color: #FFFFFF !important;
        border: 1px solid #38bdf8 !important;
        font-weight: 600 !important;
        height: 3rem;
    }

    /* Animación fondo */
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
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
    st.markdown("<h2 style='text-align:center;'>Inhala y exhala con Luz</h2>", unsafe_allow_html=True)
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
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:450px;">
                        <div style="width:{size}px; height:{size}px; background:{color}; border-radius:50%; box-shadow: 0 0 80px {color};"></div>
                        <h1 style="margin-top:40px; color:white; font-size:3rem;">{accion}</h1>
                        <p style="font-size:1.5rem; color:white;">{s + 1}</p>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
    st.session_state.respirando = False
    st.rerun()

else:
    # CABECERA VISUAL
    st.markdown('<h1 class="titulo-luz">Luz</h1>', unsafe_allow_html=True)

    # MENÚ ACCIONES
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
                st.write("Sin datos.")
    with col3:
        with st.popover("👤"):
            c = conn.cursor()
            c.execute("SELECT nombre FROM usuarios WHERE id=1")
            res_n = c.fetchone()
            nombre_actual = res_n[0] if res_n else "Usuario"
            nuevo_n = st.text_input("Tu nombre", nombre_actual)
            if st.button("Guardar"):
                c.execute("INSERT OR REPLACE INTO usuarios (id, nombre) VALUES (1, ?)", (nuevo_n,))
                conn.commit()
                st.rerun()

    # RETOS
    c = conn.cursor()
    c.execute("SELECT id, titulo, fecha FROM eventos WHERE completado = 0")
    evs = c.fetchall()
    if evs:
        with st.expander(f"🔔 Tienes {len(evs)} recordatorios"):
            for ide, tit, fec in evs:
                col_e1, col_e2 = st.columns([3, 1])
                col_e1.write(f"**{tit}**")
                if col_e2.button("✓", key=f"ch_{ide}"):
                    c.execute("UPDATE eventos SET completado = 1 WHERE id = ?", (ide,))
                    conn.commit()
                    st.rerun()

    st.markdown("---")

    # CHAT
    if "messages" not in st.session_state:
        c.execute("SELECT rol, contenido FROM historial ORDER BY id DESC LIMIT 15")
        st.session_state.messages = [{"role": r, "content": c} for r, c in reversed(c.fetchall())]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("¿Qué tal va todo?"):
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
            Eres Luz, colega de {nombre_actual}. 
            Vives en España. Habla natural y de tú (tío, guay, tela).
            Sabes que le preocupa: {pendientes}.
            Responde muy corto (máx 2 frases). Sé empático.
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