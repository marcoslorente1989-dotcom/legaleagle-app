import streamlit as st
import os

# ==============================================================================
# 0. PARCHE DE EMERGENCIA PARA WHATSAPP/SEO (Sobrescribe el archivo físico)
# ==============================================================================
try:
    # Buscamos dónde está instalado Streamlit en el servidor de Render
    import streamlit
    p = os.path.dirname(streamlit.__file__)
    f_path = os.path.join(p, "static", "index.html")
    
    # Leemos el archivo original
    with open(f_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Si sigue poniendo "Streamlit", lo cambiamos físicamente por "LegalApp"
    if "<title>Streamlit</title>" in html_content:
        new_content = html_content.replace(
            "<title>Streamlit</title>", 
            "<title>LegalApp AI - Tu Abogado 24h</title>"
        )
        # Añadimos metaetiquetas reales para que WhatsApp las lea sí o sí
        meta_tags = """
        <meta property="og:title" content="LegalApp AI - Tu Abogado 24h">
        <meta property="og:description" content="Tu abogado virtual gratuito. Analiza contratos, calcula impuestos y reclama deudas con IA.">
        <meta property="og:image" content="https://legalapp.es/logo.png">
        """
        new_content = new_content.replace("<head>", f"<head>{meta_tags}")
        
        # Guardamos el archivo hackeado
        with open(f_path, "w", encoding="utf-8") as f:
            f.write(new_content)
except Exception as e:
    print(f"Error parcheando SEO: {e}")

# ==============================================================================
# 1. IMPORTS Y CONFIGURACIÓN
# ==============================================================================
import streamlit.components.v1 as components
import pdfplumber
from groq import Groq
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import json
import gspread
import requests 
from oauth2client.service_account import ServiceAccountCredentials
import re 
from docx import Document # Para generar Word
import urllib.parse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT

st.set_page_config(
    page_title="LegalApp AI - Tu Abogado 24h",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "LegalApp AI"
    }
)

# ... después de st.set_page_config ...

# ANCLA INVISIBLE PARA EL SCROLL MÓVIL
st.markdown("<div id='top-of-page'></div>", unsafe_allow_html=True)

# ... aquí siguen tus claves api_key ...

# Intentar leer de Variable de Entorno (Render) o Secrets (Local)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        from streamlit.runtime.secrets import secrets_singleton
        if secrets_singleton.load_if_present():
            api_key = st.secrets.get("GROQ_API_KEY")
    except: pass

# ==============================================================================
# 2. SCRIPTS Y ESTILOS (SEPARADOS)
# ==============================================================================

# --- A. LÓGICA JAVASCRIPT (SOLO CÓDIGO) ---
st.markdown(
    """
    <script>
        // 1. Icono y Título
        var link = window.parent.document.querySelector("link[rel*='icon']") || window.parent.document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'shortcut icon';
        link.href = 'https://legalapp.es/logo.png';
        window.parent.document.getElementsByTagName('head')[0].appendChild(link);
        window.parent.document.title = "LegalApp AI - Tu Abogado 24h";
        
        // 2. Función para sobreescribir los metadatos (WhatsApp)
        function fixMeta() {
            const metas = window.parent.document.getElementsByTagName('meta');
            for (let i = 0; i < metas.length; i++) {
                if (metas[i].getAttribute('property') === 'og:title' || metas[i].getAttribute('name') === 'title') {
                    metas[i].content = "LegalApp AI - Tu Abogado 24h";
                }
                if (metas[i].getAttribute('property') === 'og:description' || metas[i].getAttribute('name') === 'description') {
                    metas[i].content = "Analiza contratos y genera documentos legales gratis con IA en España.";
                }
            }
        }
        fixMeta();
        setInterval(fixMeta, 500); 
    </script>
    """,
    unsafe_allow_html=True
)

