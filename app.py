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

# 1. Prioridad: Intentar leer de Variable de Entorno (Así funciona Render)
api_key = os.getenv("GROQ_API_KEY")

# 2. Si no la encuentra en el entorno, intentamos leer de st.secrets de forma segura
if not api_key:
    try:
        # Usamos .get() dentro de un try para que NO falle si no existe el archivo secrets.toml
        from streamlit.runtime.secrets import secrets_singleton
        if secrets_singleton.load_if_present():
            api_key = st.secrets.get("GROQ_API_KEY")
    except:
        pass

# 3. Si después de todo esto api_key sigue vacía, avisamos (pero no rompe la app)
if not api_key:
    # Puedes poner una clave por defecto vacía o gestionar el error más tarde
    print("⚠️ ADVERTENCIA: No se ha encontrado la GROQ_API_KEY.")


st.set_page_config(
    page_title="LegalEagle AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# SOLO MANTENEMOS EL TEXTO FANTASMA (PARA EL IDIOMA EN EDGE)
st.markdown("""
<div style="display:none; visibility:hidden; height:0;">
    Hola, esto es una aplicación en español de España. Contrato laboral, nómina,
    impuestos, seguridad social, irpf, sueldo neto, bruto, clausulas, legal,
    abogado, leyes, estatuto de los trabajadores, españa, madrid, barcelona.
    No traducir. Idioma español confirmado.
</div>
""", unsafe_allow_html=True)

# SCRIPT SENCILLO SOLO PARA FORZAR EL ATRIBUTO DE IDIOMA
components.html("""
    <script>
        const doc = window.parent.document;
        doc.documentElement.lang = 'es';
        doc.documentElement.setAttribute('translate', 'no');
        console.log("🦅 App lista en Render (Limpia).");
    </script>
""", height=0)
# ==============================================================================
# 2. ESTILOS CSS (V78: DISEÑO COMPLETO + RESPALDO ANTI-MARCA)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    /* 1. FONDO */
    .stApp { 
        background: linear-gradient(135deg, #1e40af 0%, #0f172a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* 2. TEXTOS GENERALES: BLANCO */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { color: #ffffff !important; }

    /* 3. INPUTS: NEGRO */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; 
        color: #000000 !important;
        caret-color: #000000;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
    }
    ul[data-baseweb="menu"] li { color: #000000 !important; background-color: #ffffff !important; }

    /* 4. CAJA DE SUBIDA (TRADUCIDA - ESTILO PC) */
    [data-testid="stFileUploader"] section {
        background-color: #f1f5f9 !important;
        border: 2px dashed #cbd5e1; border-radius: 15px; padding: 20px;
    }
    [data-testid="stFileUploader"] section > div > div > span, 
    [data-testid="stFileUploader"] section > div > div > small { display: none !important; }

    [data-testid="stFileUploader"] section > div > div::before {
        content: "📂 Arrastra tu PDF aquí para analizar";
        display: block; text-align: center; color: #334155; font-weight: 600; margin-bottom: 10px;
    }
    [data-testid="stFileUploader"] button {
        border-radius: 20px !important; border: 1px solid #94a3b8 !important;
        background-color: #e2e8f0 !important; color: transparent !important;
        position: relative; width: 160px; height: 40px;
    }
    [data-testid="stFileUploader"] button::after {
        content: "📄 Buscar Archivo"; color: #0f172a !important;
        position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
        font-weight: 600; width: 100%; font-size: 14px;
    }

   /* 5. PESTAÑAS (CENTRADAS Y SIN LÍNEA ROJA) */
    
    /* Centrar el grupo de pestañas en la pantalla */
    /* 5. PESTAÑAS (CENTRADO + SIN LÍNEA ROJA) */
    div[data-baseweb="tab-list"] {
        justify-content: center !important;
        gap: 10px;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    button[data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important; 
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 30px !important;
        padding: 10px 30px !important;
        margin-right: 0px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #3b82f6 !important; 
        font-weight: bold !important; 
        border-color: #60a5fa !important;
        transform: scale(1.05);
    }
    /* 6. OPTIMIZACIÓN MÓVIL 📱 */
    @media only screen and (max-width: 600px) {
        .block-container {
            padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 2rem !important;
        }
        button[data-baseweb="tab"] {
            padding: 6px 10px !important; font-size: 11px !important; margin-right: 2px !important; flex: 1 1 auto;
        }
        [data-testid="stFileUploader"] section > div > div::before {
            content: "📂 Subir PDF" !important; 
        }
        [data-testid="stImage"] img { max-width: 80% !important; margin: auto; }
    }

    /* 7. OTROS (CONTRATOS, CHAT, SIDEBAR, BOTONES) */
    .contract-box {
        font-family: 'Times New Roman', serif; background-color: #ffffff !important; 
        padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .contract-box, .contract-box * { color: #000000 !important; }

    .chat-user { background-color: #bfdbfe; color: #000000 !important; padding: 10px; border-radius: 15px 15px 0 15px; text-align: right; margin-bottom: 5px; }
    .chat-bot { background-color: #ffffff; color: #000000 !important; padding: 10px; border-radius: 15px 15px 15px 0; margin-bottom: 5px; }
    
    section[data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #e2e8f0 !important; }

    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white !important; border: none; border-radius: 25px !important; 
        padding: 0.6rem 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    div.stButton > button:hover {
        transform: scale(1.03); background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
    }

    /* --- 8. ZONA NUCLEAR (RESPALDO VISUAL) --- */
    
    /* Ocultar Barras y Menús Superiores */
    header, [data-testid="stHeader"], [data-testid="stToolbar"] { 
        display: none !important; 
        visibility: hidden !important; 
    }
    
    /* Ocultar Footer Estándar */
    footer, [data-testid="stFooter"] { 
        display: none !important; 
        visibility: hidden !important; 
        height: 0px !important;
    }
    
    /* ELIMINAR VIEWER BADGE (Doble seguridad: CSS + JS) */
    div[class*="viewerBadge"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important;
        display: none !important;
        opacity: 0 !important;
        pointer-events: none !important;
        z-index: -9999 !important;
        width: 0px !important;
        height: 0px !important;
        position: fixed !important;
        bottom: -100px !important;
    }

    #MainMenu { visibility: hidden !important; display: none !important; }
</style>
""", unsafe_allow_html=True)
# ==============================================================================
# 3. LÓGICA & MOTOR IA
# ==============================================================================

keys = ["contract_text", "analysis_report", "generated_contract", "generated_claim", "generated_calc", "defense_text"]
for k in keys:
    if k not in st.session_state: st.session_state[k] = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "analysis_done" not in st.session_state: st.session_state.analysis_done = False

# --- PROCESAMIENTO PDF ---
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extract = page.extract_text()
            if extract: text += extract + "\n"
    return text

# --- PROCESAMIENTO IMAGEN ---
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

# --- PDF ---
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
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_content)
    return pdf.output(dest='S').encode('latin-1')

# --- MOTOR TEXTO ---
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
    """Guarda el lead en Google Sheets (Si falla, no rompe la app)"""
    try:
        # 1. Leemos credenciales de Render
        json_creds = os.getenv("GOOGLE_CREDENTIALS")
        
        # 2. Conectamos
        if json_creds:
            creds_dict = json.loads(json_creds)
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            
            # 3. Escribimos en la hoja "Base de Datos LegalEagle"
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

# --- CABECERA LOGO ---
# Usamos columnas para centrar la imagen y que no ocupe el 100% del ancho (se vería enorme)
c_logo1, c_logo2, c_logo3 = st.columns([3, 2, 3]) 

with c_logo2:
    if os.path.isfile("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        # Fallback por si no encuentra la imagen
        st.markdown("<h1 style='text-align: center; color: white;'>🦅 LegalEagle AI</h1>", unsafe_allow_html=True)

st.write("") # Espacio separador
# ---------------------

if not api_key:
    st.error("⚠️ Falta API Key en secrets.toml")
    st.stop()

tabs = st.tabs(["🔍 1. ANALIZAR", "✍️ 2. CREAR CONTRATO", "🛡️ 3. RECLAMAR/RECURRIR", "🧮 4. IMPUESTOS"])

# --- TAB 1: ANALIZADOR ---
# --- TAB 1: ANALIZADOR (CON LA HERRAMIENTA DE CANCELACIÓN RECUPERADA) ---
with tabs[0]:
    with st.container(border=True):
        st.markdown("### 📤 Analizador de Documentos")
        st.caption("PDF o FOTO (OCR Inteligente)")
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
                # 1. EL INFORME
                with st.container(border=True): st.markdown(st.session_state.analysis_report)
                pdf_bytes = create_pdf(st.session_state.analysis_report, "Informe Riesgos")
                st.download_button("📄 Descargar Informe PDF", data=pdf_bytes, file_name="Informe_Legal.pdf", mime="application/pdf")
                
                st.write("")
                
                # --- HERRAMIENTA RECUPERADA: CANCELACIÓN ---
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
                            """
                            aviso_texto = groq_engine(prompt_cancel, api_key)
                            st.markdown(f"<div class='contract-box'>{aviso_texto}</div>", unsafe_allow_html=True)
                            pdf_cancel = create_pdf(aviso_texto, "Carta Cancelacion")
                            save_lead(email_remitente, "CANCELACION_AUTO", "Desde Analizador")
                            st.download_button("⬇️ Descargar Carta PDF", data=pdf_cancel, file_name="Cancelacion.pdf", mime="application/pdf")

                # 3. CHAT LEGAL
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

# --- TAB 2: CREADOR ---
with tabs[1]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        with st.container(border=True):
            st.subheader("🛠️ Generador")
            
            # --- ACTUALIZADO: Lista completa con los nuevos contratos ---
            tipo = st.selectbox("Documento", [
                "Alquiler Vivienda", 
                "Compraventa Vehículo", 
                "Servicios Freelance", 
                "Contrato Trabajo", 
                "NDA (Confidencialidad)",
                "Compraventa Vivienda (Piso/Casa)",
                "Contrato de Arras",
                "Desistimiento / Cancelación"
            ])
            
            data_p = ""
            
            # --- LÓGICA DE CAMPOS ACTUALIZADA ---
            if "Alquiler" in tipo: 
                data_p = f"Alquiler. Propietario: {st.text_input('Propietario')}. Inquilino: {st.text_input('Inquilino')}. Piso: {st.text_input('Dirección')}. Renta: {st.number_input('Renta €')}."
            
            elif "Vehículo" in tipo: 
                data_p = f"Coche. Vendedor: {st.text_input('Vendedor')}. Comprador: {st.text_input('Comprador')}. Matrícula: {st.text_input('Matrícula')}. Precio: {st.number_input('Precio €')}."
            
            elif "NDA" in tipo: # RECUPERADO ESPECÍFICO
                data_p = f"Acuerdo Confidencialidad. Parte Reveladora: {st.text_input('Parte Reveladora')}. Parte Receptora: {st.text_input('Parte Receptora')}. Información a proteger: {st.text_area('Motivo/Información')}."
            
            elif "Compraventa Vivienda" in tipo: # AÑADIDO
                data_p = f"Compraventa Inmueble. Vendedor: {st.text_input('Vendedor')}. Comprador: {st.text_input('Comprador')}. Inmueble: {st.text_input('Datos Inmueble')}. Precio: {st.number_input('Precio Venta €')}."
            
            elif "Arras" in tipo: # AÑADIDO
                data_p = f"Contrato de Arras. Vendedor: {st.text_input('Vendedor')}. Comprador: {st.text_input('Comprador')}. Inmueble: {st.text_input('Inmueble')}. Precio Total: {st.number_input('Precio Total')}. Señal/Arras: {st.number_input('Señal €')}. Plazo Máximo: {st.date_input('Fecha Límite')}."

            elif "Cancelación" in tipo:
                data_p = f"Acuerdo de Terminación de Contrato. Contrato Original: {st.text_input('¿Qué contrato cancelas?')}. Partes: {st.text_input('Partes implicadas')}. Motivo: {st.text_input('Motivo (Opcional)')}. Fecha efectiva: {st.date_input('Fecha Fin')}."
            
            else: # Servicios / Trabajo
                data_p = f"{tipo}. Partes: {st.text_input('Partes')}. Detalles: {st.text_area('Detalles')}."
            
            if st.button("✨ REDACTAR"):
                with st.spinner("Redactando..."):
                    st.session_state.generated_contract = groq_engine(f"Redacta contrato legal España {tipo}. Datos: {data_p}", api_key, 0.3)
    
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

# --- TAB 3: RESPONDER/RECURRIR ---
with tabs[2]:
    modo = st.radio("Opción:", ["✍️ Redactar Burofax", "🛡️ Responder/Recurrir (Subir PDF/Foto)"], horizontal=True)
    c_rec, c_doc = st.columns([1, 1.3])
    
    if "Redactar" in modo:
        with c_rec:
            with st.container(border=True):
                st.subheader("📢 Iniciar Reclamación")
                motivo = st.selectbox("Motivo", ["Seguros", "Fianza Alquiler", "Factura", "Otro"])
                remitente = st.text_input("Tus Datos")
                dest = st.text_input("Destinatario")
                hechos = st.text_area("Hechos")
                if st.button("🔥 GENERAR CARTA"):
                    with st.spinner("Redactando..."):
                        p = f"Redacta Burofax reclamación España. Remitente: {remitente}. Destinatario: {dest}. Motivo: {motivo}. Hechos: {hechos}. Tono firme."
                        st.session_state.generated_claim = groq_engine(p, api_key)
    else:
        with c_rec:
            with st.container(border=True):
                st.subheader("🛡️ Generar Defensa")
                st.info("Sube carta/multa (PDF o Foto).")
                uploaded_defense = st.file_uploader("Archivo", type=["pdf", "jpg", "png"], key="u_def")
                mis_datos = st.text_input("Tus Datos")
                mis_argumentos = st.text_area("Tus Argumentos")
                
                if uploaded_defense:
                    if uploaded_defense.type == "application/pdf":
                        st.session_state.defense_text = extract_text_from_pdf(uploaded_defense)
                    else:
                        with st.spinner("Leyendo imagen..."):
                            st.session_state.defense_text = analyze_image_groq(uploaded_defense, "Transcribe notificación legal.", api_key)
                
                if st.button("⚖️ GENERAR RESPUESTA"):
                    if st.session_state.defense_text and mis_datos:
                        with st.spinner("Redactando defensa..."):
                            p_def = f"Actúa como abogado. He recibido esto: '{st.session_state.defense_text}'. Mis argumentos: '{mis_argumentos}'. Redacta CARTA DE OPOSICIÓN. Remitente: {mis_datos}."
                            st.session_state.generated_claim = groq_engine(p_def, api_key)
                    else: st.warning("Sube archivo y pon datos.")

    with c_doc:
        if st.session_state.generated_claim:
            st.markdown(f"<div class='contract-box'>{st.session_state.generated_claim}</div>", unsafe_allow_html=True)
            st.write("")
            with st.container(border=True):
                ce2, cb2 = st.columns([2,1])
                with ce2: m2 = st.text_input("Email", key="mr")
                with cb2:
                    st.write(""); st.write("")
                    if st.button("PDF DEFENSA", key="br"):
                        save_lead(m2, "DEFENSA", "Doc generado")
                        pdf_claim = create_pdf(st.session_state.generated_claim, "Carta Legal")
                        st.download_button("⬇️ Bajar PDF", data=pdf_claim, file_name="Defensa.pdf", mime="application/pdf")

# --- TAB 4: IMPUESTOS ---
with tabs[3]:
    c_cal, c_res = st.columns([1, 1.3])
    with c_cal:
        with st.container(border=True):
            st.subheader("🧮 Calculadora Fiscal")
            tipo_calc = st.selectbox("Trámite", ["Venta Inmueble (Plusvalía+IRPF)", "Sueldo Neto (Nómina)", "Gastos Compraventa", "IPC Alquiler", "Cuota Hipoteca"])            
            anio_actual = datetime.now().year
            
            # 1. VENTA
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
            
            # 2. SUELDO NETO (HÍBRIDO: IA DEFINE EL TIPO % + PYTHON CALCULA EL DINERO)
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
                    if estado == "Casado/a":
                        conyuge_cargo = st.checkbox("¿Cónyuge gana < 1.500€/año?")
                
                with c_fam2: discapacidad = st.selectbox("Discapacidad", ["Ninguna", "33%-65%", ">65%"])
                hijos = st.number_input("Nº Hijos (<25 años)", 0, 10, 0)
                hijos_menores_3 = 0
                if hijos > 0:
                    hijos_menores_3 = st.number_input(f"De los {hijos}, ¿cuántos < 3 años?", 0, hijos, 0)
                
                # BOTÓN DE CALCULAR
                if st.button("💶 CALCULAR NETO EXACTO"):
                    with st.spinner("Consultando normativa regional y calculando..."):
                        
                        # 1. PREGUNTAMOS A LA IA SOLO EL TIPO DE RETENCIÓN (EL % CORRECTO)
                        prompt_irpf = f"""
                        Actúa como experto fiscal en España 2025.
                        Calcula el TIPO MEDIO DE RETENCIÓN IRPF (%) para este perfil:
                        - Salario Bruto: {bruto}€
                        - Región: {comunidad} (Aplica tablas autonómicas vigentes)
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

                        # 2. MATEMÁTICAS EN PYTHON (INFALIBLES)
                        ss_anual = bruto * 0.0635  # Seguridad Social estandar (~6.35%)
                        irpf_anual = bruto * (tipo_irpf / 100)
                        neto_anual = bruto - ss_anual - irpf_anual
                        
                        # Python divide, así que 12 pagas SIEMPRE será mayor que 14
                        mes_12 = neto_anual / 12
                        mes_14 = neto_anual / 14 

                        # 3. FORMATO DE NÚMEROS
                        f_mes_12 = "{:,.2f}".format(mes_12).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_mes_14 = "{:,.2f}".format(mes_14).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_irpf_mensual = "{:,.2f}".format(irpf_anual/12).replace(",", "X").replace(".", ",").replace("X", ".")
                        f_tipo = "{:,.2f}".format(tipo_irpf).replace(",", "X").replace(".", ",").replace("X", ".")

                        # 4. HTML VISUAL
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

                # --- BOTÓN DE RESET ---
                if st.session_state.generated_calc:
                     st.write("")
                     if st.button("🔄 Calcular de nuevo", use_container_width=True):
                         st.session_state.generated_calc = ""
                         st.rerun()

            # 3. GASTOS
            elif "Compraventa" in tipo_calc:
                precio = st.number_input("Precio (€)", 150000.0)
                ccaa = st.selectbox("CCAA", ["Madrid", "Cataluña", "Andalucía", "Valencia", "Otras"])
                tipo = st.radio("Tipo", ["Segunda Mano", "Obra Nueva"])
                if st.button("🧮 CALCULAR"):
                    st.session_state.generated_calc = groq_engine(f"Gastos compraventa {ccaa}. Precio {precio}. Tipo {tipo}.", api_key)

            # 4. IPC
            elif "IPC" in tipo_calc:
                renta = st.number_input("Renta (€)", 800.0)
                mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril"])
                if st.button("🧮 CALCULAR"):
                    st.session_state.generated_calc = groq_engine(f"Actualiza renta {renta}. Mes IPC {mes}.", api_key)
                    
            # 5. HIPOTECA
            elif "Hipoteca" in tipo_calc:
                st.caption("Calculadora Cuota Mensual")
                capital = st.number_input("Capital Prestado (€)", value=200000.0)
                interes = st.number_input("Interés Anual (%)", value=3.5)
                plazo = st.number_input("Plazo (Años)", value=30)
                if st.button("🧮 CALCULAR CUOTA"):
                    st.session_state.generated_calc = groq_engine(f"Calcula hipoteca. Capital {capital}. Interés {interes}. Plazo {plazo}. Tabla amortización año 1.", api_key)

    with c_res:
        if st.session_state.generated_calc:
            # LÓGICA INTELIGENTE:
            # Si es el HTML visual (nómina oscura), lo mostramos directo para respetar su diseño.
            # Si es texto plano (otras calculadoras), le ponemos la caja de papel blanca.
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
# PANEL LATERAL (MODO ADMIN SECRETO)
# ==============================================================================
with st.sidebar:
    # 1. Espacio vacío visual (CORREGIDO: Usamos un IF normal para que no imprima código raro)
    if os.path.isfile("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.write("") # Espacio separador
    
    # 2. CANDADO DIGITAL: Solo tú sabes la clave
    password = st.text_input("🔐", type="password", placeholder="Acceso Admin", label_visibility="collapsed")
    
    if password == "admin123":  # <--- CAMBIA ESTO POR TU CONTRASEÑA
        st.success("Modo Admin")
        st.markdown("---")
        
        st.markdown("### ⚙️ Panel de Control")
        if st.button("🔄 Reiniciar App"): 
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        
        if os.path.isfile("database_leads.csv"):
            st.caption("📥 Base de Datos Leads")
            df = pd.read_csv("database_leads.csv")
            st.dataframe(df, height=150)
            
            with open("database_leads.csv", "rb") as f: 
                st.download_button("Descargar CSV", f, "leads.csv", mime="text/csv")
        else:
            st.caption("📭 Base de datos vacía")
            
    else:
        # Lo que ve el cliente
        st.caption("© 2026 LegalEagle AI")




















