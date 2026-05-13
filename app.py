import streamlit as st
from groq import Groq
import time
import sqlite3
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PWA (MODO APP) ---
st.set_page_config(
    page_title="Luz App",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# --- 2. BASE DE DATOS ---
def inicializar_db():
    conn = sqlite3.connect('memoria_luz.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY, rol TEXT, contenido TEXT)')
    c.execute(
        'CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, titulo TEXT, fecha TEXT, completado INTEGER)')
    conn.commit()
    return conn


conn = inicializar_db()

# --- 3. ESTILO VISUAL MÓVIL ---
st.markdown("""
    <style>
    /* Estética de App Nativa */
    :root { color-scheme: dark; }
    .stApp { background: #0f172a; }

    /* Ocultar elementos de web */
    header, footer, [data-testid="stDecoration"] { display: none !important; }

    /* Contenedor de la App */
    .block-container { padding: 1rem !important; max-width: 500px !important; }

    .titulo-luz { 
        font-size: 2.5rem !important; 
        font-weight: 800; 
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    /* Botones Flotantes */
    .stButton>button {
        border-radius: 25px;
        height: 3.5rem;
        font-weight: 600;
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
    }

    /* Burbujas de Chat estilo WhatsApp/Telegram */
    [data-testid="stChatMessageAssistant"] { background: #1e293b !important; border-radius: 18px 18px 18px 2px !important; }
    [data-testid="stChatMessageUser"] { background: #38bdf8 !important; border-radius: 18px 18px 2px 18px !important; }
    [data-testid="stChatMessageUser"] p { color: #0f172a !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)


# --- 4. LÓGICA DE EXTRACCIÓN DE EVENTOS (IA) ---
def extraer_evento_ia(texto):
    """Luz analiza si el usuario mencionó un compromiso futuro"""
    client_extra = Groq(api_key=st.session_state.api_key)
    prompt_extract = f"""
    Analiza este texto: "{texto}". 
    Si el usuario menciona un evento futuro (examen, cita, viaje, reunión), devuelve un JSON con:
    {{"evento": "nombre corto", "fecha": "YYYY-MM-DD"}}. 
    Si no hay evento o no dice fecha clara, devuelve "None". 
    Hoy es {datetime.now().date()}.
    """
    try:
        res = client_extra.chat.completions.create(model="llama-3.1-8b-instant",
                                                   messages=[{"role": "user", "content": prompt_extract}])
        content = res.choices[0].message.content
        if "{" in content:
            data = json.loads(content[content.find("{"):content.find("}") + 1])
            c = conn.cursor()
            c.execute("INSERT INTO eventos (titulo, fecha, completado) VALUES (?, ?, 0)",
                      (data['evento'], data['fecha']))
            conn.commit()
            return data['evento']
    except:
        return None


# --- 5. LÓGICA DE RESPIRACIÓN ---
def ejercicio_respiracion():
    ph = st.empty()
    if st.button("❌ Parar"): st.session_state.respirando = False; st.rerun()

    for _ in range(2):
        for i, (t, c, m) in enumerate([(4, "#38bdf8", "Inhala"), (7, "#818cf8", "Mantén"), (8, "#4ade80", "Exhala")]):
            for s in range(t):
                size = 150 + (s * 15) if i == 0 else (300 - (s * 15) if i == 2 else 210)
                ph.markdown(
                    f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:400px;"><div style="width:{size}px;height:{size}px;background:{c};border-radius:50%;box-shadow:0 0 40px {c};transition:all 0.8s;"></div><h2 style="color:{c};margin-top:20px;">{m}... {s + 1}</h2></div>',
                    unsafe_allow_html=True)
                time.sleep(1)
    st.session_state.respirando = False;
    st.rerun()


# --- 6. INICIO DE SESIÓN Y CHAT ---
if "api_key" not in st.session_state: st.session_state.api_key = "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"
if "messages" not in st.session_state: st.session_state.messages = []
if "respirando" not in st.session_state: st.session_state.respirando = False

client = Groq(api_key=st.session_state.api_key)
nombre = st.session_state.get("nombre", "colega")

# --- INTERFAZ ---
if st.session_state.respirando:
    ejercicio_respiracion()
else:
    st.markdown('<h1 class="titulo-luz">🌱 Luz</h1>', unsafe_allow_html=True)

    # Barra de herramientas rápida
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🧘 Respirar"): st.session_state.respirando = True; st.rerun()
    with col_b:
        with st.popover("👤 Perfil"):
            n = st.text_input("Tu nombre", nombre)
            if st.button("Guardar"): st.session_state.nombre = n; st.rerun()

    # Mostrar eventos detectados automáticamente
    c = conn.cursor()
    c.execute("SELECT id, titulo FROM eventos WHERE completado = 0")
    evs = c.fetchall()
    if evs:
        with st.expander("📌 Mis recordatorios"):
            for id_e, tit in evs:
                if st.button(f"Hecho: {tit}", key=f"ev_{id_e}"):
                    c.execute("UPDATE eventos SET completado = 1 WHERE id = ?", (id_e,))
                    conn.commit();
                    st.rerun()

    st.markdown("---")

    # Chat
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Cuéntame, tío..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 1. Intentar extraer evento automáticamente
        evento_detectado = extraer_evento_ia(prompt)
        if evento_detectado: st.toast(f"Vale, me apunto lo de '{evento_detectado}'")

        # 2. Respuesta de Luz
        with st.chat_message("assistant"):
            c.execute("SELECT titulo, fecha FROM eventos WHERE completado = 0")
            pendientes = [f"{e[0]} el {e[1]}" for e in c.fetchall()]

            sys = f"Eres Luz, colega de {nombre} en España. Habla natural (tío, guay, tela). Sabes esto: {pendientes}. Pregunta por ello si viene al caso. Sé breve."
            res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "system",
                                                                                          "content": sys}] + st.session_state.messages)
            msg = res.choices[0].message.content
            st.markdown(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})