"""
Preprocesamiento SIMPLE y EFECTIVO estilo CamScanner.
Sin CLAHE. Solo iluminación + filtros inteligentes.
"""

from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageStat
import tempfile
import os
import cv2
import numpy as np


def _detectar_y_rotar_documento(img: Image.Image) -> Image.Image:
    """
    Detecta si la imagen está horizontal y la rota a vertical.
    """
    
    ancho, alto = img.size
    
    if ancho > alto:
        print("[PREPROCESSOR] Imagen horizontal detectada → Rotando 90°")
        img = img.rotate(90, expand=True)
        print(f"[PREPROCESSOR] Nueva dimensión: {img.size}")
    
    return img


def procesar_imagen_fotografia(ruta_imagen: str) -> str:
    """
    Procesa foto de documento.
    Simple: redimensionar → iluminar → blur → contraste → nitidez.
    """
    
    print(f"\n[PREPROCESSOR] Procesando: {ruta_imagen}")
    
    try:
        img = Image.open(ruta_imagen)

        # =====================================
        # CORRECCION DE SOMBRAS
        # =====================================

        img_cv = cv2.imread(ruta_imagen)

        gray_shadow = cv2.cvtColor(
            img_cv,
            cv2.COLOR_BGR2GRAY
        )

        

        background = cv2.GaussianBlur(
            gray_shadow,
            (151, 151),
            0
        )

        corrected = cv2.divide(
            gray_shadow,
            background,
            scale=220
        )

        corrected = cv2.convertScaleAbs(
            corrected,
            alpha=1.15,
            beta=-5
        )

        corrected = cv2.fastNlMeansDenoising(
            corrected,
            None,
            10,
            7,
            21
        )

        img = Image.fromarray(corrected)

        ancho_orig, alto_orig = img.size
        print(f"[PREPROCESSOR] Tamaño original: {ancho_orig}x{alto_orig}")
        
        # PASO 0: Rotar si es necesario
        img = _detectar_y_rotar_documento(img)
        
        # PASO 1: Redimensionar si es muy grande
        ancho, alto = img.size
        if max(ancho, alto) > 2500:
            ratio = 2500 / max(ancho, alto)
            nuevo_ancho = int(ancho * ratio)
            nuevo_alto = int(alto * ratio)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            print(f"[PREPROCESSOR] Redimensionada a: {img.size}")
        
        # PASO 2: Convertir a escala de grises
        img = img.convert("L")
        
        # PASO 3: Analizar brillo inicial
        stats = ImageStat.Stat(img)
        media_brillo = stats.mean[0]
        desv_brillo = stats.stddev[0]
        
        print(f"[PREPROCESSOR] Análisis inicial: brillo={media_brillo:.1f}, desviación={desv_brillo:.1f}")
        
        # PASO 4: ILUMINAR PRIMERO (esto aclara las sombras sin bloques feos)
        # Cuanto más oscura, más iluminamos
        if media_brillo < 100:
            factor_brillo = 1.5  # Muy oscura
            print("[PREPROCESSOR] Imagen oscura → +50% brillo")
        elif media_brillo < 130:
            factor_brillo = 1.3 # Medianamente oscura
            print("[PREPROCESSOR] Imagen mediana → +30% brillo")
        else:
            factor_brillo = 1.0  # Clara
            print("[PREPROCESSOR] Imagen clara → +10% brillo")
        
        enhancer_bright = ImageEnhance.Brightness(img)
        img = enhancer_bright.enhance(factor_brillo)
        
        # PASO 5: Gaussian Blur suave (reduce ruido)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
        
        
        # PASO 6: Expandir rango dinámico
        img = ImageOps.autocontrast(img, cutoff=0)

        # =====================================================
        # NUEVO BLOQUE OCR
        # Oscurece únicamente las letras sin afectar el papel.
        # =====================================================

        img_np = np.array(img)

        # BlackHat resalta solamente texto oscuro
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (15, 15)
        )

        blackhat = cv2.morphologyEx(
            img_np,
            cv2.MORPH_BLACKHAT,
            kernel
        )

        # Amplificar solamente el texto encontrado
        blackhat = cv2.normalize(
            blackhat,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        )

        # Restar el texto detectado al fondo
        resultado = cv2.subtract(
            img_np,
            blackhat
        )

        # Oscurecer únicamente el texto encontrado

        resultado = cv2.addWeighted(
            img_np,
            1.0,
            blackhat,
            -1.6,
            0
        )

        resultado = cv2.normalize(
            resultado,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        )

        resultado = cv2.fastNlMeansDenoising(
            resultado,
            None,
            6,
            7,
            21
        )

        img = Image.fromarray(resultado)
        
        # PASO 9: Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            ruta_temp = tmp.name
        
        img.save(ruta_temp, "PNG")
        print(f"[PREPROCESSOR] ✅ Imagen procesada: {ruta_temp}")
        
        return ruta_temp
        
    except Exception as e:
        print(f"[PREPROCESSOR] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None