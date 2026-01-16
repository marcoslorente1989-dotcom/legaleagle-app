import streamlit as st
import streamlit.components.v1 as components
import pdfplumber
from groq import Groq
import os
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==============================================================================
# 1. CONFIGURACIÓN Y CLAVES
# ==============================================================================

# Intentar leer de Variable de Entorno (Render) o Secrets (Local)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        from streamlit.runtime.secrets import secrets_singleton
        if secrets_singleton.load_if_present():
            api_key = st.secrets.get("GROQ_API_KEY")
    except: pass

st.set_page_config(
    page_title="LegalEagle AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

    /* 1. ELIMINAR ESPACIO SUPERIOR (Subir el logo) */
    .block-container {
        padding-top: 1rem !important; /* Ajusta este número si quieres que suba más o menos */
        padding-bottom: 0rem !important;
    }

    /* 2. PESTAÑAS EN 2x2 PARA MÓVIL */
    @media only screen and (max-width: 600px) {
        div[data-baseweb="tab-list"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important; /* Fuerza las 2 columnas */
            gap: 8px !important;
            justify-content: center !important;
        }
        
        button[data-baseweb="tab"] {
            width: 100% !important;
            padding: 8px 4px !important;
            font-size: 10px !important; /* Un pelín más pequeño para que quepa bien */
            margin: 0 !important;
        }

        /* Ajuste de logo en móvil para que no coma pantalla */
        [data-testid="stImage"] img {
            max-width: 70% !important;
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
    }
    .contract-box * { color: #000000 !important; }
    .chat-user { background-color: #bfdbfe; color: #000000 !important; padding: 10px; border-radius: 15px 15px 0 15px; text-align: right; margin-bottom: 5px; }
    .chat-bot { background-color: #ffffff; color: #000000 !important; padding: 10px; border-radius: 15px 15px 15px 0; margin-bottom: 5px; }
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white !important; border: none; border-radius: 25px !important; 
        padding: 0.6rem 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* 9. OCULTAR UI NATIVA */
    header, [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    footer, [data-testid="stFooter"] { display: none !important; height: 0px !important; }
    section[data-testid="stSidebar"] { display: none !important; }

</style>
""", unsafe_allow_html=True)
# ==============================================================================
# 3. LÓGICA & FUNCIONES
# ==============================================================================

keys = ["contract_text", "analysis_report", "generated_contract", "generated_claim", "generated_calc", "defense_text"]
for k in keys:
    if k not in st.session_state: st.session_state[k] = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "analysis_done" not in st.session_state: st.session_state.analysis_done = False

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

def groq_engine(prompt, key, temp=0.1):
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

tabs = st.tabs(["🔍 1. ANALIZAR", "✍️ 2. CREAR CONTRATO", "🛡️ 3. RECLAMAR/RECURRIR", "🧮 4. IMPUESTOS"])

# --- TAB 1: ANALIZADOR ---
with tabs[0]:
    with st.container(border=True):
        st.subheader("Analizador de Documentos")
        st.caption("Sube un contrato (PDF o Foto) y la IA detectará riesgos, cláusulas abusivas y fechas clave automáticamente.")
        uploaded_file = st.file_uploader(" ", type=["pdf", "jpg", "png", "jpeg"], label_visibility="collapsed", key="u1")
    
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
                with st.container(border=True): st.markdown(st.session_state.analysis_report)
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
with tabs[1]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        with st.container(border=True):
            st.subheader("Generador de Contratos")
            st.caption("Selecciona el tipo de contrato y rellena los datos. La IA redactará un documento legal válido en España y listo para firmar.")
            
            tipo = st.selectbox("Documento", [
                "Alquiler Vivienda", 
                "Compraventa Vehículo", 
                "Contrato Trabajo",
                "Servicios Freelance", 
                "NDA (Confidencialidad)",
                "Compraventa Vivienda (Piso/Casa)",
                "Contrato de Arras",
                "Desistimiento / Cancelación"
            ])
            
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
            with st.container(border=True):
                ce, cb = st.columns([2,1])
                with ce: m = st.text_input("Email", key="mc")
                with cb: 
                    st.write(""); st.write("")
                    if st.button("PDF OFICIAL", key="bc"):
                        save_lead(m,"CREAR",tipo)
                        pdf_file = create_pdf(st.session_state.generated_contract, f"Contrato {tipo}")
                        st.success("Hecho")
                        st.download_button("⬇️ Bajar Archivo PDF", data=pdf_file, file_name=f"{tipo}.pdf", mime="application/pdf")

# --- TAB 3: RECLAMAR / RECURRIR (PROFESIONALIZADO) ---
with tabs[2]:
    modo = st.radio("Opción:", ["✍️ Redactar Burofax / Reclamación", "🛡️ Responder/Recurrir (Subir PDF/Foto)"], horizontal=True)
    c_rec, c_doc = st.columns([1, 1.3])
    
    if "Redactar" in modo:
        with c_rec:
            with st.container(border=True):
                st.subheader("Iniciar Reclamación")
                st.caption("Generador de Burofax y cartas certificadas con terminología jurídica para reclamar impagos o incidencias.")
                
                remitente = st.text_input("Tus Datos (Nombre, DNI, Dirección)")
                dest = st.text_input("Destinatario (Empresa/Persona y Dirección)")
                st.markdown("---")
                
                motivo = st.selectbox("Tipo de Reclamación", [
                    "Cobro Indebido / Facturas", "Seguros (Siniestros/Coberturas)", 
                    "Devolución Fianza Alquiler", "Banca (Comisiones/Tarjetas)",
                    "Transporte (Vuelos/Equipaje)", "Otro / Genérico"
                ])
                
                datos_clave = ""
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
                        1. Usa estructura formal de carta legal (Encabezado, Referencias, Cuerpo, Cierre).
                        2. Cita la legislación aplicable según el caso (Ej: Ley Contrato Seguro 50/1980, Ley General Defensa Consumidores, LAU, Reglamento Europeo, etc).
                        3. Establece un plazo de respuesta (ej: 7 días) antes de iniciar acciones judiciales.
                        4. Incluye coletilla de "Quedo a la espera de sus noticias...".
                        """
                        st.session_state.generated_claim = groq_engine(prompt_claim, api_key)

    else:
        with c_rec:
            with st.container(border=True):
                st.subheader("Generar Defensa")
                st.caption("Sube la multa o notificación que has recibido. Analizaremos los defectos de forma y redactaremos tu defensa.")
                st.info("Sube la carta o multa que has recibido.")
                uploaded_defense = st.file_uploader("Archivo (PDF/Foto)", type=["pdf", "jpg", "png"], key="u_def")
                mis_datos = st.text_input("Tus Datos (Nombre y DNI)")
                mis_argumentos = st.text_area("Tus Argumentos de defensa")
                
                if uploaded_defense:
                    if uploaded_defense.type == "application/pdf": st.session_state.defense_text = extract_text_from_pdf(uploaded_defense)
                    else:
                        with st.spinner("Leyendo imagen..."): st.session_state.defense_text = analyze_image_groq(uploaded_defense, "Transcribe esta notificación legal.", api_key)
                
                if st.button("⚖️ GENERAR RESPUESTA"):
                    if st.session_state.defense_text and mis_datos:
                        with st.spinner("Analizando puntos débiles y redactando defensa..."):
                            p_def = f"""
                            Actúa como abogado defensor. He recibido esta notificación:
                            ---
                            {st.session_state.defense_text[:4000]}
                            ---
                            MIS ARGUMENTOS: {mis_argumentos}
                            MIS DATOS: {mis_datos}
                            TAREA: Redacta un PLIEGO DE DESCARGOS o CARTA DE OPOSICIÓN formal.
                            Busca defectos de forma, cita jurisprudencia o leyes que me beneficien y mantén un tono respetuoso pero firme en la defensa.
                            """
                            st.session_state.generated_claim = groq_engine(p_def, api_key)
                    else: st.warning("Por favor sube el archivo y rellena tus datos.")

    with c_doc:
        if st.session_state.generated_claim:
            st.markdown(f"<div class='contract-box'>{st.session_state.generated_claim}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=True):
                ce2, cb2 = st.columns([2,1])
                with ce2: m2 = st.text_input("Email", key="mr")
                with cb2:
                    st.write(""); st.write("")
                    if st.button("PDF LEGAL", key="br"):
                        save_lead(m2, "RECLAMACION", "Burofax Generado")
                        pdf_claim = create_pdf(st.session_state.generated_claim, "Documento Legal")
                        st.download_button("⬇️ Bajar PDF", data=pdf_claim, file_name="Reclamacion.pdf", mime="application/pdf")

# --- TAB 4: IMPUESTOS ---
with tabs[3]:
    c_cal, c_res = st.columns([1, 1.3])
    with c_cal:
        with st.container(border=True):
            st.subheader("Calculadora Fiscal")
            st.caption("Calcula con precisión tu sueldo neto real, los impuestos por venta de vivienda o tu cuota hipotecaria actual.")
            tipo_calc = st.selectbox("Trámite", ["Venta Inmueble (Plusvalía+IRPF)", "Sueldo Neto (Nómina)", "Gastos Compraventa", "IPC Alquiler", "Cuota Hipoteca"])            
            anio_actual = datetime.now().year
            
            if "Venta" in tipo_calc:
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
                st.caption("Calculadora Cuota Mensual")
                capital = st.number_input("Capital Prestado (€)", value=200000.0)
                interes = st.number_input("Interés Anual (%)", value=3.5)
                plazo = st.number_input("Plazo (Años)", value=30)
                if st.button("🧮 CALCULAR CUOTA"):
                    st.session_state.generated_calc = groq_engine(f"Calcula hipoteca. Capital {capital}. Interés {interes}. Plazo {plazo}. Tabla amortización año 1.", api_key)

    with c_res:
        if st.session_state.generated_calc:
            if "<div" in st.session_state.generated_calc and "rgba" in st.session_state.generated_calc:
                st.markdown(st.session_state.generated_calc, unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='contract-box' style='background:#f0f9ff; border-color:#bae6fd;'>{st.session_state.generated_calc}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=True):
                ce3, cb3 = st.columns([2,1])
                with ce3: m3 = st.text_input("Email", key="mf")
                with cb3: 
                    st.write(""); st.write("")
                    if st.button("PDF RESULTADO", key="bf"):
                        save_lead(m3, "CALCULO", "Fiscalidad")
                        pdf_calc = create_pdf(st.session_state.generated_calc, "Informe Fiscal")
                        st.download_button("⬇️ Bajar PDF", data=pdf_calc, file_name="Calculo.pdf", mime="application/pdf")

# ==============================================================================
# 5. FOOTER (LEGAL & ADMIN OCULTO)
# ==============================================================================
st.write(""); st.write(""); st.write("") # Espacio para separar del contenido

# Contenedor final
with st.container():
    st.markdown("---") # Línea separadora sutil
    
    # Creamos columnas: Izquierda (Legal) - Derecha (Admin discreto)
    c_legal, c_admin = st.columns([6, 1])
    
    with c_legal:
        # Texto legal obligatorio pero discreto
        st.caption("⚖️ **Aviso Legal:** Herramienta de orientación legal basada en IA. No sustituye el asesoramiento de un abogado colegiado.")
        
        # Desplegable CON LOS CAMPOS RECUPERADOS
        with st.expander("📜 Ver Aviso Legal y Privacidad"):
            st.caption("""
            **1. Responsable:** Marcos Lorente Diaz-Guerra - 46994385A
            **2. Finalidad:** Gestión de herramientas legales y redacción asistida por IA.
            **3. Legitimación:** Consentimiento del usuario al usar la herramienta.
            **4. Destinatarios:** Los datos se procesan a través de APIs de terceros (Groq) de forma anónima y no se usan para entrenar modelos.
            **5. Derechos:** Acceder, rectificar y suprimir los datos escribiendo a marcoslorente1989@gmail.com.
            """)
            
    with c_admin:
        # EL TRUCO: Un botón "popover" que solo muestra el candado.
        # Al hacer clic, se abre el formulario flotante.
        # El CSS V95 se encargará de que las letras aquí dentro sean NEGRAS.
        with st.popover("🔐", help="Acceso Administrador"):
            st.markdown("### Panel Admin")
            pass_admin = st.text_input("Clave", type="password", key="admin_pass_footer")
            
            if pass_admin == "admin123": # <--- CAMBIA ESTO POR TU CLAVE
                st.success("Acceso OK")
                
                if st.button("📂 Descargar CSV Leads"):
                    if os.path.isfile("database_leads.csv"):
                        df_leads = pd.read_csv("database_leads.csv")
                        st.dataframe(df_leads)
                    else:
                        st.warning("No hay datos aún.")
                        
                if st.button("🔄 Reiniciar Web"):
                    st.session_state.clear()
                    st.rerun()








