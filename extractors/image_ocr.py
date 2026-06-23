from PIL import Image
import pytesseract
import tempfile
import os

from extractors.image_preprocessor import procesar_imagen_fotografia
from config.settings import TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extraer_texto_imagen(ruta_imagen):
    """
    Extrae texto de imagen fotográfica.
    
    Flujo:
    1. Preprocesar imagen (oscurecer/contrastar)
    2. Pasar DIRECTAMENTE a Tesseract (sin PDF)
    3. OCR
    """

    print("=" * 60)
    print("EXTRAYENDO TEXTO DE IMAGEN CON PREPROCESAMIENTO")
    print("=" * 60)

    try:
        # PASO 1: Preprocesar la imagen
        ruta_procesada = procesar_imagen_fotografia(ruta_imagen)
        
        if ruta_procesada is None:
            print("[image_ocr] ❌ Preprocesamiento falló")
            return ""
        
        # PASO 2: Abrir imagen procesada
        img_procesada = Image.open(ruta_procesada)
        print(f"[image_ocr] Imagen procesada: {img_procesada.size}")
        
        # PASO 3: OCR DIRECTO sin pasar por PDF
        print("[image_ocr] Ejecutando Tesseract OCR directamente...")
        
        config_ocr = (
            "--oem 3 "
            "--psm 6 "
            "-l spa+eng "
            "-c preserve_interword_spaces=1"
        )
        
        texto = pytesseract.image_to_string(img_procesada, config=config_ocr)
        
        # PASO 4: Limpiar archivo temporal
        try:
            os.remove(ruta_procesada)
        except:
            pass
        
        print(f"[image_ocr] ✅ OCR completado ({len(texto)} caracteres)")
        return texto

    except Exception as e:
        print(f"[image_ocr] ❌ Error en OCR de imagen: {e}")
        import traceback
        traceback.print_exc()
        return ""