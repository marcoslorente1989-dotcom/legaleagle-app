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

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, 'LegalEagle AI - Documento Oficial', align='C')
        self.ln(10)
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(15)
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()} | LegalEagle Suite', align='C')

def create_pdf(content, title="Documento"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(5)
    pdf.set_font("Times", size=11)
    # Codificación segura para PDF
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_content)
    return pdf.output(dest='S').encode('latin-1')

def groq_engine(prompt, key, temp=0.2):
    client = Groq(api_key=key)
    try:
        sys_msg = "Eres LegalEagle, abogado y asesor fiscal experto en España. Responde de forma directa, compacta y profesional. Cita leyes."
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
            sheet = client.open("Base de Datos LegalEagle").sheet1 
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
        st.markdown("<h1 style='text-align: center; color: white;'>🦅 LegalEagle AI</h1>", unsafe_allow_html=True)

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
   
# --- TAB 1: ANALIZADOR ---
with tabs[1]:
    with st.container(border=False):
        st.subheader("Analizador de Documentos")
        st.caption("Sube un contrato (PDF o Foto) y la IA detectará riesgos, cláusulas abusivas y fechas clave automáticamente.")
        uploaded_file = st.file_uploader(" ", type=["pdf", "jpg", "png", "jpeg"], label_visibility="collapsed", key="u1")

    st.write("---")
    st.markdown("💡 **¿Solo quieres revisar tu sueldo?**")
    if st.button("📊 Ir al Escáner de Nóminas Ahora"):
        # Cambiamos la selección en el selectbox de la otra pestaña antes de ir
        st.session_state.generated_calc = "" # Limpiamos cálculos previos
        
        # Inyectamos un pequeño script de JavaScript para hacer clic en la pestaña 4
        # Esta es la única forma real de cambiar de pestaña físicamente en Streamlit hoy
        components.html("""
            <script>
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                tabs[4].click(); 
            </script>
        """, height=0)
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            if st.session_state.contract_text == "":
                with st.spinner("Leyendo PDF..."):
                    st.session_state.contract_text = extract_text_from_pdf(uploaded_file)
        else:
            if st.session_state.contract_text == "":
                with st.spinner("Escaneando imagen..."):
                    st.session_state.contract_text = analyze_image_groq(uploaded_file, "Transcribe texto legal.", api_key)
        
        if st.session_state.contract_text:
            if not st.session_state.analysis_done:
                if st.button("🚀 ANALIZAR RIESGOS"):
                    with st.spinner("Analizando..."):
                        p = f"Analiza texto. Markdown emojis. 1.📊RESUMEN 2.🚨RIESGOS 3.💰OBLIGACIONES 4.📅FECHAS 5.⚖️VEREDICTO.\n\n{st.session_state.contract_text}"
                        st.session_state.analysis_report = groq_engine(p, api_key)
                        st.session_state.analysis_done = True
                        st.rerun()
            
            if st.session_state.analysis_done:
                with st.container(border=False): st.markdown(st.session_state.analysis_report)
                pdf_bytes = create_pdf(st.session_state.analysis_report, "Informe Riesgos")
                st.download_button("📄 Descargar Informe PDF", data=pdf_bytes, file_name="Informe_Legal.pdf", mime="application/pdf")
                
                st.write("")
                
                with st.expander("📅 GENERAR AVISO DE CANCELACIÓN / DESISTIMIENTO", expanded=False):
                    st.info("Crea un documento formal para cancelar este contrato basado en su contenido.")
                    c_cancel_mail, c_cancel_date = st.columns(2)
                    with c_cancel_mail: email_remitente = st.text_input("Tu Email / Identificación", key="email_cancel")
                    with c_cancel_date: fecha_cancel = st.date_input("Fecha efectiva de la baja", key="date_cancel")
                    
                    if st.button("✉️ Generar Carta de Cancelación"):
                        with st.spinner("Redactando aviso legal..."):
                            prompt_cancel = f"""
                            Actúa como abogado. Basándote en el contrato analizado: "{st.session_state.contract_text[:3000]}..."
                            Redacta una CARTA FORMAL DE DESISTIMIENTO o NO RENOVACIÓN.
                            Remitente: {email_remitente}. Fecha efectos: {fecha_cancel}.
                            El tono debe ser firme, legal y citando las cláusulas de terminación si existen en el texto.
                            """
                            aviso_texto = groq_engine(prompt_cancel, api_key)
                            st.markdown(f"<div class='contract-box'>{aviso_texto}</div>", unsafe_allow_html=True)
                            pdf_cancel = create_pdf(aviso_texto, "Carta Cancelacion")
                            save_lead(email_remitente, "CANCELACION_AUTO", "Desde Analizador")
                            st.download_button("⬇️ Descargar Carta PDF", data=pdf_cancel, file_name="Cancelacion.pdf", mime="application/pdf")

                st.write("")
                col_chat_title, col_chat_btn = st.columns([4, 1])
                with col_chat_title: st.markdown("### 💬 Chat Legal")
                with col_chat_btn: 
                    if st.button("🗑️ Borrar", help="Limpia solo el chat"):
                        st.session_state.chat_history = []
                        st.rerun()

                for m in st.session_state.chat_history:
                    css = "chat-user" if m["role"]=="user" else "chat-bot"
                    st.markdown(f"<div class='{css}'>{m['content']}</div>", unsafe_allow_html=True)
                if q:=st.chat_input("Pregunta sobre el contrato..."):
                    st.session_state.chat_history.append({"role":"user","content":q})
                    ans = groq_engine(f"Contexto: {st.session_state.contract_text}. Pregunta: {q}", api_key)
                    st.session_state.chat_history.append({"role":"assistant","content":ans})
                    st.rerun()

