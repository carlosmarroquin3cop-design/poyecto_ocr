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
Eres un experto en lectura de facturas, recibos y comprobantes en español.

Responde SIEMPRE con este JSON:

{
"proveedor":"",
"total":"",
"fecha":"",
"nit":"",
"cliente":"",
"nombre_cliente":"",
"numero_factura":"",
"banco":""
}

Reglas:

* proveedor = nombre del establecimiento, empresa, banco o entidad emisora.

* total = priorizar, en este orden:

  1. VALOR NETO A PAGAR
  2. TOTAL A PAGAR
  3. VALOR TOTAL
  4. TOTAL

* fecha = fecha principal del documento.

* nit = NIT de la empresa emisora.

* cliente = valor asociado al campo CLIENTE. Puede ser una identificación, código, referencia o número.

* nombre_cliente = valor asociado al campo NOMBRE. Puede ser "CONSUMIDOR FINAL", "JORGE ARIZA SALAMANCA" o cualquier otro nombre.

Ejemplo:

CLIENTE: 222222222222

NOMBRE: CONSUMIDOR FINAL

debe devolver:

"cliente": "222222222222"

"nombre_cliente": "CONSUMIDOR FINAL"

* numero_factura = número completo de factura.

IMPORTANTE:

Si el número de factura aparece dividido en varias líneas, deben unirse.

Ejemplo:

Factura Electrónica de Venta No. 2199
184411

debe devolver:

"numero_factura": "2199184411"

Otro ejemplo:

Factura Electrónica de Venta No. 2G69
125005

debe devolver:

"numero_factura": "2G69125005"

No confundas:

* productos,
* medicamentos,
* vendedores,
* cajeros,
* nombres de empleados,

con el proveedor.

No inventes información.

Si un dato no aparece en el documento, devolver una cadena vacía.

Responde exclusivamente con JSON válido.

"""

def _normalizar(datos: dict) -> dict:
    """
    Limpia el JSON devuelto por la IA y traduce claves equivalentes
    para mantener compatibilidad con el sistema.
    """

    if not isinstance(datos, dict):
        return {}

    resultado = {}

    equivalencias = {

        # proveedor
        "empresa_emisora": "proveedor",
        "empresa": "proveedor",
        "nombre_empresa": "proveedor",
        "emisor": "proveedor",

        # total
        "valor_neto_a_pagar": "total",
        "valor_total": "total",
        "total_a_pagar": "total",
        "valor": "total",

        # fecha
        "fecha_factura": "fecha",
        "fecha_emision": "fecha",

        # banco
        "entidad_bancaria": "banco"
    }

    for clave, valor in datos.items():

        if valor is None:
            continue

        clave = str(clave).strip().lower()
        valor = str(valor).strip()

        if not clave or not valor:
            continue

        # Traducción inteligente
        clave_final = equivalencias.get(clave, clave)

        resultado[clave_final] = valor

    return resultado

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
