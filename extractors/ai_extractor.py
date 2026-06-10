import base64
import json
from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL_TEXTO, GROQ_MODEL_VISION 

from config.imports import *
from io import BytesIO
from PIL import Image


client = Groq(api_key=GROQ_API_KEY)

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

PROMPT_FACTURA = """
Eres un asistente especializado en leer facturas, recibos y comprobantes en español latinoamericano.
Extrae ÚNICAMENTE los siguientes datos y responde SOLO con JSON válido, sin explicaciones ni texto extra:

{
  "proveedor": "nombre de la empresa o tienda emisora",
  "total": "valor total a pagar con sus separadores originales (puntos, comas, etc.)",
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

def _imagen_a_base64(ruta: str) -> tuple[str, str]:
    """
    Lee una imagen del disco y la convierte a base64.
    Retorna (base64_string, mime_type)
    """

    ext = os.path.splitext(ruta)[1].lower()

    mapa_mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
    }

    mime = mapa_mime.get(ext, "image/jpeg")


    imagen = Image.open(ruta)

    # Reducir tamaño máximo manteniendo proporción
    imagen.thumbnail((1500, 1500))

    buffer = BytesIO()

    # JPEG es mucho más ligero
    imagen.convert("RGB").save(
        buffer,
        format="JPEG",
        quality=80,
        optimize=True
    )

    b64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return b64, mime




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
    Para imágenes JPG, PNG, WEBP, BMP, TIFF.
    Usa llama-4-scout con visión, lee la imagen directamente sin OCR.
    Es más preciso que OCR + texto para documentos escaneados.
    """
    try:
        b64, mime = _imagen_a_base64(ruta_imagen)

        respuesta = client.chat.completions.create(
            model=GROQ_MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT_FACTURA
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0
        )
        contenido = respuesta.choices[0].message.content

        # El modelo a veces rodea el JSON con texto, lo extraemos limpio
        inicio = contenido.find("{")
        fin    = contenido.rfind("}") + 1
        if inicio == -1:
            raise ValueError("La IA no devolvió JSON válido")

        return _normalizar(json.loads(contenido[inicio:fin]))
    except Exception as e:
        print(f"[Groq vision] Error: {e}")
        return _normalizar({})
    

def es_imagen(nombre_archivo: str) -> bool:
    """Devuelve True si el archivo es una imagen soportada."""
    ext = os.path.splitext(nombre_archivo)[1].lower()
    return ext in EXTENSIONES_IMAGEN
