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
Eres un experto en validación de facturas y recibos.

Recibirás:

1. Una imagen del documento.
2. Un JSON generado previamente mediante OCR.

Tu función NO es volver a extraer toda la información.

Tu única tarea es validar cada campo del JSON comparándolo con la imagen.

Reglas:

- Si el valor del JSON es correcto, consérvalo exactamente igual.
- Si encuentras un valor más correcto en la imagen, reemplázalo.
- Si un campo está vacío y la imagen permite identificarlo claramente, complétalo.
- No inventes información.
- No elimines campos.
- No cambies los nombres de las claves.
- Devuelve exactamente el mismo JSON recibido, únicamente con las correcciones necesarias.

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

        "empresa_emisora": "proveedor",
        "empresa": "proveedor",
        "nombre_empresa": "proveedor",
        "emisor": "proveedor",

        "valor_neto_a_pagar": "total",
        "valor_total": "total",
        "total_a_pagar": "total",
        "valor": "total",

        "fecha_factura": "fecha",
        "fecha_emision": "fecha",

        "entidad_bancaria": "banco"
    }

    for clave, valor in datos.items():

        if valor is None:
            continue

        clave = str(clave).strip().lower()
        valor = str(valor).strip()

        if not clave or not valor:
            continue

        clave_final = equivalencias.get(clave, clave)

        # ------------------------------------
        # numero_factura
        # ------------------------------------

        if clave_final == "numero_factura":

            valor = valor.upper()

            # quitar espacios
            valor = valor.replace(" ", "")

            # quitar guiones
            valor = valor.replace("-", "")

            # quitar puntos
            valor = valor.replace(".", "")

        # ------------------------------------
        # total
        # ------------------------------------

        elif clave_final == "total":

            numeros = re.sub(r"[^\d]", "", valor)

            if numeros:

                valor = f"{int(numeros):,}"

        # ------------------------------------
        # proveedor
        # ------------------------------------

        elif clave_final == "proveedor":

            valor = re.sub(r"\s+", " ", valor)

            valor = valor.replace("No.", "NO.")
            valor = valor.replace("No ", "NO ")

            valor = valor.strip()

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
    
def extraer_con_ia_desde_imagen(ruta_imagen: str, datos_ocr: dict | None = None) -> dict:
    """
    Para imágenes JPG, PNG, WEBP, BMP, TIFF.
    Usa llama-4-scout con visión, lee la imagen directamente sin OCR.
    Es más preciso que OCR + texto para documentos escaneados.
    """
    try:
        b64, mime = _imagen_a_base64(ruta_imagen)


        if datos_ocr:


            prompt = f"""
            {PROMPT_FACTURA}

            Recibirás un JSON obtenido mediante OCR.

            NO debes reconstruir la factura.

            Debes revisar UNO POR UNO los campos del JSON.

            Reglas generales:

            - Conserva el JSON original.
            - Solo cambia un campo si la imagen demuestra claramente que el OCR está equivocado.
            - Si tienes dudas, conserva el valor del OCR.
            - Nunca reemplaces un dato completo por uno parcial.
            - Nunca elimines caracteres.
            - Nunca devuelvas menos información que la recibida.

            Reglas por campo:

            proveedor:
            - Corrige únicamente si el nombre comercial visible en la imagen es claramente diferente.
            - Conserva el nombre del OCR si la diferencia es solo de mayúsculas, puntos o espacios.

            nit:
            - Corrige únicamente los dígitos incorrectos.
            - Conserva los puntos y guiones si existen.
            - No elimines dígitos.

            fecha:
            - Corrige únicamente los caracteres incorrectos.
            - Mantén siempre el formato YYYY-MM-DD.

            total:
            - Corrige únicamente si el valor visible en la imagen es diferente.
            - Conserva el valor del OCR cuando la diferencia sea únicamente el formato (8500 vs 8,500).

            numero_factura:

            - Es el campo MÁS IMPORTANTE del documento.

            - Revísalo cuidadosamente antes de responder.

            - NO asumas que todos los caracteres son números.

            - Puede contener letras y números.

            - El número puede estar dividido en dos líneas.

            Ejemplo:

            Factura Electrónica de Venta No. 2G69
            126313

            Resultado correcto:

            2G69126313

            - Antes de modificar el número, compara carácter por carácter el valor del OCR con el de la imagen.

            - Si el OCR solo tiene uno o dos caracteres incorrectos, corrige únicamente esos caracteres.

            - Nunca reconstruyas el número completo desde cero.

            - Nunca elimines caracteres.

            - Nunca devuelvas un número más corto que el recibido.

            - Si tienes dudas entre una letra y un número, observa nuevamente la imagen antes de decidir.

            Presta especial atención a estas confusiones frecuentes del OCR:

            G ↔ 6
            O ↔ 0
            I ↔ 1
            L ↔ 1
            S ↔ 5
            B ↔ 8
            Z ↔ 2

            nombre_cliente:
            - Solo complétalo si aparece claramente.
            - No inventes nombres.

            JSON OCR:

            {json.dumps(datos_ocr, ensure_ascii=False, indent=2)}

            Devuelve exactamente el mismo JSON recibido.

            No reconstruyas el documento.

            No vuelvas a extraer toda la información.

            Tu trabajo consiste únicamente en corregir caracteres incorrectos del JSON OCR.

            Si el OCR tiene un único carácter equivocado (por ejemplo G↔6, O↔0, I↔1), modifica únicamente ese carácter y conserva el resto del valor.

            Si no estás completamente seguro de una corrección, conserva el valor del OCR.

            Devuelve únicamente JSON válido.
            """

        else:

            prompt = PROMPT_FACTURA

        respuesta = client.chat.completions.create(
            model=GROQ_MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
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
