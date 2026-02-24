import os
# Force reload
import io
import json
import base64
import requests
import re
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from groq import Groq
import PyPDF2
from PIL import Image
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LegalApp API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_api_key():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY no configurada.")
    return api_key

# ==============================================================================
# CORE AI FUNCTIONS
# ==============================================================================

def groq_engine(prompt: str, key: str, temp: float = 0.2):
    client = Groq(api_key=key)
    try:
        sys_msg = "Eres LegalApp, abogado y asesor fiscal experto en España. Responde de forma directa, compacta y profesional. Cita leyes."
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=temp
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error AI: {str(e)}")

def extract_text_from_pdf(file_bytes: bytes, max_pages: int = 30) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        limit = min(len(pdf_reader.pages), max_pages)
        for page_num in range(limit):
            page_text = pdf_reader.pages[page_num].extract_text() or ""
            text += f"[PÁGINA {page_num + 1}]: {' '.join(page_text.split())}\n\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo PDF: {e}")

def analyze_image_groq(file_bytes: bytes, prompt: str, api_key: str):
    try:
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        if image.width > 1500 or image.height > 1500:
            image.thumbnail((1500, 1500))
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Vision AI: {e}")

def detectar_tipo_contrato(texto_pdf: str, api_key: str):
    prompt_tipo = f"Analiza el inicio del contrato y clasifícalo (Ej: Energía, Alquiler, Laboral, Seguro). Responde SOLO con la categoría.\n\nTEXTO: {texto_pdf[:2000]}"
    return groq_engine(prompt_tipo, api_key)

def extraer_datos_universales(texto_pdf: str, categoria: str, api_key: str):
    campos = "partes_firmantes, fecha_inicio, importe_o_valor, clausulas_clave"
    if categoria == "Alquiler": campos = "arrendador, arrendatario, renta_mensual, fianza, duracion"
    elif categoria == "Laboral": campos = "empresa, empleado, salario_bruto_anual, jornada, tipo_contrato"

    prompt_dinamico = f"""
    Actúa como extractor de datos. Contrato tipo: {categoria}.
    INSTRUCCIONES:
    1. Busca: {campos}.
    2. Busca cifras junto a '€', '€/mes'.
    4. Devuelve EXCLUSIVAMENTE formato JSON puro.
    TEXTO:
    {texto_pdf[:15000]}
    """
    return groq_engine(prompt_dinamico, api_key)

# ==============================================================================
# DOC GENERATION
# ==============================================================================

def create_pdf(text: str, title: str = "Documento Legal") -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin_x, margin_y = 50, 50
    max_width, cursor_y = width - 2 * margin_x, height - margin_y
    
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle('JustifiedBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    style_heading = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceAfter=10, spaceBefore=10)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, cursor_y, title)
    c.setLineWidth(0.5)
    c.line(margin_x, cursor_y - 10, width - margin_x, cursor_y - 10)
    cursor_y -= 40

    for para_text in text.split('\n'):
        para_text = para_text.strip()
        if not para_text:
            cursor_y -= 10
            continue
        if para_text.startswith('#'):
            p = Paragraph(para_text.replace('#', '').strip(), style_heading)
        else:
            formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para_text)
            p = Paragraph(formatted_text, style_body)

        w, h = p.wrap(max_width, height)
        if cursor_y - h < margin_y:
            c.showPage()
            cursor_y = height - margin_y
            w, h = p.wrap(max_width, height)
        p.drawOn(c, margin_x, cursor_y - h)
        cursor_y -= h
    c.save()
    return buffer.getvalue()


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@app.get("/")
def read_root():
    return {"status": "ok", "app": "LegalApp Backend API"}

# --- 1. ANALÍTICA ---
@app.post("/api/analyze/document")
async def analyze_document(file: UploadFile = File(...), mode: str = Form("CONTRATO")):
    api_key = get_api_key()
    file_bytes = await file.read()
    
    # 1. Extracción de texto
    if file.filename.lower().endswith(".pdf"):
        texto = extract_text_from_pdf(file_bytes)
    else:
        texto = analyze_image_groq(file_bytes, "Transcribe fielmente todo el texto visible.", api_key)
    
    if not texto.strip():
        raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento.")

    result = {}
    
    # 2. Análisis Contextual Groq
    if mode == "CONTRATO":
        cat = detectar_tipo_contrato(texto, api_key)
        datos = extraer_datos_universales(texto, cat, api_key)
        prompt = f"""
        Aplica para: Analizar Riesgos legales
        TIPO: {cat}
        
        GENERA INFORME MARKDOWN DE 4 PUNTOS CON:
        1. 📋 RESUMEN EJECUTIVO: Propósito y partes
        2. 📅 DURACIÓN Y FECHAS (Preaviso, etc.)
        3. 💶 ECONOMÍA
        4. 🚨 CLÁUSULAS ABUSIVAS o PELIGROSAS
        5. ⚖️ VEREDICTO FINAL
        
        TEXTO: {texto[:10000]}
        """
        informe = groq_engine(prompt, api_key)
        result = {"categoria": cat, "datos_estructurados": datos, "informe": informe}

    elif mode == "SEGURO":
        prompt = f"Analiza esta póliza. 1. LO QUE CUBRE 2. EXCLUSIONES 3. LÍMITES 4. RESUMEN.\nTEXTO: {texto[:10000]}"
        result = {"informe": groq_engine(prompt, api_key)}
        
    elif mode == "GENERICO":
        result = {"informe": "✅ Documento procesado. Listo para chatear.", "texto_crudo": texto[:10000]}

    return JSONResponse(content=result)

