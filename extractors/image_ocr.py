from PIL import Image
import pytesseract
import tempfile
import os

from extractors.image_preprocessor import procesar_imagen_fotografia
from config.settings import TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def _aplicar_upscale(img: Image.Image, factor_minimo: int = 2000) -> Image.Image:
    """
    Aplica upscale (zoom) a la imagen COMPLETA.
    Si el ancho es menor a factor_minimo, la agranda.
    """
    
    ancho, alto = img.size
    
    if ancho < factor_minimo:
        factor_escala = factor_minimo / ancho
        nuevo_ancho = int(ancho * factor_escala)
        nuevo_alto = int(alto * factor_escala)
        
        img = img.resize(
            (nuevo_ancho, nuevo_alto),
            Image.Resampling.LANCZOS
        )
        print(f"[image_ocr] Upscale: {ancho}x{alto} → {nuevo_ancho}x{nuevo_alto}")
    
    return img


def extraer_texto_imagen(ruta_imagen):
    """
    Extrae texto de imagen fotográfica SIN dividir en bloques.
    Procesamiento COMPLETO de la imagen:
    1. Preprocesar (rotación + filtro básico)
    2. Upscale moderado (2000px)
    3. OCR directo con Tesseract
    4. Limpiar
    
    Este método es MÁS FIABLE porque:
    - No divide la imagen (evita pérdida de contexto)
    - Mantiene la relación espacial de los datos
    - OCR trabaja con imagen completa
    """

    print("=" * 60)
    print("EXTRAYENDO TEXTO DE IMAGEN - PROCESAMIENTO COMPLETO")
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
        
        # PASO 3: Aplicar upscale a la imagen COMPLETA
        print("[image_ocr] Aplicando upscale a imagen completa (2000px)...")
        img_procesada = _aplicar_upscale(img_procesada, factor_minimo=2000)
        
        # PASO 4: Guardar imagen upscaleada como PNG temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            ruta_png = tmp.name
        
        img_procesada.save(ruta_png, "PNG")
        print(f"[image_ocr] PNG temporal creado: {ruta_png}")
        
        # PASO 5: OCR en la imagen COMPLETA
        print("[image_ocr] Ejecutando OCR en imagen completa...")
        
        config_ocr = (
            "--oem 3 "
            "--psm 4 "
            "-l spa+eng "
            "-c preserve_interword_spaces=1 "
            "-c textord_heavy_nr=1"
        )
        
        try:
            texto_completo = pytesseract.image_to_string(ruta_png, config=config_ocr)
        except Exception as e:
            print(f"[image_ocr] ❌ Error en OCR: {e}")
            texto_completo = ""
        
        texto_completo = texto_completo.strip()
        
        # PASO 6: Limpiar archivos temporales
        print("[image_ocr] Limpiando archivos temporales...")
        try:
            os.remove(ruta_procesada)
        except:
            pass
        
        try:
            os.remove(ruta_png)
        except:
            pass
        
        caracteres = len(texto_completo)
        print(f"[image_ocr] ✅ OCR completado ({caracteres} caracteres)")
        
        return texto_completo

    except Exception as e:
        print(f"[image_ocr] ❌ Error en OCR de imagen: {e}")
        import traceback
        traceback.print_exc()
        return ""