# --- TAB 2: CREADOR (DETALLADO) ---
with tabs[2]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        with st.container(border=False):
            st.subheader("Generador de Contratos")
            st.caption("Selecciona el tipo de contrato y rellena los datos. La IA redactará un documento legal válido en España y listo para firmar.")
            
            tipo = st.selectbox("Documento", [
                "Alquiler Vivienda", 
                "Préstamo entre Particulares", # NUEVA OPCIÓN
                "Compraventa Vehículo", 
                "Contrato Trabajo",
                "Servicios Freelance", 
                "NDA (Confidencialidad)",
                "Compraventa Vivienda (Piso/Casa)",
                "Contrato de Arras",
                "Desistimiento / Cancelación"
            ])
            st.markdown("<div id='prestamos'></div>", unsafe_allow_html=True)
            
            data_p = ""
            
             # --- LÓGICA DE CAMPOS ESPECÍFICOS ---
            if "Alquiler" in tipo: 
                st.caption("🏠 Datos del Alquiler")
                prop = st.text_input('Propietario (Nombre y DNI/CIF)')
                inq = st.text_input('Inquilino (Nombre y DNI/CIF)')
                dir_piso = st.text_input('Dirección completa')
                ref_cat = st.text_input('Referencia Catastral (Opcional)')
                renta = st.number_input('Renta Mensual (€)')
                data_p = f"Alquiler. Propietario: {prop}. Inquilino: {inq}. Piso: {dir_piso}. Ref. Catastral: {ref_cat}. Renta: {renta} euros/mes."

    
            elif "Préstamo" in tipo: # NUEVO BLOQUE
                st.info("💡 **Consejo:** Para evitar problemas con Hacienda, este contrato debe indicar si es con intereses y presentarse (exento) mediante el Modelo 600.")
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    pres_nombre = st.text_input("Prestamista (quien presta)")
                    pret_nombre = st.text_input("Prestatario (quien recibe)")
                with c_p2:
                    monto = st.number_input("Importe (€)", min_value=10)
                    es_gratuito = st.checkbox("¿Es un préstamo sin intereses?", value=True)
                interes_txt = "sin intereses (gratuito)" if es_gratuito else st.text_input("Tipo de interés %")
                data_p = f"Préstamo entre particulares. Prestamista: {pres_nombre}. Prestatario: {pret_nombre}. Importe: {monto}€. Intereses: {interes_txt}. Plazo devolución: A acordar."
                    
           
            elif "Vehículo" in tipo: 
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
            
            elif "Contrato Trabajo" in tipo:
                st.caption("👤 Las Partes")
                empresa = st.text_input("Empresa (Nombre y CIF)")
                trabajador = st.text_input("Trabajador (Nombre y DNI)")
                st.caption("💼 Condiciones Laborales")
                modalidad = st.selectbox("Modalidad", ["Indefinido", "Temporal (Duración Determinada)", "Sustitución"])
                duracion_txt = "Indefinida"
                if modalidad != "Indefinido":
                    duracion_txt = st.text_input("Duración / Fecha Fin", placeholder="Ej: 6 meses / Hasta el 31 de Diciembre")
                salario = st.number_input("Salario Bruto Anual (€)", min_value=15000.0, step=500.0)
                tiene_variable = st.checkbox("¿Incluye Variable / Bonus?")
                variable_txt = "Sin retribución variable."
                if tiene_variable:
                    cantidad_var = st.text_input("Detalles del Variable", placeholder="Ej: 10% sobre objetivos o 3.000€")
                    variable_txt = f"Con retribución variable: {cantidad_var}."
                data_p = f"Contrato de Trabajo. Modalidad: {modalidad}. Empresa: {empresa}. Trabajador: {trabajador}. Duración: {duracion_txt}. Salario Fijo: {salario}€ Brutos/Año. Variable: {variable_txt}. Convenio aplicable: Según sector."

            elif "NDA" in tipo: 
                data_p = f"Acuerdo Confidencialidad. Parte Reveladora: {st.text_input('Parte Reveladora (Nombre y CIF/DNI)')}. Parte Receptora: {st.text_input('Parte Receptora (Nombre y CIF/DNI)')}. Información a proteger: {st.text_area('Motivo/Información')}."
            
            elif "Compraventa Vivienda" in tipo:
                st.caption("👤 Intervinientes")
                vendedor = st.text_input('Vendedor (Nombre y DNI/CIF)')
                comprador = st.text_input('Comprador (Nombre y DNI/CIF)')
                st.caption("🏠 Inmueble")
                inmueble = st.text_input('Dirección Completa')
                ref_catastral = st.text_input('Referencia Catastral', help="Código de 20 caracteres")
                precio = st.number_input('Precio Venta (€)', step=1000.0)
                data_p = f"Compraventa Inmueble. Vendedor: {vendedor}. Comprador: {comprador}. Dirección: {inmueble}. Referencia Catastral: {ref_catastral}. Precio: {precio} euros. Se vende libre de cargas."
            
            elif "Arras" in tipo:
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
            
            elif "Cancelación" in tipo:
                data_p = f"Acuerdo de Terminación. Contrato a cancelar: {st.text_input('¿Qué contrato?')}. Partes: {st.text_input('Partes implicadas (Nombres y DNI/CIF)')}. Fecha Efectiva: {st.date_input('Fecha Fin')}."

            else: 
                data_p = f"{tipo}. Partes: {st.text_input('Partes (Nombres y DNI/CIF)')}. Detalles: {st.text_area('Detalles')}."
            
            st.write("")
            ciudad = st.text_input("📍 Ciudad de firma", value="Madrid")
            
            if st.button("✨ REDACTAR"):
                with st.spinner("Redactando..."):
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    instruccion = f"""
                    Redacta un contrato legal formal en España de tipo: {tipo}.
                    LUGAR Y FECHA: En {ciudad}, a {fecha_hoy}.
                    DATOS: {data_p}
                    
                    IMPORTANTE:
                    - Empieza indicando "En {ciudad}, a {fecha_hoy}".
                    - Identifica a las partes con sus DNI/CIF.
                    - Para LABORAL: Especifica modalidad, salario y si hay variable.
                    - Para INMUEBLES: Incluye Referencia Catastral.
                    - Para VEHÍCULOS: Incluye Bastidor y Kilómetros.
                    - Cita leyes vigentes (Estatuto Trabajadores, Código Civil, etc).
                    - Usa cláusulas claras y formato profesional.
                    """
                    st.session_state.generated_contract = groq_engine(instruccion, api_key, 0.3)
    
    with c2:
        if st.session_state.generated_contract:
            st.markdown(f"<div class='contract-box'>{st.session_state.generated_contract}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=False):
                ce, cb = st.columns([2,1])
                with ce: m = st.text_input("Email", key="mc")
                with cb: 
                    st.write(""); st.write("")
                    if st.button("PDF OFICIAL", key="bc"):
                        save_lead(m,"CREAR",tipo)
                        pdf_file = create_pdf(st.session_state.generated_contract, f"Contrato {tipo}")
                        st.success("Hecho")
                        st.download_button("⬇️ Bajar Archivo PDF", data=pdf_file, file_name=f"{tipo}.pdf", mime="application/pdf")

# --- TAB 3: RECLAMAR / RECURRIR (VERSIÓN COMPLETA Y BLINDADA) ---
with tabs[3]:
    st.subheader("Centro de Reclamaciones")
    st.caption("Genera burofaxes, responde cartas o recurre multas.")
    
    # 1. SELECTOR DE MODO (Solo una vez)
    modo = st.radio("Elige tu caso:", [
        "✍️ Redactar Burofax (Reclamar Dinero/Derechos)", 
        "🛡️ Responder Carta/Notificación (Vecinos, Seguros...)", 
        "👮 Recurrir Multa Tráfico (DGT/Ayto)"
    ], horizontal=True)
    
    c_rec, c_doc = st.columns([1, 1.3])
    
    # =========================================================
    # CASO A: REDACTAR BUROFAX (TODA TU LÓGICA COMPLETA)
    # =========================================================
    if "Redactar" in modo:
        with c_rec:
            with st.container(border=False):
                st.subheader("Datos del Burofax")
                st.caption("Rellena los campos para generar la reclamación legal.")
                
                remitente = st.text_input("Tus Datos (Nombre, DNI, Dirección)")
                dest = st.text_input("Destinatario (Empresa/Persona y Dirección)")
                st.markdown("---")
                
                motivo = st.selectbox("Tipo de Reclamación", [
                    "Cobro Indebido / Facturas", "Seguros (Siniestros/Coberturas)", 
                    "Devolución Fianza Alquiler", "Banca (Comisiones/Tarjetas)",
                    "Transporte (Vuelos/Equipaje)", "Otro / Genérico"
                ])
                
                datos_clave = ""
                
                # --- LÓGICA DETALLADA DE CAMPOS (RECUPERADA AL 100%) ---
                if "Facturas" in motivo:
                    c_fac1, c_fac2 = st.columns(2)
                    with c_fac1: num_fac = st.text_input("Nº Factura / Contrato")
                    with c_fac2: importe = st.number_input("Importe Reclamado (€)", min_value=0.0)
                    fecha_fac = st.date_input("Fecha de la factura")
                    datos_clave = f"Reclamación de Cantidad. Factura Nº: {num_fac}. Importe: {importe}€. Fecha: {fecha_fac}. Motivo: Cobro indebido o servicio no prestado."
                
                elif "Seguros" in motivo:
                    c_seg1, c_seg2 = st.columns(2)
                    with c_seg1: num_poliza = st.text_input("Nº Póliza (Obligatorio)")
                    with c_seg2: num_siniestro = st.text_input("Nº Siniestro (Opcional)")
                    fecha_sin = st.date_input("Fecha del Siniestro")
                    datos_clave = f"Reclamación a Aseguradora. Póliza Nº: {num_poliza}. Siniestro Nº: {num_siniestro}. Fecha Ocurrencia: {fecha_sin}. Exigencia de cumplimiento de contrato y cobertura."
                
                elif "Fianza" in motivo:
                    direccion = st.text_input("Dirección del Inmueble alquilado")
                    fecha_llaves = st.date_input("Fecha devolución llaves")
                    importe_fianza = st.number_input("Importe Fianza (€)", min_value=0.0)
                    datos_clave = f"Reclamación de Fianza. Inmueble: {direccion}. Fecha fin contrato: {fecha_llaves}. Importe retenido: {importe_fianza}€. Aplicación de la LAU."
                
                elif "Banca" in motivo:
                    producto = st.text_input("Producto (Cuenta/Tarjeta)")
                    concepto = st.text_input("Concepto reclamado (Ej: Comisión mantenimiento)")
                    importe = st.number_input("Importe (€)", min_value=0.0)
                    datos_clave = f"Reclamación Bancaria. Producto: {producto}. Concepto: {concepto}. Importe: {importe}€. Solicitud de retrocesión."
                
                elif "Transporte" in motivo:
                    vuelo = st.text_input("Nº Vuelo / Localizador")
                    incidencia = st.selectbox("Incidencia", ["Retraso > 3h", "Cancelación", "Pérdida Equipaje"])
                    datos_clave = f"Reclamación Transporte. Referencia: {vuelo}. Incidencia: {incidencia}. Solicitud de indemnización según Reglamento Europeo 261/2004."
                
                else: 
                    asunto = st.text_input("Asunto")
                    datos_clave = f"Reclamación Genérica. Asunto: {asunto}."

                st.write("")
                hechos = st.text_area("Descripción detallada de los hechos", placeholder="Explica brevemente qué ha pasado y qué exiges...")
                
                if st.button("🔥 GENERAR BUROFAX"):
                    with st.spinner("Redactando reclamación jurídica..."):
                        prompt_claim = f"""
                        Actúa como abogado experto en derecho civil y mercantil español.
                        Redacta un BUROFAX DE RECLAMACIÓN PRE-CONTENCIOSO (Tono formal, firme y amenazante legalmente).
                        REMITENTE: {remitente}
                        DESTINATARIO: {dest}
                        CONTEXTO: {datos_clave}
                        HECHOS DETALLADOS: {hechos}
                        INSTRUCCIONES:
                        1. Usa estructura formal de carta legal.
                        2. Cita la legislación aplicable según el caso (Ej: Ley Contrato Seguro, Ley General Defensa Consumidores, LAU, etc).
                        3. Establece un plazo de respuesta (7 días).
                        """
                        st.session_state.generated_claim = groq_engine(prompt_claim, api_key)
                        
                        # Auto-Scroll
                        js_scroll_up = """<script>var topAnchor = window.parent.document.getElementById('top-of-page'); if (topAnchor) { topAnchor.scrollIntoView({behavior: "smooth", block: "start"}); }</script>"""
                        components.html(js_scroll_up, height=0)

    # =========================================================
    # CASO B: RESPONDER CARTA (IA)
    # =========================================================
    elif "Responder" in modo:
        with c_rec:
            with st.container(border=False):
                st.info("📂 **Respuesta Universal:** Sube la carta recibida.")
                uploaded_gen = st.file_uploader("Sube la carta (PDF/Foto)", type=["pdf", "jpg", "png"], key="u_gen")
                mis_argumentos = st.text_area("¿Qué quieres responder?", placeholder="Ej: No estoy de acuerdo porque...")
                
                if st.button("📝 GENERAR RESPUESTA"):
                    if uploaded_gen and mis_argumentos:
                        with st.spinner("Analizando documento y redactando respuesta..."):
                            if uploaded_gen.type == "application/pdf": txt_gen = extract_text_from_pdf(uploaded_gen)
                            else: txt_gen = analyze_image_groq(uploaded_gen, "Lee esta carta.", api_key)
                            
                            p_gen = f"""
                            Actúa como abogado. He recibido esta notificación:
                            ---
                            {txt_gen[:4000]}
                            ---
                            QUIERO RESPONDER ESTO: {mis_argumentos}
                            TAREA: Redacta una carta formal de respuesta/alegaciones.
                            Cita leyes si aplica al contexto.
                            """
                            st.session_state.generated_claim = groq_engine(p_gen, api_key)
                            
                            js_scroll_up = """<script>var topAnchor = window.parent.document.getElementById('top-of-page'); if (topAnchor) { topAnchor.scrollIntoView({behavior: "smooth", block: "start"}); }</script>"""
                            components.html(js_scroll_up, height=0)
                    else: st.warning("Sube el archivo y tus argumentos.")

    # =========================================================
    # CASO C: RECURRIR MULTA (IA TRÁFICO)
    # =========================================================
    elif "Multa" in modo:
        with c_rec:
            with st.container(border=False):
                st.info("👮 **Especialista en Tráfico:** Busca defectos de forma.")
                uploaded_multa = st.file_uploader("Sube la Multa (PDF/Foto)", type=["pdf", "jpg", "png"], key="u_multa")
                tipo_multa = st.selectbox("Tipo", ["Tráfico (DGT/Ayto)", "Hacienda", "Otros"])
                mis_datos = st.text_input("Tus Datos (Nombre y DNI)", key="d_multa")
                
                if st.button("⚖️ ANALIZAR Y RECURRIR"):
                    if uploaded_multa and mis_datos:
                        with st.spinner("Auditando multa..."):
                            if uploaded_multa.type == "application/pdf": txt_multa = extract_text_from_pdf(uploaded_multa)
                            else: txt_multa = analyze_image_groq(uploaded_multa, "Lee esta multa entera.", api_key)
                            
                            p_multa = f"""
                            Actúa como Abogado experto en {tipo_multa}. Sanción recibida: ---{txt_multa[:5000]}---.
                            DATOS CLIENTE: {mis_datos}.
                            TAREA: Redacta PLIEGO DE DESCARGOS. Busca defectos forma (fechas, fotos, márgenes). Cita ley. Solicita nulidad.
                            """
                            st.session_state.generated_claim = groq_engine(p_multa, api_key)
                            
                            js_scroll_up = """<script>var topAnchor = window.parent.document.getElementById('top-of-page'); if (topAnchor) { topAnchor.scrollIntoView({behavior: "smooth", block: "start"}); }</script>"""
                            components.html(js_scroll_up, height=0)
                    else: st.warning("Faltan datos.")

    # =========================================================
    # VISOR DE RESULTADOS (COMÚN PARA LOS 3 MODOS)
    # =========================================================
    with c_doc:
        if st.session_state.generated_claim:
            st.markdown(f"<div class='contract-box'>{st.session_state.generated_claim}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=False):
                ce2, cb2 = st.columns([2,1])
                with ce2: m2 = st.text_input("Email (Opcional)", key="mr")
                with cb2:
                    st.write(""); st.write("")
                    if st.button("PDF LEGAL", key="br"):
                        save_lead(m2, "RECLAMACION", modo)
                        pdf_claim = create_pdf(st.session_state.generated_claim, "Documento Legal")
                        st.download_button("⬇️ Bajar PDF", data=pdf_claim, file_name="Documento_Legal.pdf", mime="application/pdf")

# --- TAB 4: IMPUESTOS ---
with tabs[4]:
    c_cal, c_res = st.columns([1, 1.3])
    with c_cal:
        with st.container(border=False):
            st.subheader("Calculadora Fiscal")
            st.caption("Calcula con precisión tu sueldo neto real, los impuestos por venta de vivienda o tu cuota hipotecaria actual.")
            tipo_calc = st.selectbox("Trámite", [
                "💰 DEDUCCIONES RENTA (Buscador de Ahorro)",
                "🔍 ESCÁNER DE NÓMINA (Foto/PDF)", 
                "Sueldo Neto (Nómina)", 
                "Venta Inmueble (Plusvalía+IRPF)", 
                "Gastos Compraventa", 
                "IPC Alquiler", 
                "Cuota Hipoteca"   
            ])
            anio_actual = datetime.now().year
            st.markdown("<div id='hipoteca'></div>", unsafe_allow_html=True)

            # --- A. LÓGICA RENTA (CON DETALLE HIJOS) ---
            if "RENTA" in tipo_calc:
                st.info("💡 **Buscador de Ahorro:** La IA filtrará las deducciones según tu perfil exacto.")
                ccaa = st.selectbox("📍 Tu Comunidad Autónoma", [
                    "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria", 
                    "Castilla-La Mancha", "Castilla y León", "Cataluña", "Extremadura", 
                    "Galicia", "Madrid", "Murcia", "La Rioja", "Valencia"
                ])
                st.markdown("👇 **Marca tu situación:**")
                
                # Sub-menú Hijos
                hijos = st.checkbox("👶 Tengo hijos (< 25 años)")
                detalles_hijos = ""
                if hijos:
                    st.markdown("""<div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border-left: 3px solid #3b82f6; margin-bottom: 10px;"><small>📝 Detalles para filtrar deducciones:</small></div>""", unsafe_allow_html=True)
                    anios_hijos = st.text_input("Año de nacimiento de cada hijo (ej: 2018, 2024)")
                    c_h1, c_h2 = st.columns(2)
                    with c_h1:
                        guarderia = st.checkbox("Gastos de Guardería (0-3 años)")
                        material = st.checkbox("Gastos Material Escolar / Libros")
                    with c_h2:
                        fam_mono = st.checkbox("Familia Monoparental / Numerosa")
                        discap_hijo = st.checkbox("Algún hijo con Discapacidad")
                    detalles_hijos = f"Tiene hijos nacidos en: {anios_hijos}. "
                    if guarderia: detalles_hijos += "Paga Guardería. "
                    if material: detalles_hijos += "Paga Material Escolar/Libros. "
                    if fam_mono: detalles_hijos += "Es Familia Monoparental/Numerosa. "
                    if discap_hijo: detalles_hijos += "Hijo con discapacidad. "

                st.markdown("---")
                c_chk1, c_chk2 = st.columns(2)
                with c_chk1:
                    alquiler = st.checkbox("Vivo de alquiler (Inquilino)")
                    hipoteca = st.checkbox("Hipoteca (Anterior 2013)")
                    discapacidad = st.checkbox("Mi Discapacidad (>33%)")
                with c_chk2:
                    donaciones = st.checkbox("Hago Donaciones")
                    idiomas = st.checkbox("Idiomas extraescolares")
                    rural = st.checkbox("Zona Rural / Despoblada")
                otros = st.text_input("Otros gastos (Ej: Eficiencia energética, Transporte...)")
                
                if st.button("🔍 BUSCAR DEDUCCIONES"):
                    situaciones = []
                    if hijos: situaciones.append(f"HIJOS: {detalles_hijos}")
                    else: situaciones.append("No tiene hijos.")
                    if alquiler: situaciones.append("Vive de Alquiler")
                    if hipoteca: situaciones.append("Paga Hipoteca")
                    if discapacidad: situaciones.append("Tiene Discapacidad propia")
                    if donaciones: situaciones.append("Hace Donaciones")
                    if idiomas: situaciones.append("Gastos Educación Idiomas")
                    if rural: situaciones.append("Residencia en zona Rural")
                    if otros: situaciones.append(f"Otros gastos: {otros}")
                    
                    perfil_txt = " | ".join(situaciones)
                    
                    prompt_renta = f"""
                    Actúa como Asesor Fiscal experto en IRPF España (Campaña 2024/2025).
                    PERFIL EXACTO: Residente en {ccaa}. SITUACIÓN: {perfil_txt}.
                    INSTRUCCIONES DE FILTRADO:
                    1. Analiza los AÑOS DE NACIMIENTO. Si nació antes de 2023, NO menciones deducción por nacimiento.
                    2. Si no hay 'Alquiler', NO hables de alquiler.
                    3. Si no hay 'Guardería' o el niño es mayor de 3 años, NO hables de guardería.
                    TAREA: Lista ÚNICAMENTE las deducciones aplicables REALMENTE.
                    FORMATO:✅ TUS DEDUCCIONES CONFIRMADAS (Iconos, Nombre, Cuantía, Casilla del modelo 100).
                    
                    ⚠️ REVISA ESTO POR SI ACASO
                    (Solo 1 o 2 deducciones muy famosas de {ccaa} que no haya marcado, brevemente).
                    """
                    st.session_state.generated_calc = groq_engine(prompt_renta, api_key)
                    
                    js_scroll_up = """
                        <script>
                            var topAnchor = window.parent.document.getElementById('top-of-page');
                            if (topAnchor) {
                                topAnchor.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
                            }
                        </script>
                    """
                    components.html(js_scroll_up, height=0)

            

            elif "ESCÁNER" in tipo_calc:
                st.info("📸 Sube una foto o PDF de tu nómina. La IA revisará si el IRPF es correcto y si cumples con el SMI 2026.")
                file_nomina = st.file_uploader("Subir Nómina", type=["pdf", "jpg", "png", "jpeg"], key="u_nomina")
                
                if file_nomina:
                    if st.button("🚀 ANALIZAR MI NÓMINA"):
                        with st.spinner("Revisando conceptos salariales y retenciones..."):
                            # Extraemos el texto según el formato
                            if file_nomina.type == "application/pdf":
                                texto_nomina = extract_text_from_pdf(file_nomina)
                            else:
                                texto_nomina = analyze_image_groq(file_nomina, "Transcribe todos los conceptos, bases de cotización y retenciones de esta nómina.", api_key)
                            
                            # Prompt específico para el "Semáforo Legal"
                            p_nomina = f"""
                            Actúa como asesor laboral experto en España (Año 2026). 
                            Analiza esta nómina: {texto_nomina}
                            
                            Genera un informe con este formato:
                            1. ✅/🚨 SMI: ¿El salario base y complementos llegan al SMI vigente?
                            2. ✅/🚨 IRPF: ¿La retención es adecuada para su sueldo anual bruto? (Evitar sustos en la Renta).
                            3. ✅/🚨 COTIZACIÓN: ¿Las bases de cotización concuerdan con el bruto?
                            4. 💡 RECOMENDACIÓN: ¿Debe el trabajador pedir un ajuste de retención?
                            
                            Usa un lenguaje muy claro y formato de 'Semáforo'.
                            """
                            st.session_state.generated_calc = groq_engine(p_nomina, api_key)
            
               # --- BLOQUE VENTA (Corregido con elif y alineación exacta) ---
            elif "Venta" in tipo_calc:
                st.caption("Plusvalía Municipal + IRPF")
                f_compra = st.number_input("Año Compra", 1950, anio_actual, 2015)
                p_compra = st.number_input("Precio Compra (€)", min_value=0.0)
                f_venta = st.number_input("Año Venta", value=anio_actual, disabled=True)
                p_venta = st.number_input("Precio Venta (€)", min_value=0.0)
                municipio = st.text_input("Municipio")
                v_suelo = st.number_input("Valor Catastral SUELO (€)", min_value=0.0)
                
                if st.button("🧮 CALCULAR IMPUESTOS"):
                    if v_suelo > 0:
                        anios = anio_actual - f_compra
                        ganancia = p_venta - p_compra
                        p = f"Calcula impuestos venta piso {municipio}. Años: {anios}. Valor Suelo: {v_suelo}. Ganancia: {ganancia}. 1. Plusvalía. 2. IRPF. Totales."
                        st.session_state.generated_calc = groq_engine(p, api_key)
            elif "Sueldo" in tipo_calc:
                st.caption("Simulador Nómina (IA Fiscal + Precisión Matemática)")
                bruto = st.number_input("Bruto Anual (€)", value=24000.0, step=500.0)
                edad = st.number_input("Edad", 18, 70, 30)
                comunidad = st.selectbox("CCAA (Define el IRPF)", ["Madrid", "Cataluña", "Andalucía", "Valencia", "Galicia", "País Vasco", "Canarias", "Resto"])
                movilidad = st.checkbox("¿Movilidad Geográfica?")
                st.markdown("---")
                c_fam1, c_fam2 = st.columns(2)
                with c_fam1: 
                    estado = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a"])
                    conyuge_cargo = False
                    if estado == "Casado/a": conyuge_cargo = st.checkbox("¿Cónyuge gana < 1.500€/año?")
                with c_fam2: discapacidad = st.selectbox("Discapacidad", ["Ninguna", "33%-65%", ">65%"])
                hijos = st.number_input("Nº Hijos (<25 años)", 0, 10, 0)
                hijos_menores_3 = 0
                if hijos > 0: hijos_menores_3 = st.number_input(f"De los {hijos}, ¿cuántos < 3 años?", 0, hijos, 0)
                
                if st.button("💶 CALCULAR NETO EXACTO"):
                    with st.spinner("Consultando normativa regional y calculando..."):
                        prompt_irpf = f"""
                        Actúa como experto fiscal en España 2025.
                        Calcula el TIPO MEDIO DE RETENCIÓN IRPF (%) para este perfil:
                        - Salario Bruto: {bruto}€
                        - Región: {comunidad}
                        - Edad: {edad}
                        - Hijos: {hijos}
                        - Discapacidad: {discapacidad}
                        - Cónyuge a cargo: {conyuge_cargo}
                        - Hijos < 3 años: {hijos_menores_3}
                        IMPORTANTE: Responde ÚNICAMENTE con el número del porcentaje con dos decimales.
                        Ejemplo de respuesta válida: 14.20
                        NO escribas texto, ni símbolos de porcentaje, solo el número.
                        """
                        try:
                            respuesta_ia = groq_engine(prompt_irpf, api_key, temp=0.0)
                            import re
                            match = re.search(r"(\d+[.,]\d+)", respuesta_ia)
                            if match: tipo_irpf = float(match.group(1).replace(",", "."))
                            else: tipo_irpf = 15.0
                        except: tipo_irpf = 15.0

                        ss_anual = bruto * 0.0635
                        irpf_anual = bruto * (tipo_irpf / 100)
                        neto_anual = bruto - ss_anual - irpf_anual
                        mes_12 = neto_anual / 12
                        mes_14 = neto_anual / 14 

                        f_mes_12 = "{:,.2f}".format(mes_12).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_mes_14 = "{:,.2f}".format(mes_14).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_irpf_mensual = "{:,.2f}".format(irpf_anual/12).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_tipo = "{:,.2f}".format(tipo_irpf).replace(",", "X").replace(".", ",").replace("X", ".")

                        html_nomina = f"""
                        <div style="background-color: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); color: #ffffff !important; padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; max-width: 500px; margin: auto;">
                            <div style="color: #94a3b8 !important; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold;">Neto Mensual (12 pagas)</div>
                            <div style="color: #38bdf8 !important; font-size: 48px; font-weight: 900; margin: 10px 0; line-height: 1; text-shadow: 0 0 20px rgba(56, 189, 248, 0.3);">{f_mes_12} €</div>
                            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px dashed rgba(255, 255, 255, 0.2);">
                                <div style="color: #94a3b8 !important; font-size: 14px; font-weight: bold;">Neto Mensual (14 pagas)</div>
                                <div style="color: #f1f5f9 !important; font-size: 28px; font-weight: 700;">{f_mes_14} €</div>
                            </div>
                            <div style="background-color: rgba(0, 0, 0, 0.3); margin-top: 25px; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; border: 1px solid rgba(255,255,255,0.05);">
                                <div style="text-align: center; width: 48%;">
                                    <div style="color: #cbd5e1 !important; font-size: 11px; font-weight: bold;">RETENCIÓN IRPF</div>
                                    <div style="color: #f87171 !important; font-size: 16px; font-weight: bold;">- {f_irpf_mensual} €/mes</div>
                                </div>
                                <div style="width: 1px; background-color: rgba(255, 255, 255, 0.2);"></div>
                                <div style="text-align: center; width: 48%;">
                                    <div style="color: #cbd5e1 !important; font-size: 11px; font-weight: bold;">TIPO APLICADO</div>
                                    <div style="color: #f87171 !important; font-size: 16px; font-weight: bold;">{f_tipo} %</div>
                                </div>
                            </div>
                            <div style="margin-top: 10px; font-size: 10px; color: #64748b !important;">*Cálculo basado en normativa autonómica de {comunidad}.</div>
                        </div>
                        """
                        st.session_state.generated_calc = html_nomina

                if st.session_state.generated_calc:
                     st.write("")
                     if st.button("🔄 Calcular de nuevo", use_container_width=True):
                         st.session_state.generated_calc = ""
                         st.rerun()

            elif "Compraventa" in tipo_calc:
                precio = st.number_input("Precio (€)", 150000.0)
                ccaa = st.selectbox("CCAA", ["Madrid", "Cataluña", "Andalucía", "Valencia", "Otras"])
                tipo = st.radio("Tipo", ["Segunda Mano", "Obra Nueva"])
                if st.button("🧮 CALCULAR"):
                    st.session_state.generated_calc = groq_engine(f"Gastos compraventa {ccaa}. Precio {precio}. Tipo {tipo}.", api_key)

            elif "IPC" in tipo_calc:
                renta = st.number_input("Renta (€)", 800.0)
                mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril"])
                if st.button("🧮 CALCULAR"):
                    st.session_state.generated_calc = groq_engine(f"Actualiza renta {renta}. Mes IPC {mes}.", api_key)
                    
           
            elif "Hipoteca" in tipo_calc:
                st.caption("Calculadora Cuota Mensual Inteligente")
                capital_h = st.number_input("Capital Pendiente (€)", value=150000.0)
                plazo_h = st.number_input("Plazo (Años)", value=25)
                
                # Lógica condicional Euribor/Interés
                t_interes = st.radio("Tipo de Interés", ["Fijo", "Variable"], horizontal=True)
                
                if t_interes == "Fijo":
                    interes_final = st.number_input("Interés Nominal Anual (%)", value=3.0)
                else:
                    eur_actual = obtener_euribor_actual()
                    st.success(f"📈 Euríbor hoy: **{eur_actual}%**")
                    dif_banco = st.number_input("Diferencial del banco (%)", value=0.75)
                    interes_final = eur_actual + dif_banco
                    st.caption(f"Interés total aplicado: {interes_final}%")

                if st.button("🧮 CALCULAR CUOTA"):
                    p_h = f"Calcula hipoteca. Capital: {capital_h}€. Interés total: {interes_final}%. Plazo: {plazo_h} años. Indica cuota mensual y total intereses."
                    st.session_state.generated_calc = groq_engine(p_h, api_key)
    with c_res:
        if st.session_state.generated_calc:
            if "<div" in st.session_state.generated_calc and "rgba" in st.session_state.generated_calc:
                st.markdown(st.session_state.generated_calc, unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='contract-box' style='background:#f0f9ff; border-color:#bae6fd;'>{st.session_state.generated_calc}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=False):
                ce3, cb3 = st.columns([2,1])
                with ce3: m3 = st.text_input("Email", key="mf")
                with cb3: 
                    st.write(""); st.write("")
                    if st.button("PDF RESULTADO", key="bf"):
                        save_lead(m3, "CALCULO", "Fiscalidad")
                        pdf_calc = create_pdf(st.session_state.generated_calc, "Informe Fiscal")
                        st.download_button("⬇️ Bajar PDF", data=pdf_calc, file_name="Calculo.pdf", mime="application/pdf")

# ==============================================================================
# 5. FOOTER (LEGAL & CONTACTO & ADMIN)
# ==============================================================================
st.write(""); st.write(""); st.write("") 

with st.container():
    st.markdown("---") 
    
    c_legal, c_contact, c_admin = st.columns([4, 2, 1])
    
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

    with c_contact:
        st.link_button("✉️ Contactar Soporte", "mailto:marcoslorente@legalapp.es")
            
    with c_admin:
        with st.popover("🔐", help="Admin"):
            pass_admin = st.text_input("Clave", type="password")
            if pass_admin == "admin123": 
                if st.button("🔄 Reiniciar App"):
                    st.session_state.clear()
                    st.rerun()

