class ChatRequest(BaseModel):
    pregunta: str
    contexto: str

@app.post("/api/analyze/chat")
async def chat_document(req: ChatRequest):
    api_key = get_api_key()
    prompt = f"ERES UN EXPERTO LEGAL.\nCONTEXTO: {req.contexto[:20000]}\nPREGUNTA USUARIO: {req.pregunta}\nResponde directo y claro."
    respuesta = groq_engine(prompt, api_key)
    return {"respuesta": respuesta}

# --- 2. GENERACIÓN DE CONTRATOS ---
class GenerateRequest(BaseModel):
    modo: str
    datos: str
    ciudad: str

@app.post("/api/generate/document")
async def generate_document(req: GenerateRequest):
    api_key = get_api_key()
    prompt = f"""
    Actúa como Abogado Experto en España.
    Redacta un {req.modo} formal y válido legalmente.
    DATOS CLAVE: {req.datos}
    ESTRUCTURA OBLIGATORIA:
    1. Encabezado (Lugar, Fecha, Reunidos).
    2. Exponen.
    3. ESTIPULACIONES (Cláusulas numeradas).
    4. Cierre y Firmas. En {req.ciudad}.
    Usa lenguaje jurídico. Formato Markdown.
    """
    contrato = groq_engine(prompt, api_key, temp=0.3)
    return {"documento": contrato}

class PdfRequest(BaseModel):
    texto: str
    titulo: str = "Documento Legal"

@app.post("/api/generate/pdf")
async def get_pdf(req: PdfRequest):
    pdf_bytes = create_pdf(req.texto, req.titulo)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={req.titulo.replace(' ', '_')}.pdf"})

# --- 3. DEFENSA LEGAL ---
@app.post("/api/defense/analyze")
async def analyze_defense(file: UploadFile = File(None), modo: str = Form(...), mis_datos: str = Form(""), extras: str = Form("")):
    api_key = get_api_key()
    
    file_txt = ""
    if file:
        file_bytes = await file.read()
        if file.filename.lower().endswith(".pdf"):
            file_txt = extract_text_from_pdf(file_bytes)
        else:
            file_txt = analyze_image_groq(file_bytes, "Lee el texto del requerimiento, multa o documento oficial.", api_key)

    if modo == "MULTA_VIABILIDAD":
        p = f"Analiza esta multa/carta: {file_txt[:4000]}. 1. ¿Recurrible? 2. Defectos forma 3. Probabilidad éxito. 4. Consejo."
        return {"analisis": groq_engine(p, api_key)}
        
    elif modo == "MULTA_RECURSO":
        p = f"Redacta PLIEGO DESCARGOS. MULTA: {file_txt[:4000]}. CLIENTE: {mis_datos}. Alega defectos de forma. Cita ley aplicable."
        return {"documento": groq_engine(p, api_key)}
        
    elif modo == "BUROFAX":
        p = f"Redacta Burofax. Datos: {mis_datos}. Contexto: {extras}. Tono formal."
        return {"documento": groq_engine(p, api_key)}
        
    elif modo == "RESPONDER":
        p = f"Redacta respuesta a esta carta: {file_txt[:4000]}. Mi argumento: {extras}. Tono formal."
        return {"documento": groq_engine(p, api_key)}
    
    raise HTTPException(status_code=400, detail="Modo no soportado.")

# --- 4. FINANZAS Y FISCALIDAD ---
class FinanzasChatRequest(BaseModel):
    pregunta: str

@app.post("/api/finanzas/chat")
async def chat_finanzas(req: FinanzasChatRequest):
    api_key = get_api_key()
    prompt = f"ERES UN ASESOR FISCAL ESPAÑOL EXPERTO. Responde breve y directo a esta duda tributaria:\nPREGUNTA USUARIO: {req.pregunta}"
    respuesta = groq_engine(prompt, api_key)
    return {"respuesta": respuesta}

