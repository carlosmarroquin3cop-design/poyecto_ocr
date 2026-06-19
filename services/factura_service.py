import os
import tempfile

from pdf2image import convert_from_path

from config.settings import POPPLER_PATH

from database.db_manager import guardar_factura

from services.comparador_service import (
    elegir_cliente,
    elegir_nombre_cliente,
    elegir_nit,
    elegir_fecha,
    elegir_total,
    elegir_proveedor,
    elegir_numero_factura
)


from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner import limpiar_texto, extraer_patrones
from extractors.regex_extractor import extraer_con_regex
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


            print("\n========== TEXTO LIMPIO ==========")
            print(texto_limpio)
            print("=================================\n")

            #PRIMERA CAPA: REGEX
            datos_regex = extraer_con_regex(texto_limpio)

            print("\n========== REGEX ==========")
            print(datos_regex)
            print("===========================\n")

            #SEGUNDA CAPA: IA
            
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
            
            print("\n========== OCR ==========")
            print(datos_ocr)

            print("\n========== VISION ==========")
            print(datos_vision)

            print("\n========== RESULTADO FINAL ==========")
            print(datos)

            print("=====================================\n")

        else:
            # PDF digital → solo texto (no necesita visión)
            tipo         = "digital"
            texto_crudo  = extraer_texto_ocr(ruta)
            texto_limpio = limpiar_texto(texto_crudo)

            print("\n========== PDF DIGITAL ==========")
            print(datos)
            print("================================\n")

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


def _consenso(datos_ocr: dict, datos_vision: dict):

    resultado = {}

    resultado["proveedor"] = elegir_proveedor(
        datos_ocr.get("proveedor", ""),
        datos_vision.get("proveedor", "")
    )

    resultado["numero_factura"] = elegir_numero_factura(
        datos_ocr.get("numero_factura", ""),
        datos_vision.get("numero_factura", "")
    )

    resultado["cliente"] = elegir_cliente(
        datos_ocr.get("cliente", ""),
        datos_vision.get("cliente", "")
    )

    resultado["nombre_cliente"] = elegir_nombre_cliente(
        datos_ocr.get("nombre_cliente", ""),
        datos_vision.get("nombre_cliente", "")
    )

    resultado["nit"] = elegir_nit(
        datos_ocr.get("nit", ""),
        datos_vision.get("nit", "")
    )

    resultado["fecha"] = elegir_fecha(
        datos_ocr.get("fecha", ""),
        datos_vision.get("fecha", "")
    )

    resultado["total"] = elegir_total(
        datos_ocr.get("total", ""),
        datos_vision.get("total", "")
    )

    resultado["banco"] = datos_vision.get(
        "banco",
        datos_ocr.get("banco", "")
    )

    return resultado