# --- B. ESTILOS CSS (SOLO DISEÑO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    /* 1. ELIMINAR RESALTADO NEGRO/GRIS EN MÓVIL (CRÍTICO) */
    * {
        -webkit-tap-highlight-color: transparent !important;
        -webkit-touch-callout: none !important;
        outline: none !important;
    }
    
    /* 2. SCROLLBAR INVISIBLE */
    ::-webkit-scrollbar { display: none; }
    .stApp { scrollbar-width: none; -ms-overflow-style: none; }

    /* 3. LOGO Y ESPACIOS (AJUSTE FINAL) */
    .block-container {
        padding-top: 0rem !important; 
        margin-top: -4.5rem !important; /* Subida agresiva */
    }

    [data-testid="stImage"] {
        margin-top: 0px !important;
        margin-bottom: -50px !important;
        display: flex;
        justify-content: center;
        transform: scale(0.7); /* Logo un poco más pequeño para móviles */
    }
    
    /* Ocultar header nativo */
    header, [data-testid="stHeader"] { display: none !important; }

    /* 4. UNIFICAR BOTONES (AZULES Y GRANDES) */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        font-weight: bold !important;
        height: 50px !important;
        width: 100% !important;
        transition: 0.2s ease;
    }
    div.stButton > button:hover { transform: scale(1.02) !important; }

    /* 5. ARREGLO PESTAÑAS MÓVIL (2x2) */
    @media only screen and (max-width: 600px) {
        .stApp, .main, .block-container { overflow-x: hidden !important; width: 100vw !important; }
        div[data-baseweb="tab-list"] { 
            display: grid !important; 
            grid-template-columns: 1fr 1fr !important; 
            gap: 10px !important; 
            padding: 10px !important; 
        }
        button[data-baseweb="tab"]:first-child { 
            grid-column: span 2 !important; 
            width: 92% !important; 
            margin: 0 auto 10px auto !important; 
        }
        button[data-baseweb="tab"] {
            border-radius: 25px !important;
            background-color: rgba(255, 255, 255, 0.12) !important;
            font-size: 11px !important;
        }
    }

    /* 6. ESTILOS GENERALES (FONDO Y TEXTO) */
    .stApp { background: linear-gradient(135deg, #1e40af 0%, #0f172a 100%); font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption { color: #ffffff !important; }

    /* Inputs Blancos */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; color: #000000 !important; border-radius: 12px;
    }
    ul[data-baseweb="menu"], div[data-baseweb="popover"] { background-color: #ffffff !important; }
    ul[data-baseweb="menu"] li { color: #000000 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; }

    /* 7. FAQ TRANSPARENTE */
    .stExpander {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    .stExpander details summary p { color: #ffffff !important; }
    .stExpander details summary:hover { background-color: transparent !important; }
    .stExpander details div { color: #ffffff !important; }

    /* 8. CAJA CONTRATO */
    .contract-box {
        font-family: 'Times New Roman', serif; background-color: #ffffff !important; 
        padding: 30px; border-radius: 10px; color: #000000 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .contract-box * { color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# Textos ocultos para SEO/Idioma
st.markdown("""
<div style="display:none; visibility:hidden; height:0;">
    Hola, esto es una aplicación en español de España. Contrato laboral, nómina,
    impuestos, seguridad social, irpf, sueldo neto, bruto, clausulas, legal,
    abogado, leyes, estatuto de los trabajadores, españa, madrid, barcelona.
    No traducir. Idioma español confirmado.
</div>
""", unsafe_allow_html=True)

components.html("""
    <script>
        const doc = window.parent.document;
        doc.documentElement.lang = 'es';
        doc.documentElement.setAttribute('translate', 'no');
        console.log("🦅 App lista en Render (Limpia).");
    </script>
""", height=0)

# ==============================================================================
# 2. ESTILOS CSS (V110: SOLUCIÓN FINAL CANDADO Y COLORES)
# ==============================================================================
st.markdown("""
    <style>
    /* Ocultar menú hamburguesa y footer de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Reducir el espacio blanco excesivo de arriba */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Estilo botón WhatsApp (Verde) */
    .stLinkButton a {
        background-color: #25D366 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    /* 1. Cargamos Font Awesome para el logo de WhatsApp */
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    /* --- NUEVO: OCULTAR LA BARRA DE SCROLL LATERAL --- */
    /* Esto la hace invisible pero permite seguir bajando con el ratón/dedo */
    
    /* Para Chrome, Safari y Edge */
    ::-webkit-scrollbar {
        display: none;
    }
    /* Para Firefox */
    .stApp {
        scrollbar-width: none;
        -ms-overflow-style: none;  /* IE y Edge antiguo */
    }

    /* 1. ELIMINAR ESPACIO SUPERIOR TOTAL */
    .block-container {
        padding-top: 0rem !important; 
        margin-top: -6rem !important; /* Forzamos la subida masiva */
    }

    /* 2. AJUSTE DEL LOGO PARA QUE NO OCUPE ESPACIO VERTICAL */
    [data-testid="stImage"] {
        margin-top: -30px !important;
        margin-bottom: -50px !important; /* Quitamos el espacio que deja debajo */
        display: flex;
        justify-content: center;
        transform: scale(0.8); /* Reducimos un poco el tamaño visual para ganar pantalla */
    }

    /* Ocultar elementos nativos que roban espacio arriba */
    header, [data-testid="stHeader"] {
        display: none !important;
    }
  
    /* 2. PESTAÑAS EN 2x2 PARA MÓVIL */

    @media only screen and (max-width: 600px) {
        
        /* 1. Bloqueo total de movimiento lateral en la raíz y contenedores */
        .stApp, .main, .block-container { 
            overflow-x: hidden !important; 
            width: 100vw !important;
            max-width: 100vw !important;
        }

        /* 2. Contenedor de pestañas: Ajuste de ancho exacto al 100% real */
        div[data-baseweb="tab-list"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
            padding: 10px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            overflow: hidden !important; /* Evita que las pestañas "empujen" hacia afuera */
        }

        /* 3. Botón INICIO: Forzamos limpieza de sombras y bordes */
        button[data-baseweb="tab"]:first-child {
            grid-column: span 2 !important;
            width: 92% !important; 
            margin: 0 auto 10px auto !important;
            border-radius: 30px !important;
            /* Eliminamos la sombra/brillo que causa la mancha negra lateral */
            box-shadow: none !important; 
            outline: none !important;
            -webkit-tap-highlight-color: transparent !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            height: 45px !important;
        }

        /* 4. Botones 2x2: Ovalados y limpios */
        button[data-baseweb="tab"] {
            border-radius: 25px !important;
            padding: 12px 5px !important;
            background-color: rgba(255, 255, 255, 0.12) !important;
            box-shadow: none !important;
            outline: none !important;
            font-size: 11px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }

        /* 5. Ajustes de Logo y Texto de Subida */
        [data-testid="stImage"] img { max-width: 80% !important; }
        
        [data-testid="stFileUploader"] section > div > div::before {
            content: "📂 Pulsa para subir PDF" !important;
            font-size: 14px !important;
        }

        /* 6. Eliminación de márgenes de bloque que provocan desbordamiento */
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0.5rem !important;
        }

        div[data-testid="stVerticalBlock"] > div {
            padding-left: 0px !important;
            padding-right: 0px !important;
        }
    }
    
    /* 1. FONDO GENERAL */
    .stApp { 
        background: linear-gradient(135deg, #1e40af 0%, #0f172a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* 2. TEXTOS GENERALES */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption { color: #ffffff !important; }

    /* 3. --- EL CANDADO (TRANSPARENCIA FORZADA) --- */
    /* Quitamos fondo, borde y sombra al botón del candado */
    button[kind="secondary"] {
         background: transparent !important;
         border: none !important;
         box-shadow: none !important;
    }
    div[data-testid="stPopover"] button {
        background-color: transparent !important;
        border: 0px solid transparent !important;
        color: rgba(255, 255, 255, 0.7) !important;
    }
    /* Al pasar el ratón */
    div[data-testid="stPopover"] button:hover {
        background-color: transparent !important;
        color: #ffffff !important;
        transform: scale(1.1);
    }

    /* 4. --- CONTENIDO DENTRO DEL CANDADO Y LEGAL (LETRAS NEGRAS) --- */
    /* Fondo blanco para los desplegables */
    div[data-testid="stPopoverBody"], div[data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1;
    }
    /* FORZAR COLOR NEGRO en todos los textos dentro de los desplegables */
    div[data-testid="stPopoverBody"] p, div[data-testid="stPopoverBody"] span, 
    div[data-testid="stPopoverBody"] div, div[data-testid="stPopoverBody"] h3,
    div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] span, 
    div[data-testid="stExpanderDetails"] div, div[data-testid="stExpanderDetails"] li {
        color: #000000 !important;
    }

    /* 5. INPUTS (Cajas blancas, letra negra) */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; 
        color: #000000 !important;
        caret-color: #000000;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
    }
    ul[data-baseweb="menu"] { background-color: #ffffff !important; }
    ul[data-baseweb="menu"] li { color: #000000 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; } 

    /* 6. CAJA DE SUBIDA */
    [data-testid="stFileUploader"] section {
        background-color: #f1f5f9 !important;
        border: 2px dashed #cbd5e1; border-radius: 15px; padding: 20px;
    }
    [data-testid="stFileUploader"] section > div > div > span, 
    [data-testid="stFileUploader"] section > div > div > small { display: none !important; }
    [data-testid="stFileUploader"] section > div > div::before {
        content: "📂 Arrastra PDF para analizar";
        display: block; text-align: center; color: #334155 !important; font-weight: 600; margin-bottom: 10px;
    }
    [data-testid="stFileUploader"] button {
        border-radius: 20px !important; border: 1px solid #94a3b8 !important;
        background-color: #e2e8f0 !important; color: transparent !important;
        position: relative; width: 160px; height: 40px; margin: auto; display: block;
    }
    [data-testid="stFileUploader"] button::after {
        content: "📄 Buscar Archivo"; color: #0f172a !important;
        position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
        font-weight: 600; width: 100%; font-size: 14px;
    }

    /* 7. PESTAÑAS */
    div[data-baseweb="tab-list"] { justify-content: center !important; gap: 10px; }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    button[data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important; 
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 30px !important;
        /* CAMBIA ESTA LÍNEA: Quita el 30px y ponlo así para que sea flexible */
        padding: 10px 15px !important; 
        min-width: 100px; /* Asegura un tamaño mínimo pero flexible */
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #3b82f6 !important; font-weight: bold !important; border-color: #60a5fa !important; transform: scale(1.05);
    }

    /* 8. OTROS */
    .contract-box {
        font-family: 'Times New Roman', serif; background-color: #ffffff !important; 
        padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        /* Bloqueo de copia en la previsualización */
        }
    .contract-box {
        -webkit-user-select: none; /* Safari */
        -ms-user-select: none; /* IE/Edge */
        user-select: none; /* Estándar */
        pointer-events: none; /* Evita que el ratón interactúe con el texto */
    }

    .contract-box * { color: #000000 !important; }
    .chat-user { background-color: #bfdbfe; color: #000000 !important; padding: 10px; border-radius: 15px 15px 0 15px; text-align: right; margin-bottom: 5px; }
    .chat-bot { background-color: #ffffff; color: #000000 !important; padding: 10px; border-radius: 15px 15px 15px 0; margin-bottom: 5px; }
  
   /* --- BOTÓN WHATSAPP VERDE PROFESIONAL --- */
    /* --- BOTÓN WHATSAPP MÁS ESTRECHO Y ELEGANTE --- */
    div.stLinkButton a[href*="wa.me"] {
        background: linear-gradient(90deg, #25D366 0%, #128C7E 100%) !important;
        color: white !important;
        border-radius: 30px !important;
        border: 1px solid rgba(255,255,255,0.2) !important; /* Borde fino sugerido */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        font-weight: bold !important;
        font-size: 14px !important; /* Texto un poco más pequeño para que quepa bien */
        padding: 8px 15px !important; /* Menos relleno para hacerlo más fino */
        display: flex !important;
        justify-content: center !important;
        text-decoration: none !important;
    }

    /* Estilo específico para el icono dentro del texto */
    .fa-whatsapp-icon {
        font-family: "Font Awesome 6 Brands" !important;
        margin-right: 10px;
        font-size: 20px;
    }

    /* --- BOTÓN CONTACTAR Y OTROS (AZUL) --- */
    /* Usamos :not para que esta regla no afecte al de WhatsApp */
    
    div.stButton > button, .stLinkButton a:not([href*="wa.me"]) {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        font-weight: bold !important;
        height: 45px !important;
        width: 100% !important;
        transition: 0.2s ease;
    }

    /* Efecto al pasar el ratón (opcional pero recomendado) */
    div.stButton > button:hover {
        transform: scale(1.05) !important;
        filter: brightness(1.1);
    }
    
    /* 9. OCULTAR UI NATIVA */
    header, [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    footer, [data-testid="stFooter"] { display: none !important; height: 0px !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* AÑADIR: Color blanco para el nombre del archivo subido */
    [data-testid="stFileUploaderFileName"] {
        color: #ffffff !important;
    }

    /* AÑADIR: Quitar bordes de cajas en el móvil para que no se vea el rastro blanco */
    @media only screen and (max-width: 600px) {
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: none !important;
            padding: 0 !important;
        }
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 0px !important;
            padding-right: 0px !important;
        }
    }

    /* --- DISEÑO FAQ PREMIUM: TRANSPARENTE Y BLANCO --- */
    
    /* 1. Fondo transparente para la caja principal y quitar bordes blancos */
    .stExpander {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }

    /* 2. Forzar letras BLANCAS en el título (Cerrado y Abierto) */
    .stExpander details summary p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* 3. Forzar letras BLANCAS en el contenido interior */
    .stExpander details div {
        color: #ffffff !important;
    }

    /* 4. Cambiar color del icono de la flecha a Blanco */
    .stExpander details summary svg {
        fill: #ffffff !important;
    }

    /* 5. Eliminar el color de fondo que Streamlit pone al pasar el ratón o hacer clic */
    .stExpander details summary:hover, 
    .stExpander details summary:active, 
    .stExpander details summary:focus {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
    }

</style>
""", unsafe_allow_html=True)
# ==============================================================================
# 3. LÓGICA & FUNCIONES
# ==============================================================================

if "active_tab" not in st.session_state: 
    st.session_state.active_tab = 0 # 0 es Inicio, 1 Analizar... 4 Impuestos
keys = ["contract_text", "analysis_report", "generated_contract", "generated_claim", "generated_calc", "defense_text"]
for k in keys:
    if k not in st.session_state: st.session_state[k] = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "analysis_done" not in st.session_state: st.session_state.analysis_done = False

# --- FUNCIÓN DE LIMPIEZA AGRESIVA (PEGAR ARRIBA) ---
def nukear_memoria_reclamacion():
    """Borra cualquier rastro de texto generado en la pestaña 3"""
    st.session_state.generated_claim = ""

def limpiar_cache_reclamacion():
    """Borra el resultado de la reclamación al cambiar de modo"""
    st.session_state.generated_claim = ""  
    

@st.cache_data(ttl=3600) # Se actualiza cada hora
def obtener_euribor_actual():
    try:
        # 1. Web objetivo
        url = "https://www.euribor.com.es/"
        
        # 2. Navegador simulado
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            import re
            
            # 3. ESTRATEGIA FRANCOTIRADOR: Buscamos "Euríbor hoy" y pillamos el número que le sigue
            # (?i) hace que no importe si es mayúscula o minúscula
            # Busca: "Euríbor hoy", luego cualquier cosa (espacios, dos puntos), y luego el número (d.ddd)
            match_hoy = re.search(r"(?i)Euríbor hoy.*?:.*?(\d+[.,]\d+)", response.text)
            
            if match_hoy:
                # Encontramos el dato exacto del día (ej: 2.248)
                valor = match_hoy.group(1).replace(',', '.')
                return float(valor)
            
            # 4. ESTRATEGIA DE RESPALDO: Si no encuentra "hoy", busca la "Media" del mes
            match_media = re.search(r"(?i)Media.*?(\d+[.,]\d+)", response.text)
            if match_media:
                valor = match_media.group(1).replace(',', '.')
                return float(valor)

        return 2.248 # Valor fijo de tu captura (por si la web se cae)
        
    except Exception as e:
        print(f"Error Euribor: {e}")
        return 2.248 # Valor seguro
        
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extract = page.extract_text()
            if extract: text += extract + "\n"
    return text

def analyze_image_groq(image_file, prompt_instruction, key):
    image_bytes = image_file.read()
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    client = Groq(api_key=key)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_instruction},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
            temperature=0.1,
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"Error Vision AI: {str(e)}"

# --- FUNCIÓN GENERAR PDF PROFESIONAL (CON NEGRITAS Y ESTILOS) ---
def create_pdf(text, title="Documento Legal"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Márgenes
    margin_x = 50
    margin_y = 50
    max_width = width - (2 * margin_x)
    cursor_y = height - margin_y # Empezamos arriba
    
    # Preparar estilos
    styles = getSampleStyleSheet()
    
    # Estilo Normal (Cuerpo)
    style_body = ParagraphStyle(
        'JustifiedBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14, # Espaciado entre líneas
        alignment=TA_JUSTIFY, # Justificado como contrato real
        spaceAfter=6
    )
    
    # Estilo Título (Cabeceras ##)
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        spaceAfter=10,
        spaceBefore=10
    )

    # 1. DIBUJAR EL TÍTULO DEL DOCUMENTO (Cabecera Principal)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, cursor_y, title)
    c.setLineWidth(0.5)
    c.line(margin_x, cursor_y - 10, width - margin_x, cursor_y - 10)
    cursor_y -= 40 # Bajamos el cursor

    # 2. PROCESAR EL TEXTO LÍNEA A LÍNEA
    # Reemplazamos los saltos de línea dobles para separar párrafos
    paragraphs = text.split('\n')
    
    for para_text in paragraphs:
        para_text = para_text.strip()
        if not para_text:
            cursor_y -= 10 # Espacio extra si hay línea vacía
            continue
            
        # --- LÓGICA DE DETECCIÓN DE FORMATO ---
        
        # A) Si es un título Markdown (## o ###)
        if para_text.startswith('#'):
            # Quitamos las almohadillas
            clean_text = para_text.replace('#', '').strip()
            p = Paragraph(clean_text, style_heading)
        
        # B) Si es texto normal
        else:
            # MAGIA: Convertimos **texto** en <b>texto</b> para ReportLab
            # Usamos Regex para reemplazar todas las ocurrencias
            formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para_text)
            p = Paragraph(formatted_text, style_body)

        # Calculamos cuánto ocupa este párrafo
        w, h = p.wrap(max_width, height)
        
        # Si no cabe en la página, creamos una nueva
        if cursor_y - h < margin_y:
            c.showPage()
            cursor_y = height - margin_y
            # Si cambiamos de página, volvemos a calcular wrap por si acaso
            w, h = p.wrap(max_width, height)
        
        # Dibujamos el párrafo
        p.drawOn(c, margin_x, cursor_y - h)
        cursor_y -= h # Bajamos el cursor lo que ocupe el párrafo

    c.save()
    buffer.seek(0)
    return buffer
    
# --- FUNCIÓN PARA GENERAR WORD (.docx) ---
def create_docx(text, title="Documento"):
    doc = Document()
    doc.add_heading(title, 0)
    for paragraph in text.split('\n'):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- FUNCIÓN PARA ENLACE WHATSAPP ---
def get_whatsapp_link(text):
    # Cortamos el texto si es muy largo para que quepa en la URL
    msg = f"Hola, aquí tienes el documento generado por AbogadoIA:\n\n{text[:500]}...\n(Ver documento completo adjunto)"
    encoded_msg = urllib.parse.quote(msg)
    return f"https://wa.me/?text={encoded_msg}"

def groq_engine(prompt, key, temp=0.2):
    client = Groq(api_key=key)
    try:
        sys_msg = "Eres LegalApp, abogado y asesor fiscal experto en España. Responde de forma directa, compacta y profesional. Cita leyes."
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
            {"role":"system", "content": sys_msg},
            {"role":"user","content":prompt}
        ], temperature=temp).choices[0].message.content
    except Exception as e: return f"Error AI: {str(e)}"

def save_lead(email, action, details):
    """Guarda el lead en Google Sheets"""
    try:
        json_creds = os.getenv("GOOGLE_CREDENTIALS")
        if json_creds:
            creds_dict = json.loads(json_creds)
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            
            # Asegúrate de que esta hoja existe en tu Drive
            sheet = client.open("Base de Datos LegalApp").sheet1 
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, email, action, details])
            print(f"✅ Guardado en Google: {email}")
        else:
            print("⚠️ No hay credenciales Google configuradas.")
    except Exception as e:
        print(f"❌ Error Google Sheets: {e}")

# ==============================================================================
# 4. INTERFAZ PRINCIPAL
# ==============================================================================

# --- LOGO (SOLUCIÓN HTML PURO ANTI-FULLSCREEN) ---
c_logo1, c_logo2, c_logo3 = st.columns([3, 2, 3]) 
with c_logo2:
    if os.path.isfile("logo.png"):
        # 1. Leemos la imagen como bytes
        with open("logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        # 2. La inyectamos como HTML con 'pointer-events: none' (INTOCABLE)
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{encoded_string}" 
                     style="width: 100%; max-width: 300px; pointer-events: none; user-select: none;">
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h1 style='text-align: center; color: white;'>🦅 LegalApp AI</h1>", unsafe_allow_html=True)

st.write("") 

if not api_key:
    st.error("⚠️ Falta API Key. Configura GROQ_API_KEY en Render.")
    st.stop()

# Sustituye tu línea de tabs por esta:
tabs = st.tabs(["🏠 INICIO", "🔍 ANALIZAR", "✍️ CREAR CONTRATO", "⚖️ RECLAMAR/RECURRIR", "📊 IMPUESTOS"])

# Esta línea es un truco para que Streamlit fuerce el cambio visual
# (Se coloca justo después de definir los tabs)

with tabs[0]:
    st.markdown("<h1 style='display:none;'>LegalApp AI - Inteligencia Legal en España</h1>", unsafe_allow_html=True)
    st.subheader("Bienvenido a LegalApp")
    st.caption("Tu asistente jurídico inteligente disponible las 24 horas.")
    
    col1, col2, col3 = st.columns(3)

    script_universal_scroll = """
        <script>
            function goToTab(index) {
                // 1. Cambiar la pestaña
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs[index]) { tabs[index].click(); }
                
                // 2. BUSCAR EL ANCLA INVISIBLE Y SALTAR A ELLA
                var topAnchor = window.parent.document.getElementById('top-of-page');
                if (topAnchor) {
                    topAnchor.scrollIntoView({behavior: "auto", block: "start", inline: "nearest"});
                }

                // 3. RESPALDO: Forzar también los contenedores internos
                var mainView = window.parent.document.querySelector('section[data-testid="stAppViewContainer"]');
                if (mainView) { mainView.scrollTop = 0; }
            }
        </script>
    """
    
    with col1:
        st.markdown("#### 🔍 Analizar")
        st.write("Detecta cláusulas abusivas y riesgos en tus contratos o nóminas.")
        if st.button("Empezar Análisis", key="btn_ir_analizar"):
            components.html(script_universal_scroll + "<script>goToTab(2);</script>", height=0)
        
    with col2:
        st.markdown("#### ✍️ Crear")
        st.write("Genera contratos de alquiler, préstamos o trabajo listos para firmar.")
        if st.button("Redactar Contrato", key="btn_ir_crear"):
            components.html(script_universal_scroll + "<script>goToTab(2);</script>", height=0)
        
    with col3:
        st.markdown("#### 📊 Impuestos")
        st.write("Calcula tu sueldo neto, hipoteca o impuestos por venta de vivienda.")
        if st.button("Calcular ahora", key="btn_ir_impuestos"):
            components.html(script_universal_scroll + "<script>goToTab(2);</script>", height=0)

    st.write("---")
    st.warning("⚠️ **Nota Importante:** Esta herramienta ofrece orientación basada en IA. Siempre recomendamos la revisión final por un profesional colegiado.")

    # Añadir después del st.warning en tabs[0]
    st.write("")
    st.markdown("### 🛠️ Soluciones Legales Populares")
    c_serv1, c_serv2, c_serv3 = st.columns(3)
    
    with c_serv1:
        st.info("**Préstamos Familiares**\n\nEvita multas de Hacienda con contratos de préstamo entre particulares (Modelo 600).")
    with c_serv2:
        st.info("**Revisión de Alquiler**\n\nAnalizamos tu contrato de vivienda para asegurar que cumple con la nueva Ley de Vivienda.")
    with c_serv3:
        st.info("**Euríbor al día**\n\nCalculamos tu hipoteca variable con el valor oficial del Euríbor en tiempo real.")
    
    
# --- ACCESOS DIRECTOS A TRÁMITES (CORREGIDO Y UNIFICADO) ---
    st.write("")
    st.markdown("#### ⚡ Realiza tu trámite ahora gratis")
    
    c_acc1, c_acc2, c_acc3 = st.columns(3)
    
    # 1. Definimos la variable (Nombre: script_universal_scroll)
    script_universal_scroll = """
        <script>
            function goToTab(index) {
                // 1. Cambiar la pestaña
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs[index]) { tabs[index].click(); }
                
                // 2. BUSCAR EL ANCLA INVISIBLE Y SALTAR A ELLA
                var topAnchor = window.parent.document.getElementById('top-of-page');
                if (topAnchor) {
                    // Usamos setTimeout para dar tiempo a que la pestaña cambie visualmente antes de saltar
                    setTimeout(function() {
                        topAnchor.scrollIntoView({behavior: "auto", block: "start", inline: "nearest"});
                    }, 100);
                }

                // 3. RESPALDO: Forzar también el contenedor principal
                var mainView = window.parent.document.querySelector('section[data-testid="stAppViewContainer"]');
                if (mainView) { mainView.scrollTop = 0; }
            }
        </script>
    """

    # 2. Usamos la variable CORRECTA dentro de los botones
    with c_acc1:
        if st.button("💰 Préstamos", key="btn_q1_uni"):
            # AQUÍ estaba el error: ahora usamos script_universal_scroll
            components.html(script_universal_scroll + "<script>goToTab(2);</script>", height=0)
            
    with c_acc2:
        if st.button("🏠 Alquiler", key="btn_q2_uni"):
            components.html(script_universal_scroll + "<script>goToTab(1);</script>", height=0)

    with c_acc3:
        if st.button("📉 Hipoteca", key="btn_q3_uni"):
            components.html(script_universal_scroll + "<script>goToTab(4);</script>", height=0)
    
    # --- BOTÓN DE COMPARTIR (Asegúrate de que estas líneas estén indentadas) ---
    st.write(""); st.write("") 
    mensaje_share = "¡Mira esta herramienta legal con IA! Analiza contratos y redacta documentos al instante: https://legalapp.es"
    url_wa = f"https://wa.me/?text={mensaje_share.replace(' ', '%20')}"

    # Centramos el botón en el medio (todo dentro del with tabs[0])
    col_wa_1, col_wa_2, col_wa_3 = st.columns([3, 2, 3])
    with col_wa_2:
        st.link_button("📲Compartir por WhatsApp", url_wa, use_container_width=True)

# --- FILA 4: PREGUNTAS FRECUENTES (FAQ) ---
    st.write("")
    st.markdown("### ❓ Preguntas Frecuentes")
    
    with st.expander("¿Tienen validez legal los documentos generados?"):
        st.write("""
        Sí. Los documentos generados por LegalApp AI siguen la normativa vigente en España (LAU, Código Civil, Estatuto de los Trabajadores). 
        Utilizamos modelos de lenguaje entrenados específicamente en derecho español para asegurar que todas las cláusulas necesarias estén presentes.
        """)
        
    with st.expander("¿Cómo registro mi contrato ante las autoridades?"):
        st.write("""
        Dependiendo del contrato:
        - **Alquiler:** Debe depositarse la fianza en el organismo autonómico correspondiente (ej. IVIMA en Madrid).
        - **Préstamo:** Debe presentarse el Modelo 600 en Hacienda (está exento de pago).
        """)

    with st.expander("¿Es seguro subir mis documentos personales?"):
        st.write("""
        Totalmente. Los archivos se procesan de forma cifrada y efímera. Una vez analizados, no se guardan permanentemente en nuestros servidores ni se utilizan para entrenar modelos públicos de IA.
        """)
      
    with st.expander("¿Qué es el Modelo 600 que mencionáis?"):
            st.write("Es el impuesto de Transmisiones Patrimoniales. Para préstamos entre particulares es obligatorio presentarlo, aunque la cuota a pagar es 0€ (exento).")    
    
# --- TAB 1: ANALIZADOR INTELIGENTE (FUSIÓN DASHBOARD + CHAT + HERRAMIENTAS) ---
with tabs[1]:
    st.subheader("Analizador de Documentos")
    
    if "nav_analizar" not in st.session_state:
        st.session_state.nav_analizar = "MENU"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- VISTA A: MENÚ PRINCIPAL ---
    if st.session_state.nav_analizar == "MENU":
        st.info("Selecciona qué quieres analizar:")
        
        c_menu_ana_1, c_menu_ana_2 = st.columns(2)
        
        with c_menu_ana_1:
            if st.button("📄\nANALIZAR\nCONTRATO", use_container_width=True):
                st.session_state.nav_analizar = "CONTRATO"
                st.session_state.analisis_result = ""
                st.session_state.contract_text = "" # Limpiamos texto previo
                st.session_state.chat_history = []  # Limpiamos chat previo
                st.rerun()
            
            if st.button("💬\nCHAT / PREGUNTAR\nA DOCUMENTO", use_container_width=True):
                st.session_state.nav_analizar = "GENERICO"
                st.session_state.analisis_result = ""
                st.session_state.contract_text = ""
                st.session_state.chat_history = []
                st.rerun()

        with c_menu_ana_2:
            if st.button("🛡️\nREVISAR\nSEGURO", use_container_width=True):
                st.session_state.nav_analizar = "SEGURO"
                st.session_state.analisis_result = ""
                st.session_state.contract_text = ""
                st.session_state.chat_history = []
                st.rerun()
            
            # ACCESO DIRECTO A NÓMINAS (Pestaña 4)
            if st.button("📊\nESCÁNER\nNÓMINAS", use_container_width=True):
                st.session_state.nav_impuestos = "ESCANER" # Preparamos la tab 4
                # JavaScript para saltar de pestaña
                components.html("""<script>var tabs=window.parent.document.querySelectorAll('button[data-baseweb="tab"]');tabs[4].click();</script>""", height=0)

    # --- VISTA B: HERRAMIENTAS ---
    else:
        c_ana_izq, c_ana_der = st.columns([1, 1.3])
        
        with c_ana_izq:
            if st.button("⬅️ VOLVER AL MENÚ"):
                st.session_state.nav_analizar = "MENU"
                st.session_state.analisis_result = ""
                st.rerun()
            
            st.markdown("---")
            modo = st.session_state.nav_analizar

            # === CONTRATO ===
            if modo == "CONTRATO":
                st.info("📄 Sube un contrato (Alquiler, Servicios, Laboral).")
                f = st.file_uploader("PDF/Imagen", type=["pdf", "jpg", "png"], key="u_cont")
                if f and st.button("🔍 ANALIZAR RIESGOS", key="btn_cont"):
                    with st.spinner("Leyendo letra pequeña..."):
                        if f.type == "application/pdf": txt = extract_text_from_pdf(f)
                        else: txt = analyze_image_groq(f, "Lee este contrato", api_key)
                        
                        st.session_state.contract_text = txt # Guardamos para el chat
                        
                        p = f"""
                        Actúa como Abogado. Analiza: {txt[:6000]}.
                        Informe: 1.Resumen. 2.Duración/Fechas. 3.Pagos. 4.🚨 CLÁUSULAS ABUSIVAS. 5.Veredicto.
                        """
                        st.session_state.analisis_result = groq_engine(p, api_key)

            # === SEGUROS ===
            elif modo == "SEGURO":
                st.info("🛡️ Sube tu Póliza (Hogar, Coche, Salud).")
                f = st.file_uploader("Póliza", type=["pdf", "jpg", "png"], key="u_seg")
                if f and st.button("🛡️ ANALIZAR COBERTURAS", key="btn_seg"):
                    with st.spinner("Revisando coberturas..."):
                        if f.type == "application/pdf": txt = extract_text_from_pdf(f)
                        else: txt = analyze_image_groq(f, "Lee póliza", api_key)
                        
                        st.session_state.contract_text = txt # Guardamos para el chat
                        
                        p = f"""
                        Actúa como Corredor Seguros. Analiza: {txt[:7000]}.
                        Informe: 1.✅ LO QUE CUBRE. 2.❌ EXCLUSIONES (Lo que NO paga). 3.💶 LÍMITES. 4.💡 FRANQUICIAS. 5.CONCLUSIÓN.
                        """
                        st.session_state.analisis_result = groq_engine(p, api_key)

            # === CHAT / GENÉRICO ===
            elif modo == "GENERICO":
                st.info("💬 Sube un documento para chatear con él.")
                f = st.file_uploader("Documento", type=["pdf", "jpg", "png"], key="u_gen")
                if f and not st.session_state.contract_text:
                    if st.button("📂 PROCESAR DOCUMENTO"):
                        with st.spinner("Leyendo..."):
                            if f.type == "application/pdf": txt = extract_text_from_pdf(f)
                            else: txt = analyze_image_groq(f, "Lee doc", api_key)
                            st.session_state.contract_text = txt
                            st.success("¡Leído! Ya puedes preguntar a la derecha 👉")

        # --- VISOR DE RESULTADOS + HERRAMIENTAS EXTRA ---
        with c_ana_der:
            # A) Si hay informe inicial, lo mostramos
            if st.session_state.analisis_result:
                st.markdown(f"<div class='contract-box'>{st.session_state.analisis_result}</div>", unsafe_allow_html=True)
                
                # Botón descargar PDF
                pdf = create_pdf(st.session_state.analisis_result, f"Informe {modo}")
                st.download_button("⬇️ Bajar Informe PDF", data=pdf, file_name="Informe.pdf", mime="application/pdf")
                st.write("---")

            # B) HERRAMIENTAS ADICIONALES (Solo si hay texto cargado)
            if st.session_state.contract_text:
                
                # 1. GENERADOR DE CARTA DE CANCELACIÓN (Recuperado)
                if modo == "CONTRATO":
                    with st.expander("📅 Generar Carta de Cancelación", expanded=False):
                        st.caption("Redacta un aviso formal para terminar este contrato.")
                        email_remitente = st.text_input("Tu Email / ID", key="email_cancel")
                        fecha_cancel = st.date_input("Fecha baja", key="date_cancel")
                        
                        if st.button("✉️ Redactar Carta"):
                            with st.spinner("Escribiendo..."):
                                p_cancel = f"""
                                Actúa como abogado. Basado en: "{st.session_state.contract_text[:3000]}..."
                                Redacta CARTA FORMAL DESISTIMIENTO. Remitente: {email_remitente}. Fecha: {fecha_cancel}.
                                Tono firme y legal.
                                """
                                carta = groq_engine(p_cancel, api_key)
                                st.markdown(f"<div class='contract-box'>{carta}</div>", unsafe_allow_html=True)
                                pdf_c = create_pdf(carta, "Cancelacion")
                                st.download_button("⬇️ Bajar Carta", pdf_c, "Baja.pdf")

                # 2. CHAT INTERACTIVO (Recuperado)
                st.markdown("### 💬 Chat con el Documento")
                
                # Historial
                for m in st.session_state.chat_history:
                    css = "chat-user" if m["role"]=="user" else "chat-bot"
                    st.markdown(f"<div class='{css}'>{m['content']}</div>", unsafe_allow_html=True)
                
                # Input del chat
                if q := st.chat_input("Pregunta algo sobre el archivo..."):
                    st.session_state.chat_history.append({"role":"user","content":q})
                    st.markdown(f"<div class='chat-user'>{q}</div>", unsafe_allow_html=True)
                    
                    with st.spinner("Pensando..."):
                        ans = groq_engine(f"Contexto: {st.session_state.contract_text[:10000]}. Pregunta: {q}", api_key)
                    
                    st.session_state.chat_history.append({"role":"assistant","content":ans})
                    st.rerun() # Para refrescar y mostrar la respuesta

# --- TAB 2: GENERADOR DE CONTRATOS (VERSIÓN RESTAURADA Y BLINDADA) ---
with tabs[2]:
    # 1. CONTENEDOR MÁGICO (Evita que se mezclen menús y formularios)
    # Todo lo que pintemos, lo haremos dentro de este 'placeholder'. 
    # Al cambiar de vista, el placeholder se vacía automáticamente.
    main_placeholder = st.empty()

    # 2. GESTIÓN DEL ESTADO
    if "nav_crear" not in st.session_state:
        st.session_state.nav_crear = "MENU"
        
    # Variables de seguridad
    tipo_texto = "Documento Legal" 
    data_p = "Datos generales"

    # ==============================================================================
    # ESCENA A: EL MENÚ DE BOTONES
    # ==============================================================================
    if st.session_state.nav_crear == "MENU":
        # Usamos .container() para pintar DENTRO del placeholder
        with main_placeholder.container():
            st.subheader("Generador de Contratos")
            st.info("👆 Selecciona el documento que necesitas crear:")
            
            c1, c2, c3 = st.columns(3)
            
            # Función para cambiar de pantalla y limpiar rastros
            def ir_a(destino):
                st.session_state.nav_crear = destino
                st.session_state.generated_contract = ""
            
            with c1:
                st.button("🏠\nALQUILER\nVIVIENDA", use_container_width=True, on_click=ir_a, args=("ALQUILER",))
                st.button("💼\nCONTRATO\nTRABAJO", use_container_width=True, on_click=ir_a, args=("TRABAJO",))
                st.button("🏡\nCOMPRAVENTA\nVIVIENDA", use_container_width=True, on_click=ir_a, args=("C_VIVIENDA",))

            with c2:
                st.button("💰\nPRÉSTAMO\nPARTICULARES", use_container_width=True, on_click=ir_a, args=("PRESTAMO",))
                st.button("🤝\nSERVICIOS\nFREELANCE", use_container_width=True, on_click=ir_a, args=("SERVICIOS",))
                st.button("📝\nCONTRATO\nDE ARRAS", use_container_width=True, on_click=ir_a, args=("ARRAS",))

            with c3:
                st.button("🚗\nCOMPRAVENTA\nVEHÍCULO", use_container_width=True, on_click=ir_a, args=("VEHICULO",))
                st.button("🤫\nNDA\nCONFIDENCIALIDAD", use_container_width=True, on_click=ir_a, args=("NDA",))
                st.button("❌\nCANCELACIÓN\nCONTRATO", use_container_width=True, on_click=ir_a, args=("CANCELACION",))

    # ==============================================================================
    # ESCENA B: EL FORMULARIO (Se activa si NO estamos en MENU)
    # ==============================================================================
    else:
        # Al entrar aquí, el 'main_placeholder' SE VACÍA. Adiós botones antiguos.
        with main_placeholder.container():
            
            # Layout: Botón volver (izq) y Formulario (der)
            c_izq, c_der = st.columns([1, 1.3])
            
            # --- COLUMNA IZQUIERDA: DATOS DEL CONTRATO ---
            with c_izq:
                # Botón volver
                def volver():
                    st.session_state.nav_crear = "MENU"
                    st.session_state.generated_contract = ""
                
                st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, on_click=volver)
                st.markdown("---")
                
                modo = st.session_state.nav_crear
                
                # 1. ALQUILER (Con cálculo de fechas automático)
                if modo == "ALQUILER":
                    st.subheader("🏠 Alquiler Vivienda")
                    tipo_texto = "Contrato de Alquiler de Vivienda Habitual (LAU)"
                    
                    prop = st.text_input('Propietario (Nombre y DNI)', key="alq_prop")
                    inq = st.text_input('Inquilino (Nombre y DNI)', key="alq_inq")
                    dir_piso = st.text_input('Dirección completa', key="alq_dir")
                    
                    c1, c2 = st.columns(2)
                    with c1: ref_cat = st.text_input('Ref. Catastral', key="alq_ref")
                    with c2: renta = st.number_input('Renta (€/mes)', value=800.0, step=50.0, key="alq_renta")
                    
                    c3, c4 = st.columns(2)
                    with c3: f_inicio = st.date_input("Fecha Inicio", value=datetime.now(), key="alq_ini")
                    with c4: duracion = st.number_input("Años", 1, 20, 5, key="alq_dur")
                    
                    # Lógica fechas
                    try: f_fin = f_inicio.replace(year=f_inicio.year + duracion)
                    except: f_fin = f_inicio.replace(year=f_inicio.year + duracion, month=3, day=1)
                    st.caption(f"📅 Finaliza el: **{f_fin.strftime('%d/%m/%Y')}**")
                    
                    clausulas = st.text_area("Cláusulas Extra", placeholder="Ej: No mascotas.", key="alq_clau")
                    data_p = f"Propietario: {prop}. Inquilino: {inq}. Piso: {dir_piso}. Ref: {ref_cat}. Renta: {renta}. Inicio: {f_inicio}. Duración: {duracion} años (Fin: {f_fin}). Extras: {clausulas}."

                # 2. PRÉSTAMO (Con calculadora de intereses recuperada)
                elif modo == "PRESTAMO":
                    st.subheader("💰 Préstamo Dinero")
                    tipo_texto = "Contrato de Préstamo entre Particulares"
                    
                    c1, c2 = st.columns(2)
                    with c1: 
                        pres_nom = st.text_input("Prestamista (Deja dinero)", key="pre_pres")
                        pres_dni = st.text_input("DNI Prestamista", key="pre_dnip")
                    with c2: 
                        pret_nom = st.text_input("Prestatario (Recibe dinero)", key="pre_pret")
                        pret_dni = st.text_input("DNI Prestatario", key="pre_dnir")
                    
                    c3, c4 = st.columns(2)
                    with c3: importep = st.number_input("Importe (€)", 100.0, step=100.0, key="pre_imp")
                    with c4: plazop = st.number_input("Plazo (Meses)", 1, 120, 12, key="pre_pla")
                    
                    # Lógica intereses recuperada
                    interes = st.checkbox("¿Con Intereses?", key="pre_int")
                    detalles = "Sin intereses (Tipo 0%)"
                    
                    if interes:
                        tipo_int = st.number_input("Interés Anual (%)", 1.0, step=0.5, key="pre_tint")
                        # Calculadora Sistema Francés
                        i = (tipo_int / 100) / 12
                        c_men = importep * (i * (1 + i)**plazop) / ((1 + i)**plazop - 1)
                        total_dev = c_men * plazop
                        st.success(f"🧮 Cuota: **{c_men:.2f}€/mes**. Total a devolver: {total_dev:.2f}€")
                        detalles = f"Con interés del {tipo_int}% anual. Cuota mensual: {c_men:.2f}€."
                    
                    data_p = f"Prestamista: {pres_nom} ({pres_dni}). Prestatario: {pret_nom} ({pret_dni}). Importe: {importep}€. Plazo: {plazop} meses. {detalles}."

               # 4. TRABAJO (COMPLETO: HORARIOS, CIF, REPRESENTANTE)
                elif modo == "TRABAJO":
                    st.subheader("💼 Contrato Laboral")
                    tipo_texto = "Contrato de Trabajo"
                    
                    st.caption("🏢 Empresa y Representante")
                    c_emp1, c_emp2 = st.columns(2)
                    with c_emp1:
                        empresa_nom = st.text_input("Nombre Empresa", key="tra_emp_nom")
                    with c_emp2:
                        empresa_cif = st.text_input("CIF Empresa", key="tra_emp_cif")
                    
                    empresa_rep = st.text_input("Representante Legal (Quien firma)", placeholder="Ej: Administrador único", key="tra_rep")

                    st.caption("👤 Trabajador")
                    c_trab1, c_trab2 = st.columns(2)
                    with c_trab1:
                        trab_nom = st.text_input("Nombre Trabajador", key="tra_trab_nom")
                    with c_trab2:
                        trab_dni = st.text_input("DNI/NIE Trabajador", key="tra_trab_dni")

                    st.caption("⏰ Jornada y Horario")
                    c_hor1, c_hor2 = st.columns(2)
                    with c_hor1:
                        horas_sem = st.number_input("Horas Semanales", min_value=1.0, max_value=40.0, value=40.0, step=0.5, key="tra_horas")
                    with c_hor2:
                        es_flexible = st.checkbox("¿Horario Flexible?", key="tra_flex")
                    
                    if es_flexible:
                        horario_txt = st.text_input("Detalle Flexibilidad", placeholder="Ej: Entrada 8-9h, Salida 17-18h", key="tra_hor_txt")
                        texto_horario = f"Horario Flexible: {horario_txt}"
                    else:
                        horario_txt = st.text_input("Horario Fijo", placeholder="Ej: L-V de 9:00 a 18:00", key="tra_hor_txt")
                        texto_horario = f"Horario Fijo: {horario_txt}"

                    st.caption("📋 Condiciones Económicas")
                    puesto = st.text_input("Puesto / Categoría", key="tra_pue")
                    
                    c_cond1, c_cond2 = st.columns(2)
                    with c_cond1:
                        modalidad = st.selectbox("Modalidad", ["Indefinido", "Temporal", "Prácticas"], key="tra_mod")
                    with c_cond2:
                        salario = st.number_input("Salario Bruto Anual (€)", 15000.0, step=500.0, key="tra_sal")
                    
                    duracion_txt = "Indefinida"
                    if modalidad != "Indefinido":
                        duracion_txt = st.text_input("Duración / Fecha Fin", placeholder="Ej: 6 meses", key="tra_dur")

                    tiene_variable = st.checkbox("¿Incluye Bonus/Variable?", key="tra_var_check")
                    variable_txt = "Sin variable"
                    if tiene_variable:
                        variable_txt = st.text_input("Detalle del Bonus", key="tra_var_txt")

                    # PROMPT ACTUALIZADO CON TODOS LOS DATOS
                    data_p = f"""
                    EMPRESA: {empresa_nom} (CIF: {empresa_cif}).
                    REPRESENTANTE LEGAL: {empresa_rep}.
                    TRABAJADOR: {trab_nom} (DNI: {trab_dni}).
                    PUESTO: {puesto}. MODALIDAD: {modalidad}. DURACIÓN: {duracion_txt}.
                    JORNADA: {horas_sem} horas/semana. {texto_horario}.
                    SALARIO: {salario}€ Brutos/Año. VARIABLE: {variable_txt}.
                    """
                    
                elif modo == "VEHICULO":
                     st.subheader("🚗 Compraventa Vehículo")
                     st.caption("👤 Intervinientes")
                     vendedor = st.text_input("Vendedor (Nombre y DNI)")
                     comprador = st.text_input("Comprador (Nombre y DNI)")
                     st.caption("🚗 Datos del Vehículo")
                     col_coche1, col_coche2 = st.columns(2)
                     with col_coche1:
                          marca = st.text_input("Marca y Modelo", placeholder="Ej: Ford Focus 1.5")
                          matricula = st.text_input("Matrícula")
                     with col_coche2:
                          bastidor = st.text_input("Nº Bastidor (VIN)", help="Fundamental para la validez legal")
                          kms = st.number_input("Kilómetros", min_value=0, step=1000)
                     precio = st.number_input("Precio Venta (€)", min_value=0.0, step=50.0)
                     data_p = f"Compraventa Vehículo. Vendedor: {vendedor}. Comprador: {comprador}. Vehículo: {marca}. Matrícula: {matricula}. Nº Bastidor: {bastidor}. Kilometraje actual: {kms} Km. Precio: {precio} euros. Se declara libre de cargas y al corriente de ITV."
 
                # 5. SERVICIOS
                elif modo == "SERVICIOS":
                    st.subheader("🤝 Servicios Freelance")
                    tipo_texto = "Contrato Prestación Servicios"
                    cli = st.text_input("Cliente", key="ser_cli")
                    pro = st.text_input("Profesional", key="ser_pro")
                    desc = st.text_area("Descripción Servicios", key="ser_des")
                    hon = st.text_input("Honorarios y Pagos", key="ser_hon")
                    data_p = f"Cliente: {cli}. Profesional: {pro}. Servicios: {desc}. Pago: {hon}."

                # === ARRAS ===
                elif modo == "ARRAS":
                     st.subheader("📝 Contrato de Arras")
                     st.caption("📝 Datos para Arras")
                     vendedor = st.text_input('Vendedor (Nombre y DNI/CIF)')
                     comprador = st.text_input('Comprador (Nombre y DNI/CIF)')
                     st.caption("🏠 Inmueble y Condiciones")
                     inmueble = st.text_input('Dirección Inmueble')
                     ref_catastral = st.text_input('Referencia Catastral')
                     col_arras1, col_arras2 = st.columns(2)
                     with col_arras1: precio = st.number_input('Precio Total Venta (€)', step=1000.0)
                     with col_arras2: senal = st.number_input('Señal/Arras (€)', step=500.0)
                     plazo = st.date_input('Fecha Límite Escritura')
                     data_p = f"Contrato de Arras. Vendedor: {vendedor}. Comprador: {comprador}. Inmueble: {inmueble}. Ref. Catastral: {ref_catastral}. Precio Total: {precio}. Señal entregada: {senal}. Fecha límite: {plazo}. Tipo: Arras Penitenciales (Art 1454 CC)."

                # 7. C_VIVIENDA
                elif modo == "C_VIVIENDA":
                    st.subheader("🏡 Compraventa Vivienda")
                    st.caption("👤 Intervinientes")
                    vendedor = st.text_input('Vendedor (Nombre y DNI/CIF)')
                    comprador = st.text_input('Comprador (Nombre y DNI/CIF)')
                    st.caption("🏠 Inmueble")
                    inmueble = st.text_input('Dirección Completa')
                    ref_catastral = st.text_input('Referencia Catastral', help="Código de 20 caracteres")
                    precio = st.number_input('Precio Venta (€)', step=1000.0)
                    data_p = f"Compraventa Inmueble. Vendedor: {vendedor}. Comprador: {comprador}. Dirección: {inmueble}. Referencia Catastral: {ref_catastral}. Precio: {precio} euros. Se vende libre de cargas."
            
                # 8. NDA
                elif modo == "NDA":
                    st.subheader("🤫 Confidencialidad")
                    tipo_texto = "Acuerdo de Confidencialidad (NDA)"
                    rev = st.text_input("Revelador", key="nda_rev")
                    rec = st.text_input("Receptor", key="nda_rec")
                    motivo = st.text_area("Información a proteger", key="nda_mot")
                    data_p = f"Revelador: {rev}. Receptor: {rec}. Info protegida: {motivo}."

                # === CANCELACIÓN ===
                elif modo == "CANCELACION":
                     st.subheader("❌ Acuerdo de Terminación")
                     tipo_texto = "Acuerdo de Terminación de Contrato"
                     contrato_origen = st.text_input("¿Qué contrato se cancela?")
                     partes = st.text_input("Partes implicadas")
                     fecha_efecto = st.date_input("Fecha Efectiva")
                     motivo = st.text_input("Motivo (Opcional)")
                     data_p = f"Terminación Contrato. Origen: {contrato_origen}. Partes: {partes}. Fecha fin: {fecha_efecto}. Motivo: {motivo}."



            # --- COLUMNA DERECHA: GENERACIÓN (COMÚN) ---
            with c_der:
                st.info("👇 **Generar Documento**")
                # Ciudad común para todos los contratos
                ciudad = st.text_input("📍 Ciudad de firma", value="Madrid", key="common_city_tab2")
                
                # BOTÓN REDACTAR (Con manejo de errores integrado)
                if st.button("✨ REDACTAR CONTRATO", use_container_width=True, key="btn_redactar_main"):
                    with st.spinner("La IA está redactando tu contrato..."):
                        try:
                            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                            prompt_final = f"""
                            Actúa como Abogado Experto en España.
                            Redacta un {tipo_texto} formal y válido legalmente.
                            
                            DATOS CLAVE:
                            - DETALLES DEL ACUERDO: {data_p}
                            
                            ESTRUCTURA OBLIGATORIA:
                            1. Encabezado (Lugar, Fecha, Reunidos con DNI).
                            2. Exponen (Antecedentes).
                            3. ESTIPULACIONES (Cláusulas numeradas).
                            4. Cierre y Firmas.
                            5. Lugar y Fecha: En {ciudad}, a {fecha_hoy}.
                            
                            Usa lenguaje jurídico preciso. Formato Markdown.
                            Usa negritas (**) para títulos y partes clave.
                            """
                            st.session_state.generated_contract = groq_engine(prompt_final, api_key, 0.3)
                        except Exception as e:
                            st.error(f"Error al conectar con la IA: {e}")

                # VISOR DE RESULTADOS Y DESCARGAS
                if st.session_state.generated_contract:
                    st.markdown("---")
                    # Visor con caja gris
                    st.markdown(f"<div class='contract-box'>{st.session_state.generated_contract}</div>", unsafe_allow_html=True)
                    
                    st.write("")
                    st.markdown("### 📥 Exportar Documento")
                    
                    # Email ocupa todo el ancho
                    mail_user = st.text_input("Email para copia (Opcional)", key="mail_down_tab2")
                    st.write("")
                    
                    # 3 Columnas para botones (PDF, Word, WhatsApp)
                    c_btn1, c_btn2, c_btn3 = st.columns(3)
                    
                    # BOTÓN PDF
                    with c_btn1:
                        if st.button("📄 PDF", key="btn_pdf_gen_2", use_container_width=True):
                            if mail_user: save_lead(mail_user, "CONTRATO", modo)
                            st.session_state.pdf_buffer = create_pdf(st.session_state.generated_contract, tipo_texto)
                        
                        if "pdf_buffer" in st.session_state:
                            st.download_button("⬇️ Bajar", st.session_state.pdf_buffer, f"{modo}.pdf", "application/pdf", key="dl_pdf_2", use_container_width=True)

                    # BOTÓN WORD
                    with c_btn2:
                        docx_file = create_docx(st.session_state.generated_contract, tipo_texto)
                        st.download_button("📝 Word", docx_file, f"{modo}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_word_2", use_container_width=True)

                    # BOTÓN WHATSAPP
                    with c_btn3:
                        link_wa = get_whatsapp_link(st.session_state.generated_contract)
                        st.link_button("📲 WhatsApp", link_wa, use_container_width=True)
                    
# --- TAB 3: RECLAMAR / RECURRIR (ESTRUCTURA IDÉNTICA A TAB 2) ---
with tabs[3]:
    
    # 1. GESTIÓN DEL ESTADO DE NAVEGACIÓN
    if "nav_reclamar" not in st.session_state:
        st.session_state.nav_reclamar = "MENU"
        
    # ... debajo de if "nav_reclamar" ...
    if "multa_viability" not in st.session_state: st.session_state.multa_viability = ""
    if "temp_multa_txt" not in st.session_state: st.session_state.temp_multa_txt = ""    

    # --- VISTA A: MENÚ PRINCIPAL (GRID DE BOTONES) ---
    if st.session_state.nav_reclamar == "MENU":
        st.subheader("Centro de Reclamaciones")
        st.caption("Selecciona qué trámite quieres iniciar:")
        
        # Definimos columnas AQUÍ (no fuera)
        c_nav1, c_nav2, c_nav3 = st.columns(3)
        
        with c_nav1:
            if st.button("✍️\nREDACTAR BUROFAX\n(Reclamar Deudas)", use_container_width=True):
                st.session_state.nav_reclamar = "BUROFAX"
                st.session_state.generated_claim = "" 
                st.rerun()
        with c_nav2:
            if st.button("🛡️\nRESPONDER CARTA\n(Vecinos, Seguros...)", use_container_width=True):
                st.session_state.nav_reclamar = "RESPONDER"
                st.session_state.generated_claim = ""
                st.rerun()
        with c_nav3:
            if st.button("👮\nRECURRIR MULTA\n(Tráfico/Ayto)", use_container_width=True):
                st.session_state.nav_reclamar = "MULTA"
                st.session_state.generated_claim = ""
                st.session_state.multa_viability = "" # <--- AÑADIR
                st.session_state.temp_multa_txt = ""  # <--- AÑADIR
                st.rerun()

    # --- VISTA B: FORMULARIO ESPECÍFICO ---
    else:
        # Definimos columnas NUEVAS para el formulario (Igual que en Tab 2)
        c_rec, c_doc = st.columns([1, 1.3])
        
        with c_rec:
            # Botón Volver DENTRO de la columna
            if st.button("⬅️ VOLVER AL MENÚ DE RECLAMACIONES"):
                st.session_state.nav_reclamar = "MENU"
                st.session_state.generated_claim = ""
                st.rerun()
            
            st.markdown("---")
            
            # Recuperamos el modo
            modo = st.session_state.nav_reclamar

            # === HERRAMIENTA 1: BUROFAX ===
            if modo == "BUROFAX":
                with st.container(border=False):
                    st.info("Generador de Burofax")
                    remitente = st.text_input("Tus Datos (Nombre, DNI, Dirección)", key="bf_remitente")
                    dest = st.text_input("Destinatario (Empresa/Persona)", key="bf_destinatario")
                    st.markdown("---")
                    
                    motivo = st.selectbox("Motivo", [
                        "Cobro Indebido / Facturas", "Seguros", "Fianza Alquiler", 
                        "Banca", "Transporte", "Otro"
                    ], key="bf_motivo")
                    
                    datos_clave = ""
                    
                    if "Facturas" in motivo:
                        c_fac1, c_fac2 = st.columns(2)
                        with c_fac1: num_fac = st.text_input("Nº Factura / Contrato", key="bf_num")
                        with c_fac2: importe = st.number_input("Importe Reclamado (€)", min_value=0.0, key="bf_imp")
                        fecha_fac = st.date_input("Fecha de la factura", key="bf_date")
                        datos_clave = f"Reclamación de Cantidad. Factura Nº: {num_fac}. Importe: {importe}€. Fecha: {fecha_fac}. Motivo: Cobro indebido o servicio no prestado."
                    
                    elif "Seguros" in motivo:
                        c_seg1, c_seg2 = st.columns(2)
                        with c_seg1: num_poliza = st.text_input("Nº Póliza (Obligatorio)", key="bf_pol")
                        with c_seg2: num_siniestro = st.text_input("Nº Siniestro (Opcional)", key="bf_sin")
                        fecha_sin = st.date_input("Fecha del Siniestro", key="bf_date_sin")
                        datos_clave = f"Reclamación a Aseguradora. Póliza Nº: {num_poliza}. Siniestro Nº: {num_siniestro}. Fecha Ocurrencia: {fecha_sin}. Exigencia de cumplimiento de contrato y cobertura."
                    
                    elif "Fianza" in motivo:
                        direccion = st.text_input("Dirección del Inmueble alquilado", key="bf_dir")
                        fecha_llaves = st.date_input("Fecha devolución llaves", key="bf_date_llaves")
                        importe_fianza = st.number_input("Importe Fianza (€)", min_value=0.0, key="bf_fianza")
                        datos_clave = f"Reclamación de Fianza. Inmueble: {direccion}. Fecha fin contrato: {fecha_llaves}. Importe retenido: {importe_fianza}€. Aplicación de la LAU."
                    
                    elif "Banca" in motivo:
                        producto = st.text_input("Producto (Cuenta/Tarjeta)", key="bf_prod")
                        concepto = st.text_input("Concepto reclamado (Ej: Comisión mantenimiento)", key="bf_con")
                        importe = st.number_input("Importe (€)", min_value=0.0, key="bf_imp_banca")
                        datos_clave = f"Reclamación Bancaria. Producto: {producto}. Concepto: {concepto}. Importe: {importe}€. Solicitud de retrocesión."
                    
                    elif "Transporte" in motivo:
                        vuelo = st.text_input("Nº Vuelo / Localizador", key="bf_vuelo")
                        incidencia = st.selectbox("Incidencia", ["Retraso > 3h", "Cancelación", "Pérdida Equipaje"], key="bf_incid")
                        datos_clave = f"Reclamación Transporte. Referencia: {vuelo}. Incidencia: {incidencia}. Solicitud de indemnización según Reglamento Europeo 261/2004."
                    
                    else: 
                        asunto = st.text_input("Asunto", key="bf_asunto")
                        datos_clave = f"Reclamación Genérica. Asunto: {asunto}."

                    st.write("")
                    hechos = st.text_area("Hechos / Detalles", placeholder="Explica qué ha pasado...", key="bf_hechos")
                    
                    if st.button("🔥 GENERAR BUROFAX", key="btn_bf_gen"):
                        with st.spinner("Redactando..."):
                            p = f"Actúa como abogado. Redacta Burofax. De: {remitente}. A: {dest}. Contexto: {datos_clave}. Hechos: {hechos}. Tono formal."
                            st.session_state.generated_claim = groq_engine(p, api_key)

            # === HERRAMIENTA 2: RESPONDER ===
            elif modo == "RESPONDER":
                with st.container(border=False):
                    st.info("📂 Sube la carta recibida.")
                    uploaded_gen = st.file_uploader("Sube PDF/Foto", type=["pdf", "jpg", "png"], key="rc_upload")
                    mis_argumentos = st.text_area("¿Qué quieres responder?", key="rc_argumentos")
                    
                    if st.button("📝 GENERAR RESPUESTA", key="btn_rc_gen"):
                        if uploaded_gen and mis_argumentos:
                            with st.spinner("Analizando..."):
                                if uploaded_gen.type == "application/pdf": txt = extract_text_from_pdf(uploaded_gen)
                                else: txt = analyze_image_groq(uploaded_gen, "Lee carta", api_key)
                                
                                p = f"Abogado. Recibido: {txt[:4000]}. Responder: {mis_argumentos}. Redacta carta."
                                st.session_state.generated_claim = groq_engine(p, api_key)
                        else: st.warning("Faltan datos.")

            # === HERRAMIENTA 3: MULTAS (NUEVO FLUJO FREEMIUM) ===
            elif modo == "MULTA":
                
                 with st.container(border=False):
                      st.info("👮 Sube la multa para analizarla.")
                      uploaded_multa = st.file_uploader("Sube la Multa (PDF/Foto)", type=["pdf", "jpg", "png"], key="mul_upload")
                      tipo_m = st.selectbox("Tipo", ["Tráfico", "Hacienda", "Otros"], key="mul_tipo")
                      mis_datos = st.text_input("Tus Datos", key="mul_datos")
                    
                      # PASO 1: ANÁLISIS DE VIABILIDAD (GRATIS)
                      if st.button("🔍 ANALIZAR VIABILIDAD (GRATIS)", key="btn_mul_via"):
                         if uploaded_multa:
                            with st.spinner("Buscando defectos de forma..."):
                                # Leemos el archivo
                                if uploaded_multa.type == "application/pdf": txt = extract_text_from_pdf(uploaded_multa)
                                else: txt = analyze_image_groq(uploaded_multa, "Lee multa", api_key)
                                
                                # Guardamos el texto en memoria para no re-leerlo luego
                                st.session_state.temp_multa_txt = txt 
                                
                                # Prompt de Diagnóstico
                                p_viabilidad = f"""
                                Actúa como abogado experto en multas. Analiza este texto:
                                ---
                                {txt[:4000]}
                                ---
                                NO REDACTES EL RECURSO AÚN. Solo dime:
                                1. ¿Es recurrible? (Sí/No/Difícil)
                                2. Probabilidad de éxito estimada (%).
                                3. Posibles defectos de forma detectados (fechas, falta de foto, márgenes, competencia, etc).
                                4. Veredicto breve: ¿Aconsejas recurrir o pagar con descuento?
                                """
                                st.session_state.multa_viability = groq_engine(p_viabilidad, api_key)
                         else:
                            st.warning("Por favor, sube el archivo de la multa.")

                    # MOSTRAR RESULTADO VIABILIDAD (Si ya se hizo)
                      if st.session_state.multa_viability:
                         st.success("✅ Análisis Completado")
                         st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; border-left:4px solid #facc15; font-size:14px;'>{st.session_state.multa_viability}</div>", unsafe_allow_html=True)
                         st.write("")
                        
                        # PASO 2: REDACCIÓN DEL RECURSO (PREMIUM - BOTÓN DESBLOQUEADO)
                         st.markdown("👇 **¿Quieres que redacte el recurso legal?**")
                         if st.button("⚖️ REDACTAR RECURSO AHORA", key="btn_mul_gen"):
                            if mis_datos and st.session_state.temp_multa_txt:
                                with st.spinner("Redactando Pliego de Descargos..."):
                                    p_recurso = f"""
                                    Actúa como Abogado. Redacta el PLIEGO DE DESCARGOS para recurrir la multa analizada anteriormente.
                                    MULTA: {st.session_state.temp_multa_txt[:4000]}
                                    CLIENTE: {mis_datos}.
                                    INSTRUCCIONES: 
                                    - Formato legal formal para presentar ante la administración.
                                    - Alega todos los defectos posibles (indefensión, falta de pruebas, márgenes de error radar, etc).
                                    - Cita leyes y sentencias aplicables.
                                    """
                                    st.session_state.generated_claim = groq_engine(p_recurso, api_key)
                            else:
                                st.warning("Faltan tus datos personales para completar el escrito.")
            
            
                      if st.session_state.generated_claim:
                       st.markdown(f"<div class='contract-box'>{st.session_state.generated_claim}</div>", unsafe_allow_html=True)
                       st.write(""); pdf = create_pdf(st.session_state.generated_claim, "Recurso"); st.download_button("⬇️ PDF", pdf, "recurso.pdf")

        # --- VISOR DE RESULTADOS (COMÚN) ---
        with c_doc:
            if st.session_state.generated_claim:
                st.markdown(f"<div class='contract-box'>{st.session_state.generated_claim}</div>", unsafe_allow_html=True)
                st.write("")
                with st.container(border=False):
                    ce2, cb2 = st.columns([2,1])
                    with ce2: m2 = st.text_input("Email (Opcional)", key="mr_tab3")
                    with cb2:
                        st.write(""); st.write("")
                        if st.button("PDF LEGAL", key="br_tab3"):
                            save_lead(m2, "RECLAMACION", st.session_state.nav_reclamar)
                            pdf = create_pdf(st.session_state.generated_claim, "Documento Legal")
                            st.download_button("⬇️ Bajar PDF", data=pdf, file_name="Legal.pdf", mime="application/pdf")
                            
# --- TAB 4: IMPUESTOS (ARQUITECTURA CORREGIDA Y DEFINITIVA) ---
with tabs[4]:
    # 1. GESTIÓN DEL ESTADO
    if "nav_impuestos" not in st.session_state:
        st.session_state.nav_impuestos = "MENU"

    main_container_imp = st.empty()

    # ==============================================================================
    # ESCENA A: MENÚ PRINCIPAL
    # ==============================================================================
    if st.session_state.nav_impuestos == "MENU":
        with main_container_imp.container():
            st.subheader("Calculadora Fiscal")
            st.caption("Selecciona una herramienta:")
        
            c_nav1, c_nav2 = st.columns(2)
            
            # Grid de botones (Izquierda)
            with c_nav1: 
                if st.button("💰\nDeducciones\nRenta", use_container_width=True): 
                    st.session_state.nav_impuestos = "RENTA"
                    st.session_state.generated_calc = ""
                    st.rerun()
                if st.button("🔍\nEscáner\nNómina", use_container_width=True): 
                    st.session_state.nav_impuestos = "ESCANER"
                    st.session_state.generated_calc = ""
                    st.rerun()
                if st.button("📈\nIPC\nAlquiler", use_container_width=True): 
                    st.session_state.nav_impuestos = "IPC"
                    st.session_state.generated_calc = ""
                    st.rerun()

            # Grid de botones (Derecha)
            with c_nav2: 
                if st.button("💶\nSimulador\nSueldo Neto", use_container_width=True): 
                    st.session_state.nav_impuestos = "SUELDO"
                    st.session_state.generated_calc = ""
                    st.rerun()
                if st.button("📝\nImpuestos\nVivienda", use_container_width=True): 
                    st.session_state.nav_impuestos = "VIVIENDA_TOTAL"
                    st.session_state.generated_calc = ""
                    st.rerun()
                if st.button("📉\nCuota\nHipoteca", use_container_width=True): 
                    st.session_state.nav_impuestos = "HIPOTECA"
                    st.session_state.generated_calc = ""
                    st.rerun()

    # ==============================================================================
    # ESCENA B: LAS HERRAMIENTAS
    # ==============================================================================
    else:
        with main_container_imp.container():
            
            # 1. BOTÓN VOLVER (Común para todos)
            def volver_imp():
                st.session_state.nav_impuestos = "MENU"
                st.session_state.generated_calc = ""
            
            st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, on_click=volver_imp)
            st.markdown("---")
            
            modo = st.session_state.nav_impuestos
            anio_actual = datetime.now().year

            # ==========================================================================
            # CASO ESPECIAL: VIVIENDA TOTAL (ANCHO COMPLETO + VISUALIZACIÓN CRUZADA)
            # ==========================================================================
            if modo == "VIVIENDA_TOTAL":
                st.subheader("🏡 Gestión Inmobiliaria")
                st.caption("Calculadora Cruzada: Compra (Izq) y Venta (Der). Los resultados aparecen en el lado opuesto.")
                
                # Variables de memoria específicas
                if "viv_res_compra" not in st.session_state: st.session_state.viv_res_compra = ""
                if "viv_res_venta" not in st.session_state: st.session_state.viv_res_venta = ""

                # DOS COLUMNAS DE ANCHO COMPLETO
                col_izq, col_der = st.columns(2, gap="small")

                # --- COLUMNA IZQUIERDA: INPUTS COMPRA + VISOR VENTA ---
                with col_izq:
                    st.info("🛒 **DATOS COMPRA** (Resultado saldrá 👉)")
                    with st.container(border=True):
                        c_p1, c_p2 = st.columns(2)
                        with c_p1: precio_c = st.number_input("Precio (€)", value=150000.0, step=1000.0, key="viv_com_pre")
                        with c_p2: tipo_c = st.selectbox("Tipo", ["Segunda Mano", "Obra Nueva"], key="viv_com_tipo")
                        
                        ccaa_c = st.selectbox("CCAA", ["Madrid", "Cataluña", "Andalucía", "Valencia", "Galicia", "Castilla-La Mancha", "Castilla y León", "Canarias", "Otras"], key="viv_com_ccaa")
                        
                        st.markdown("👇 **Perfil Compradores:**")
                        c_perf1, c_perf2 = st.columns(2)
                        with c_perf1:
                            edad_joven = st.number_input("Edad (Joven)", 18, 99, 30, key="viv_com_edad")
                            es_habitual = st.checkbox("Vivienda Habitual", value=True, key="viv_com_hab")
                        with c_perf2:
                            num_compradores = st.number_input("Nº Compradores", 1, 5, 1, key="viv_com_num")
                            es_fam_num = st.checkbox("Fam. Numerosa", key="viv_com_fn")
                            es_discap = st.checkbox("Discapacidad", key="viv_com_dis")

                        if st.button("🧮 CALCULAR GASTOS TOTALES", key="btn_viv_com"):
                            with st.spinner("Calculando impuestos regionales y aranceles notariales..."):
                                prompt_compra = f"""
                                Actúa como experto inmobiliario y fiscal en España.
                                Calcula los GASTOS DE COMPRAVENTA para:
                                - Precio: {precio}€
                                - Región: {ccaa}
                                - Tipo: {tipo}
                                
                                DESGLOSE OBLIGATORIO:
                                1. Impuestos: Si es Segunda Mano calcula el ITP de {ccaa}. Si es Obra Nueva calcula IVA (10%) + AJD de {ccaa}.
                                2. Notaría (Estimación aranceles BOE).
                                3. Registro de la Propiedad (Estimación).
                                4. Gestoría (Aproximado 300-500€).
                                
                                TOTAL A PREPARAR: Suma todo.
                                """
                                st.session_state.generated_calc = groq_engine(prompt_compra, api_key)
                                st.rerun() 

                    # Visor de Venta (viene de la derecha)
                    if st.session_state.viv_res_venta:
                        st.write("")
                        st.success("⬅️ **RESULTADO DE LA VENTA**")
                        st.markdown(f"<div class='contract-box' style='font-size:13px;'>{st.session_state.viv_res_venta}</div>", unsafe_allow_html=True)

                # --- COLUMNA DERECHA: INPUTS VENTA + VISOR COMPRA ---
                with col_der:
                    st.warning("💰 **DATOS VENTA** (Resultado saldrá 👈)")
                    with st.container(border=True):
                        p_venta = st.number_input("Venta (€)", value=180000.0, step=1000.0, key="viv_ven_pv")
                        p_compra = st.number_input("Compra (€)", value=100000.0, step=1000.0, key="viv_ven_pc")
                        anio_c = st.number_input("Año Adquisición", 1990, 2025, 2010, key="viv_ven_ac")
                        v_suelo = st.number_input("Valor Suelo IBI (€)", 0.0, step=500.0, key="viv_ven_vs")
                        municipio = st.text_input("Municipio", key="viv_ven_mun")

                        if st.button("🧮 CALCULAR IMPUESTOS VENTA", key="btn_viv_ven"):
                            if v_suelo > 0:
                                with st.spinner("Calculando Plusvalía y 'Hachazo' de Hacienda..."):
                                    anios = anio_actual - f_compra
                                    ganancia = p_venta - p_compra
                                    prompt_venta = f"""
                                    Actúa como asesor fiscal en España.
                                    Calcula los impuestos por VENTA DE VIVIENDA en {municipio}.
                                    - Años tenencia: {anios}.
                                    - Ganancia Bruta: {ganancia}€ (Venta {p_venta} - Compra {p_compra}).
                                    - Valor Catastral Suelo: {v_suelo}€.
                                    
                                    INFORME:
                                    1. PLUSVALÍA MUNICIPAL: Estima el coste (Método Objetivo vs Real). ¿Hay ganancia?
                                    2. IRPF (ESTATAL): Calcula la cuota a pagar por la Ganancia Patrimonial (Tramos del ahorro 19%-28%).
                                    3. TOTAL A PAGAR APROXIMADO.
                                    """
                                    st.session_state.generated_calc = groq_engine(prompt_venta, api_key)
                            else:
                                st.warning("⚠️ Necesitas el Valor Catastral del Suelo (míralo en el IBI) para calcular la Plusvalía.")

                    # Visor de Compra (viene de la izquierda)
                    if st.session_state.viv_res_compra:
                        st.write("")
                        st.info("➡️ **RESULTADO DE LA COMPRA**")
                        st.markdown(f"<div class='contract-box' style='font-size:13px;'>{st.session_state.viv_res_compra}</div>", unsafe_allow_html=True)


            # ==========================================================================
            # CASO GENERAL: RESTO DE HERRAMIENTAS (LAYOUT DIVIDIDO 1 | 1.3)
            # ==========================================================================
            else:
                # Creamos columnas solo para estas herramientas
                c_cal, c_res = st.columns([1, 1.3])
                
                # COLUMNA IZQUIERDA (FORMULARIOS)
                with c_cal:
                    
                    # === RENTA (COMPLETO) ===
                    if modo == "RENTA":
                        st.subheader("💰 Deducciones Renta")
                        st.info("💡 **Buscador de Ahorro:** Detecta deducciones por familia, alquiler, vivienda y personas a cargo.")
                        
                        ccaa = st.selectbox("📍 Tu Comunidad Autónoma", ["Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria", "Castilla-La Mancha", "Castilla y León", "Cataluña", "Extremadura", "Galicia", "Madrid", "Murcia", "La Rioja", "Valencia"], key="ren_ccaa")
                        
                        # Situación Personal
                        st.markdown("👇 **Tu Situación Personal:**")
                        c_est1, c_est2 = st.columns(2)
                        with c_est1:
                            estado_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Pareja de Hecho", "Divorciado/Separado", "Viudo/a"], key="ren_ec")
                        
                        info_civil_extra = ""
                        with c_est2:
                            discapacidad_propia = st.checkbox("Tengo Discapacidad (>33%)", key="ren_dis")
                            if estado_civil == "Casado/a":
                                if st.checkbox("¿Declaración Conjunta?", key="ren_conj"):
                                    info_civil_extra += " Opción Declaración Conjunta. "
                            elif estado_civil == "Pareja de Hecho":
                                if st.checkbox("¿Hijos en común?", key="ren_ph_hijos"):
                                    info_civil_extra += " Pareja de Hecho con Hijos (Valorar Monoparental). "
                            elif estado_civil == "Divorciado/Separado":
                                paga_comp = st.checkbox("Pago Pensión Compensatoria (Ex-cónyuge)", key="ren_div_comp")
                                paga_alim = st.checkbox("Pago Anualidades Alimentos (Hijos)", key="ren_div_alim")
                                if paga_comp: info_civil_extra += " Paga Pensión Compensatoria (Reduce Base). "
                                if paga_alim: info_civil_extra += " Paga Alimentos a Hijos (Escala especial). "

                        st.markdown("---")
                        # Familia
                        st.markdown("👇 **Familia y Personas a Cargo:**")
                        hijos = st.checkbox("👶 Tengo hijos (< 25 años)", key="ren_hijos")
                        detalles_familia = ""
                        
                        if hijos:
                            st.markdown("""<div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border-left: 3px solid #3b82f6; margin-bottom: 10px;"><small>📝 Hijos / Descendientes:</small></div>""", unsafe_allow_html=True)
                            anios_hijos = st.text_input("Año nacimiento hijos (ej: 2021, 2024)", key="ren_ah")
                            
                            c_h1, c_h2 = st.columns(2)
                            with c_h1:
                                guarderia = st.checkbox("Gastos Guardería (0-3 años)", key="ren_guar")
                                material = st.checkbox("Gastos Material Escolar", key="ren_mat")
                            with c_h2:
                                fam_num = st.checkbox("Familia Numerosa", key="ren_fam")
                                discap_hijo = st.checkbox("Hijo con Discapacidad", key="ren_dis_h")
                            
                            if estado_civil != "Casado/a":
                                if st.checkbox("¿Tienes la Custodia Exclusiva?", key="ren_custodia"):
                                    info_civil_extra += " Familia Monoparental (Custodia Exclusiva). "

                            detalles_familia += f"Hijos nacidos en: {anios_hijos}. "
                            if guarderia: detalles_familia += "Paga Guardería. "
                            if material: detalles_familia += "Paga Material Escolar. "
                            if fam_num: detalles_familia += "Es Familia Numerosa. "
                            if discap_hijo: detalles_familia += "Tiene hijos con Discapacidad (Aumenta mínimo). "

                        # Ascendientes
                        ascendientes = st.checkbox("👵 Ascendientes a cargo (>65 años o discapacidad)", key="ren_asc")
                        if ascendientes:
                            st.markdown("""<div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border-left: 3px solid #f59e0b; margin-bottom: 10px;"><small>📝 Padres/Abuelos que conviven contigo:</small></div>""", unsafe_allow_html=True)
                            c_asc1, c_asc2 = st.columns(2)
                            with c_asc1:
                                num_asc = st.number_input("Nº Ascendientes", 1, 4, 1, key="ren_num_asc")
                            with c_asc2:
                                asc_discap = st.checkbox("¿Tienen discapacidad > 33%?", key="ren_asc_dis")
                            
                            detalles_familia += f"Convive con {num_asc} ascendientes (>65 años). "
                            if asc_discap: detalles_familia += "Ascendientes con Discapacidad (Deducción muy alta). "

                        st.markdown("---")
                        # Gastos Deducibles
                        st.markdown("👇 **Gastos Deducibles:**")
                        c1, c2 = st.columns(2)
                        with c1:
                            alquiler = st.checkbox("Vivo de alquiler (Inquilino)", key="ren_alq")
                            if alquiler:
                                edad_inquilino = st.number_input("Tu edad", 18, 99, 30, key="ren_edad_inq")
                                detalles_familia += f" Inquilino de {edad_inquilino} años. "
                            hipoteca = st.checkbox("Hipoteca (Anterior 2013)", key="ren_hip")
                        with c2:
                            donaciones = st.checkbox("Hago Donaciones (ONG/Partidos)", key="ren_don")
                            idiomas = st.checkbox("Gastos Idiomas / Extraescolares", key="ren_idio")
                            rural = st.checkbox("Vivo en Zona Rural / Despoblada", key="ren_rur")
                        
                        otros = st.text_input("Otros gastos (Ej: Eficiencia energética, Transporte...)", key="ren_otr")

                        if st.button("🔍 BUSCAR DEDUCCIONES", key="btn_ren"):
                            with st.spinner(f"Analizando normativa de {ccaa} y estatal..."):
                                situaciones = []
                                situaciones.append(f"ESTADO CIVIL: {estado_civil}. {info_civil_extra}")
                                if detalles_familia: situaciones.append(f"SITUACIÓN FAMILIAR: {detalles_familia}")
                                else: situaciones.append("Sin cargas familiares declaradas.")
                                
                                if alquiler: situaciones.append("Vive de Alquiler")
                                if hipoteca: situaciones.append("Paga Hipoteca (Deducción estatal antigua)")
                                if discapacidad_propia: situaciones.append("Contribuyente con Discapacidad")
                                if donaciones: situaciones.append("Hace Donaciones")
                                if idiomas: situaciones.append("Gastos Educación/Idiomas")
                                if rural: situaciones.append("Residencia en zona Rural (Despoblación)")
                                if otros: situaciones.append(f"Otros: {otros}")
                                
                                perfil_txt = " | ".join(situaciones)
                                
                                prompt_renta = f"""
                                Actúa como Asesor Fiscal experto en IRPF España (Campaña actual).
                                Analiza las deducciones Autonómicas de: {ccaa} y Estatales clave.
                                PERFIL: {perfil_txt}.
                                TAREA: Lista deducciones aplicables (Hijos, Alquiler, Discapacidad, Ascendientes, Pensiones, etc).
                                FORMATO: ### ✅ DEDUCCIONES DETECTADAS.
                                """
                                st.session_state.generated_calc = groq_engine(prompt_renta, api_key)


                    # === ESCÁNER NÓMINA ===
                    elif modo == "ESCANER":
                        st.subheader("🔍 Escáner de Nómina")
                        st.info("📸 Sube una foto o PDF de tu nómina. La IA revisará si el IRPF es correcto y si cumples con el SMI 2026.")
                        file_nomina = st.file_uploader("Subir Nómina", type=["pdf", "jpg", "png"], key="u_nomina")
                        if file_nomina:
                            if st.button("🚀 ANALIZAR MI NÓMINA", key="btn_scan_nom"):
                                with st.spinner("Revisando conceptos salariales y retenciones..."):
                                    if file_nomina.type == "application/pdf": txt = extract_text_from_pdf(file_nomina)
                                    else: txt = analyze_image_groq(file_nomina, "Transcribe conceptos y retenciones.", api_key)
                                    p_nomina = f"Analiza esta nómina: {txt}. Verifica SMI 2026, IRPF correcto y Bases Cotización."
                                    st.session_state.generated_calc = groq_engine(p_nomina, api_key)


                    # === SUELDO NETO (COMPLETO) ===
                    elif modo == "SUELDO":
                        st.subheader("💶 Simulador Sueldo Neto")
                        st.caption("Simulador Nómina (IA Fiscal + Precisión Matemática)")
                        
                        bruto = st.number_input("Bruto Anual (€)", value=24000.0, step=500.0, key="su_bru")
                        edad = st.number_input("Edad", 18, 70, 30, key="su_edad")
                        comunidad = st.selectbox("CCAA (Define el IRPF)", ["Madrid", "Cataluña", "Andalucía", "Valencia", "Galicia", "País Vasco", "Canarias", "Resto"], key="su_ccaa")
                        movilidad = st.checkbox("¿Movilidad Geográfica?", key="su_mov")
                        
                        st.markdown("---")
                        c_fam1, c_fam2 = st.columns(2)
                        with c_fam1: 
                            estado = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Pareja de hecho", "Divorciado/Separado"], key="su_est")
                            conyuge_cargo = False
                            pension_alim = 0.0
                            pension_comp = 0.0
                            hijos_comun_pareja = False
                            
                            if estado == "Casado/a": 
                                conyuge_cargo = st.checkbox("¿Cónyuge gana < 1.500€/año?", key="su_con")
                            elif estado == "Pareja de hecho":
                                hijos_comun_pareja = st.checkbox("¿Tenéis hijos en común?", help="Importante para prorratear la deducción por descendientes.", key="su_pareja_hijos")
                            elif estado == "Divorciado/Separado":
                                paga_pension = st.checkbox("¿Pagas pensión por sentencia?", key="su_pen_check")
                                if paga_pension:
                                    pension_alim = st.number_input("Pensión Alimentos Hijos (€/año)", 0.0, step=500.0, key="su_pen_alim")
                                    pension_comp = st.number_input("Pensión Compensatoria Cónyuge (€/año)", 0.0, step=500.0, key="su_pen_comp")

                        with c_fam2: 
                            discapacidad = st.selectbox("Discapacidad", ["Ninguna", "33%-65%", ">65%"], key="su_dis")
                        
                        hijos = st.number_input("Nº Hijos (<25 años)", 0, 10, 0, key="su_hij")
                        hijos_menores_3 = 0
                        if hijos > 0: 
                            hijos_menores_3 = st.number_input(f"De los {hijos}, ¿cuántos < 3 años?", 0, hijos, 0, key="su_hij3")
                        
                        if st.button("💶 CALCULAR NETO EXACTO", key="btn_su_calc"):
                            with st.spinner("Calculando IRPF 2025 según situación familiar..."):
                                prompt_irpf = f"""
                                Actúa como experto fiscal en España 2025. Calcula TIPO MEDIO IRPF (%) para:
                                Bruto: {bruto}€. Región: {comunidad}. Edad: {edad}. Estado: {estado}.
                                Pensiones (reducen base): Alimentos {pension_alim}, Compensatoria {pension_comp}.
                                Hijos: {hijos} (<3 años: {hijos_menores_3}). Discapacidad: {discapacidad}.
                                INSTRUCCIÓN: Responde SOLO con el número del porcentaje (ej: 14.20).
                                """
                                try:
                                    respuesta_ia = groq_engine(prompt_irpf, api_key, temp=0.0)
                                    import re
                                    match = re.search(r"(\d+[.,]\d+)", respuesta_ia)
                                    tipo_irpf = float(match.group(1).replace(",", ".")) if match else 15.0
                                except: tipo_irpf = 15.0

                                ss_anual = bruto * 0.0635
                                irpf_anual = bruto * (tipo_irpf / 100)
                                neto_anual = bruto - ss_anual - irpf_anual
                                mes_12 = neto_anual / 12
                                mes_14 = neto_anual / 14 
                                
                                # Formateo visual
                                f_mes_12 = "{:,.2f}".format(mes_12).replace(",", "X").replace(".", ",").replace("X", ".")
                                f_mes_14 = "{:,.2f}".format(mes_14).replace(",", "X").replace(".", ",").replace("X", ".")
                                f_irpf = "{:,.2f}".format(irpf_anual/12).replace(",", "X").replace(".", ",").replace("X", ".")
                                f_tipo = "{:,.2f}".format(tipo_irpf).replace(",", "X").replace(".", ",").replace("X", ".")

                                html_nomina = f"""
                                <div style="background-color: rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;">
                                    <div style="font-size: 14px; font-weight: bold; color:#ccc;">Neto Mensual (12 pagas)</div>
                                    <div style="color: #38bdf8; font-size: 48px; font-weight: 900;">{f_mes_12} €</div>
                                    <div style="margin-top: 15px; border-top: 1px dashed #ccc; padding-top: 10px;">
                                        <div style="font-size: 14px; color:#ccc;">Neto Mensual (14 pagas)</div>
                                        <div style="color: #fff; font-size: 28px; font-weight: 700;">{f_mes_14} €</div>
                                    </div>
                                    <div style="background: rgba(0,0,0,0.3); margin-top: 20px; padding: 10px; border-radius: 8px;">
                                        <div>IRPF: <span style="color:#f87171;">-{f_irpf} €/mes</span> (Tipo: {f_tipo}%)</div>
                                    </div>
                                </div>
                                """
                                st.session_state.generated_calc = html_nomina

                    # === IPC ===
                    elif modo == "IPC":
                        st.subheader("📈 Actualizar IPC")
                        renta = st.number_input("Renta (€)", 800.0, key="ipc_ren")
                        mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="ipc_mes")
                        if st.button("📈 ACTUALIZAR", key="btn_ipc"):
                            st.session_state.generated_calc = groq_engine(f"Actualiza renta {renta} con IPC {mes}.", api_key)

                    # === HIPOTECA ===
                    elif modo == "HIPOTECA":
                        st.subheader("📉 Cuota Hipoteca")
                        st.caption("Calculadora Cuota Mensual Inteligente")
                        capital_h = st.number_input("Capital Pendiente (€)", value=150000.0, key="hip_cap")
                        plazo_h = st.number_input("Plazo (Años)", value=25, key="hip_pla")
                        t_interes = st.radio("Tipo de Interés", ["Fijo", "Variable"], horizontal=True, key="hip_tip")
                        
                        if t_interes == "Fijo":
                            interes_final = st.number_input("Interés Nominal Anual (%)", value=3.0, key="hip_int")
                        else:
                            eur_actual = 2.6 # Simulado
                            st.success(f"📈 Euríbor hoy: **{eur_actual}%**")
                            dif_banco = st.number_input("Diferencial del banco (%)", value=0.75, key="hip_dif")
                            interes_final = eur_actual + dif_banco
                            st.caption(f"Interés total aplicado: {interes_final}%")

                        if st.button("🧮 CALCULAR CUOTA", key="btn_hip"):
                            p_h = f"Calcula hipoteca. Capital: {capital_h}€. Interés total: {interes_final}%. Plazo: {plazo_h} años. Indica cuota mensual y total intereses."
                            st.session_state.generated_calc = groq_engine(p_h, api_key)


                # COLUMNA DERECHA (RESULTADOS COMUNES)
                with c_res:
                    if st.session_state.generated_calc:
                        if "<div" in st.session_state.generated_calc and "rgba" in st.session_state.generated_calc:
                            st.markdown(st.session_state.generated_calc, unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='contract-box' style='background:#f0f9ff; border-color:#bae6fd;'>{st.session_state.generated_calc}</div>", unsafe_allow_html=True)
                        st.write("")
                        with st.container(border=False):
                            ce3, cb3 = st.columns([2,1])
                            with ce3: m3 = st.text_input("Email", key="mf_tab4")
                            with cb3: 
                                st.write(""); st.write("")
                                if st.button("PDF RESULTADO", key="btn_pdf_tab4"):
                                    pdf_calc = create_pdf(st.session_state.generated_calc, "Informe Fiscal")
                                    if m3: save_lead(m3, "CALCULO", "Fiscalidad")
                                    st.download_button("⬇️ Bajar PDF", data=pdf_calc, file_name="Calculo.pdf", mime="application/pdf")
# --- PIE DE PÁGINA (FOOTER) ALINEADO Y CORREGIDO ---
st.write(""); st.write(""); st.write("") 

with st.container():
    st.markdown("---") 
    
    # Alineación vertical centrada
    c_legal, c_coffee, c_contact, c_admin = st.columns([3, 1.2, 1.2, 0.5], vertical_alignment="center")
    
    # 1. DATOS LEGALES (Tus datos)
    with c_legal:
        st.caption("⚖️ **legalapp.es** | Inteligencia Jurídica para España.")
        with st.expander("📜 Avisos Legales, Privacidad y Cookies"):
            st.markdown("""
            **Información Legal (LSSI):**
            Responsable: Marcos Lorente Diaz-Guerra | DNI: 46994385A 
            Email: marcoslorente@legalapp.es
            
            **Política de Privacidad (RGPD):**
            1. **Finalidad:** Los datos y documentos se procesan exclusivamente para generar el informe o contrato solicitado.
            2. **Conservación:** No almacenamos documentos personales de forma permanente. Los textos se procesan de forma efímera a través de la API de Groq (anónima).
            3. **Derechos:** Puede ejercer sus derechos de acceso, rectificación o supresión escribiendo a nuestro email de contacto.
            
            **Términos de Uso:**
            Esta herramienta utiliza Inteligencia Artificial. Los resultados son orientativos y no constituyen un consejo legal vinculante. Se recomienda la revisión por un abogado colegiado para procesos judiciales.
            """)

    # 2. BUY ME A COFFEE (Botón HTML Amarillo - Tooltip Nativo)
    with c_coffee:
        # Usamos HTML 'title' que el navegador muestra correctamente siempre
        st.markdown(
            """
            <a href="https://www.buymeacoffee.com/TU_USUARIO" target="_blank" style="text-decoration:none;" title="☕ Apoya el mantenimiento de la App">
                <div style="
                    background-color: #FFDD00; 
                    color: #000000; 
                    padding: 7px 15px; 
                    border-radius: 8px; 
                    text-align: center; 
                    font-weight: bold;
                    font-size: 14px;
                    border: 1px solid #eab308;
                    box-shadow: 0px 2px 0px 0px #c29606;
                    transition: 0.2s;
                    display: flex; align-items: center; justify-content: center;
                ">
                    ☕ Invitar Café
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    # 3. CONTACTO (Botón Streamlit Estándar)
    with c_contact:
        st.link_button("✉️ Soporte", "mailto:marcoslorente@legalapp.es", use_container_width=True)
            
    # 4. ADMIN
    with c_admin:
        with st.popover("🔐"):
            pass_admin = st.text_input("Clave", type="password")
            if pass_admin == "admin123": 
                if st.button("🔄 Reiniciar App"):
                    st.session_state.clear()
                    st.rerun()



























































































