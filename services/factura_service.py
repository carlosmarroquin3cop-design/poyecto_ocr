import os
import tempfile

from pdf2image import convert_from_path

from config.settings import POPPLER_PATH

from database.db_manager import guardar_factura

from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner import limpiar_texto, extraer_patrones
from extractors.ai_extractor import (
    extraer_texto_con_ia,
    extraer_con_ia_desde_imagen,
    es_imagen
)

from models.factura import Factura

def _procesar_archivo(ruta: str, nombre: str) -> Factura:
    from extractors.ai_extractor import es_imagen
    from pdf2image import convert_from_path
    from config.settings import POPPLER_PATH
    import tempfile

    ext = os.path.splitext(nombre)[1].lower()

    if es_imagen(nombre):
        # Imagen directa → solo IA visión (no hay texto que extraer)
        tipo         = "imagen"
        texto_limpio = "[Imagen procesada con IA visión]"
        datos        = extraer_con_ia_desde_imagen(ruta)

    elif ext == ".pdf":
        if es_pdf_escaneado(ruta):
            tipo = "escaneado"
            print("PDF escaneado → usando OCR + IA visión en paralelo...")

            # --- CANAL 1: OCR con Tesseract ---
            texto_crudo  = extraer_texto_ocr(ruta)
            texto_limpio = limpiar_texto(texto_crudo)
            datos_ocr    = extraer_texto_con_ia(texto_limpio)
            print("OCR+IA:")
            print(datos_ocr)

            # --- CANAL 2: IA visión directo sobre la imagen ---
            datos_vision = {}
            try:
                paginas = convert_from_path(ruta, dpi=200, poppler_path=POPPLER_PATH)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    paginas[0].save(tmp_img.name, "PNG")
                    ruta_img_tmp = tmp_img.name
                datos_vision = extraer_con_ia_desde_imagen(ruta_img_tmp)
                os.unlink(ruta_img_tmp)
                print("IA vision:")
                print(datos_vision)
            except Exception as e:
                print(f"  IA visión falló: {e}, usando solo OCR")

            # --- CONSENSO: campo por campo, prioriza el que tenga valor ---
            datos = _consenso(datos_ocr, datos_vision)
            
            print("\n===== DATOS DEVUELTOS POR LA IA =====")
            print(datos)
            print("====================================\n")

            print("Resultado final:")
            print(datos)

        else:
            # PDF digital → solo texto (no necesita visión)
            tipo         = "digital"
            texto_crudo  = extraer_texto_pdf(ruta)
            texto_limpio = limpiar_texto(texto_crudo)
            datos        = extraer_texto_con_ia(texto_limpio)

        # Respaldo final con regex si ambos canales fallaron
        if not any(datos.values()):
            print("  Ambos canales fallaron, usando regex como último respaldo...")
            datos = extraer_patrones(texto_limpio)
    else:
        raise ValueError(f"Formato no soportado: {ext}. Usa PDF, JPG o PNG.")

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio if 'texto_limpio' in locals() else "[Imagen]",
        banco=datos.get("banco", ""),
        total=datos.get("total", ""),
        fecha=datos.get("fecha", ""),
        proveedor=datos.get("proveedor", "")
    )

    guardar_factura(
        factura.nombre_archivo, factura.tipo_pdf, factura.texto_extraido,
        factura.banco, factura.total, factura.fecha, factura.proveedor
    )
    return factura


def _consenso(datos_ocr: dict, datos_vision: dict) -> dict:
    """
    Combina los resultados de OCR+IA y de IA visión campo por campo.
    Regla: si visión tiene el dato, lo prefiere (más preciso).
           si visión no tiene el dato pero OCR sí, usa OCR.
           si ninguno tiene el dato, queda vacío.
    """
    campos = ["proveedor", "total", "fecha", "banco", "tipo_documento"]
    resultado = {}
    for campo in campos:
        val_vision = datos_vision.get(campo, "")
        val_ocr    = datos_ocr.get(campo, "")
        # Prefiere visión, cae a OCR si visión está vacío
        resultado[campo] = val_vision if val_vision else val_ocr
    return resultado