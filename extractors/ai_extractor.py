from config.imports import *


client = Groq(api_key=GROQ_API_KEY)

PROMPT_FACTURA = """
Eres un asistente especializado en leer facturas, recibos y comprobantes en español latino americano.
Extrae ÚNICAMENTE los siguientes datos y responde SOLO con JSON válido, sin explicaciones ni texto extra:

{
  "proveedor": "nombre de la empresa o tienda emisora",
  "total": "valor total a pagar (solo el número, sin símbolo de moneda)",
  "fecha": "fecha del documento en formato DD/MM/YYYY",
  "banco": "nombre del banco si aparece (Bancolombia, Davivienda, Nequi, BBVA, etc.), sino null",
  "tipo_documento": "factura | recibo | comprobante | otro"
}

Si no encuentras algún dato pon null. No agregues NADA fuera del JSON.
"""

def _normalizar(datos: dict) -> dict:
    """Garantiza que siempre existen todas las claves esperadas"""
    return {
        "proveedor": datos.get("proveedor") or "",
        "total": str(datos.get("total") or ""),
        "fecha": datos.get("fecha") or "", 
        "banco": datos.get("banco") or "",
        "tipo_documento": datos.get("tipo_documento") or ""
    }

def extraer_texto_con_ia(texto: str) -> dict:
    """
    Usa llama-3.3 para extraer datos de texto ya procesado
    (PDFs digitales procesados con pdfplumber o texto OCR).
    """
    try:
        respuesta = client.chat.completions.create(
            model=GROQ_MODEL_TEXTO,
            messages=[
                {"role": "system", "content": PROMPT_FACTURA},
                {"role": "user", "content": f"texto del documento:\n\n{texto[:4000]}"}

            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        contenido = respuesta.choices[0].message.content
        return _normalizar (json.loads(contenido))
    except Exception as e:
        print(f"[Groq texto] error: {e}")
        return _normalizar({})
    
def extraer_con_ia_desde_imagen(ruta_imagen: str) -> dict:
    """
    Usa llama-4-scout (vision) para leer imágenes JPG/PNG directamente.
    También se usa para páginas de PDFs escaneados convertidas a imagen.
    """
    try:
        ext = ruta_imagen.split(".")[-1].lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        with open(ruta_imagen, "rb") as f:
            imagen_b64 = base64.b64encode(f.read()).decode("utf-8")

        respuesta = client.chat.completions.create(
            model=GROQ_MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_FACTURA},
                        {"type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{imagen_b64}"}}
                    ]
                }
            ],
            temperature=0
        )
        contenido = respuesta.choices[0].message.content

        #LLaVA a veces rodeo el json con texto, así que se intenta extraer el texto limpio
        inicio = contenido.find("{")
        fin = contenido.rfind("}") + 1
        return _normalizar(json.loads(contenido[inicio:fin]))
    except Exception as e:
        print(f"[Groq vision] error: {e}")
        return _normalizar({})