class TipRequest(BaseModel):
    modo: str
    datos: str

@app.post("/api/finanzas/tip")
async def generate_tip(req: TipRequest):
    api_key = get_api_key()
    prompt = f"Eres LegalApp, experto fiscal español. En base a este resultado de la calculadora de {req.modo}: '{req.datos}', da UN ÚNICO consejo o tip fiscal accionable en no más de 3 líneas para maximizar el ahorro del usuario. Tono profesional y animado."
    return {"tip": groq_engine(prompt, api_key)}

class HipotecaRequest(BaseModel):
    capital: float
    plazo: int
    t_interes: str
    interes_fijo: float
    dif_banco: float

@app.post("/api/finanzas/calculators/hipoteca")
async def calculate_hipoteca(req: HipotecaRequest):
    api_key = get_api_key()
    interes_final = req.interes_fijo if req.t_interes == "Fijo" else (2.6 + req.dif_banco)
    p_h = f"Calcula hipoteca. Capital: {req.capital}€. Interés total: {interes_final}%. Plazo: {req.plazo} años. Indica cuota mensual estricta y total intereses a pagar. Responde SOLO con un JSON válido con campos 'cuota_mensual', 'total_intereses', 'total_pagar' con números reales sin unidades."
    try:
        res_ia = groq_engine(p_h, api_key)
        clean_json = res_ia.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        # Fallback simple math
        r = (interes_final / 100) / 12
        n = req.plazo * 12
        if r > 0:
            cuota = req.capital * r * (1 + r)**n / ((1 + r)**n - 1)
        else:
            cuota = req.capital / n
        total_pagar = cuota * n
        total_intereses = total_pagar - req.capital
        return {
            "cuota_mensual": round(cuota, 2),
            "total_intereses": round(total_intereses, 2),
            "total_pagar": round(total_pagar, 2)
        }

class SueldoRequest(BaseModel):
    bruto: float
    edad: int
    comunidad: str
    movilidad: bool = False
    tipo_contrato: str = "General / Indefinido"
    cat_pro: str = "Ingenieros, licenciados y alta dirección"
    estado: str = "Soltero/a"
    conyuge_cargo: bool = False
    hijos: int = 0
    hijos_menores_3: int = 0
    pension_alim: float = 0
    pension_comp: float = 0

@app.post("/api/finanzas/calculators/sueldo")
async def calculate_sueldo(req: SueldoRequest):
    api_key = get_api_key()
    p_s = f"""
    Calcula sueldo neto anual y mensual en España 2026. 
    Bruto: {req.bruto}€. CCAA: {req.comunidad}. Hijos: {req.hijos} (menores de 3: {req.hijos_menores_3}). 
    Estado civil: {req.estado}. Cónyuge a cargo: {req.conyuge_cargo}.
    Movilidad: {req.movilidad}. Pensión alimentos: {req.pension_alim}. Pensión compensatoria: {req.pension_comp}.
    
    Devuelve EXCLUSIVAMENTE un JSON válido sin texto adicional con los siguientes campos estrictamente en minúscula:
    'irpf_mensual' (float positivo), 
    'ss_mensual' (float positivo), 
    'bruto_anual' (float), 
    'tipo_irpf' (float %), 
    'valores': [neto_total_anual, neto_mensual_14_pagas]
    """
    try:
        res_ia = groq_engine(p_s, api_key)
        clean_json = res_ia.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        # Fallback math estimativo
        neto = req.bruto * 0.76
        return {
            "irpf_mensual": (req.bruto * 0.18) / 12,
            "ss_mensual": (req.bruto * 0.06) / 12,
            "bruto_anual": req.bruto,
            "tipo_irpf": 18.0,
            "valores": [neto, neto / 14]
        }

class ItpRequest(BaseModel):
    precio: float
    ccaa: str
    salario_anual: float
    edades: list[int]
    es_habitual: bool
    es_fam_num: bool
    es_discap: bool

@app.post("/api/finanzas/calculators/itp")
async def calculate_itp(req: ItpRequest):
    api_key = get_api_key()
    p_s = f"""
    Calcula ITP para vivienda de segunda mano. 
    Precio de compra o referencia: {req.precio}€. 
    CA (Autonomía): {req.ccaa}. 
    Edades compradores: {req.edades}. Familia Numerosa: {req.es_fam_num}. Discapacidad: {req.es_discap}. Vivienda habitual: {req.es_habitual}.
    
    Devuelve EXCLUSIVAMENTE un JSON válido sin Markdown con:
    'porcentaje_aplicado' (string tipo "6%"), 
    'valor_impuestos' (float, cantidad euros de ITP), 
    'gastos_gestion_notaria' (float, estimación euros notaría y registro, aprox 1.5%), 
    'ahorro_total_necesario' (float, impuestos + notaría + 20% entrada bancaria si lo fuera, sólo la suma de gastos), 
    'explicacion_bonificacion' (string, breve tip si aplica a deducción en su CA).
    """
    try:
        res_ia = groq_engine(p_s, api_key)
        clean_json = res_ia.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        return {
            "porcentaje_aplicado": "10% (Est)",
            "valor_impuestos": req.precio * 0.1,
            "gastos_gestion_notaria": 1500,
            "ahorro_total_necesario": (req.precio * 0.1) + 1500 + (req.precio * 0.2),
            "explicacion_bonificacion": "No se pudieron calcular bonificaciones exactas en este momento."
        }

class VentaRequest(BaseModel):
    p_venta: float
    p_compra: float
    f_compra: int
    v_suelo: float
    tipo_impositivo: float

@app.post("/api/finanzas/calculators/venta")
async def calculate_venta(req: VentaRequest):
    api_key = get_api_key()
    p_s = f"""
    Calcula Plusvalía Municipal e IRPF por la venta de un Inmueble Urbano. 
    Compra original: {req.p_compra}€ en el año {req.f_compra}. 
    Venta actual: {req.p_venta}€ en el año actual. 
    Valor Catastral del Suelo: {req.v_suelo}€. 
    Tipo Impositivo del Ayuntamiento: {req.tipo_impositivo}%. 
    
    Devuelve EXCLUSIVAMENTE un JSON válido sin texto adicional con: 
    'mejor_opcion' (float, importe plusvalía municipal si la hubiera, elige objetiva o real, la más barata), 
    'irpf_estimado' (float, importe a pagar en IRPF por la ganancia neta en base al ahorro 19-28%), 
    'ganancia_patrimonial' (float, venta - compra tributable).
    """
    try:
        res_ia = groq_engine(p_s, api_key)
        clean_json = res_ia.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        ganancia = req.p_venta - req.p_compra
        irpf = (ganancia * 0.19) if ganancia > 0 else 0
        return {"mejor_opcion": 0, "irpf_estimado": irpf, "ganancia_patrimonial": ganancia}

class IpcRequest(BaseModel):
    renta: float
    mes: str

@app.post("/api/finanzas/calculators/ipc")
async def calculate_ipc(req: IpcRequest):
    api_key = get_api_key()
    p = f"Actúa como asesor inmobiliario en España. Calcula la actualización de alquiler. Renta actual: {req.renta}€. Mes de renovación: {req.mes}. Explica brevemente el tope del 3% u otra limitación legal vigente si aplica, y da el resultado de la nueva renta final estimada. Responde en Markdown estructurado."
    return {"informe": groq_engine(p, api_key)}

class RentaRequest(BaseModel):
    ccaa: str
    estado_civil: str
    discapacidad: bool
    hijos: bool
    num_hijos: int
    ascendientes: bool
    alquiler: bool
    hipoteca: bool
    otros: str

@app.post("/api/finanzas/calculators/renta")
async def calculate_renta(req: RentaRequest):
    api_key = get_api_key()
    pf = []
    pf.append(f"ESTADO CIVIL: {req.estado_civil}.")
    if req.discapacidad: pf.append("Con Discapacidad.")
    if req.hijos: pf.append(f"Tiene {req.num_hijos} hijos.")
    if req.ascendientes: pf.append("Ascendientes a cargo.")
    if req.alquiler: pf.append("Vive de Alquiler.")
    if req.hipoteca: pf.append("Paga hipoteca.")
    if req.otros: pf.append(f"Otros: {req.otros}.")
    
    perfil_txt = " | ".join(pf)
    
    prompt = f"""
    Actúa como Asesor Fiscal experto en IRPF España (Campaña actual).
    Analiza las deducciones Autonómicas de: {req.ccaa} y Estatales clave.
    PERFIL: {perfil_txt}.
    TAREA: Lista deducciones aplicables brevemente.
    Responde el texto en Markdown.
    """
    return {"informe": groq_engine(prompt, api_key)}

@app.post("/api/finanzas/calculators/escaner")
async def calculate_escaner(file: UploadFile = File(...)):
    api_key = get_api_key()
    file_bytes = await file.read()
    if file.filename.lower().endswith(".pdf"):
        txt = extract_text_from_pdf(file_bytes)
    else:
        txt = analyze_image_groq(file_bytes, "Transcribe conceptos y retenciones.", api_key)
    
    p = f"Analiza esta nómina: {txt[:4000]}. Verifica SMI 2026, IRPF correcto y Bases Cotización en un informe markdown."
    return {"informe": groq_engine(p, api_key)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
