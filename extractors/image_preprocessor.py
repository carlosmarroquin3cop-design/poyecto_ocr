"""
Preprocesamiento INTELIGENTE estilo CamScanner.
Optimizado para procesar 1.9k imágenes de recibos/facturas.
Balance automático + rotación automática para horizontales.
"""

from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageStat
import tempfile
import os


def _detectar_y_rotar_documento(img: Image.Image) -> Image.Image:
    """
    Detecta si la imagen está horizontal y la rota a vertical.
    Los recibos/facturas deben estar en vertical (portrait).
    """
    
    ancho, alto = img.size
    
    # Si el ancho es mayor que el alto, está horizontal
    if ancho > alto:
        print("[PREPROCESSOR] Imagen horizontal detectada → Rotando 90°")
        img = img.rotate(90, expand=True)
        print(f"[PREPROCESSOR] Nueva dimensión: {img.size}")
    
    return img


def procesar_imagen_fotografia(ruta_imagen: str) -> str:
    """
    Procesa foto de documento con balance inteligente.
    Resultado: todas las imágenes legibles, sin importar condición de luz o rotación.
    """
    
    print(f"\n[PREPROCESSOR] Procesando: {ruta_imagen}")
    
    try:
        img = Image.open(ruta_imagen)
        ancho_orig, alto_orig = img.size
        print(f"[PREPROCESSOR] Tamaño original: {ancho_orig}x{alto_orig}")
        
        # PASO 0: Detectar y rotar si es necesario
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
        
        # PASO 3: Analizar la imagen
        stats = ImageStat.Stat(img)
        media_brillo = stats.mean[0]
        desv_brillo = stats.stddev[0]
        
        print(f"[PREPROCESSOR] Análisis: brillo={media_brillo:.1f}, desviación={desv_brillo:.1f}")
        
        # CLASIFICAR TIPO DE IMAGEN
        if media_brillo < 110:
            tipo_imagen = "OSCURA CON SOMBRA"
            print(f"[PREPROCESSOR] TIPO: {tipo_imagen}")
        elif media_brillo < 140:
            tipo_imagen = "MEDIANA"
            print(f"[PREPROCESSOR] TIPO: {tipo_imagen}")
        else:
            tipo_imagen = "CLARA"
            print(f"[PREPROCESSOR] TIPO: {tipo_imagen}")
        
        # PASO 4: Gaussian Blur (adaptativo al ruido)
        if desv_brillo > 50:
            radio_blur = 1.3
            print("[PREPROCESSOR] Imagen ruidosa → Blur moderado")
        else:
            radio_blur = 0.7
            print("[PREPROCESSOR] Imagen clara → Blur mínimo")
        
        img = img.filter(ImageFilter.GaussianBlur(radius=radio_blur))
        
        # PASO 5: Estrategia DIFERENCIADA por tipo de imagen
        
        if tipo_imagen == "OSCURA CON SOMBRA":
            # ESTRATEGIA: MÁS BRILLO, MENOS CONTRASTE
            print("[PREPROCESSOR] Aplicando estrategia OSCURA...")
            
            # Iluminar bastante
            enhancer_bright = ImageEnhance.Brightness(img)
            img = enhancer_bright.enhance(1.35)
            
            # Autocontrast suave
            img = ImageOps.autocontrast(img, cutoff=3)
            
            # Contraste BAJO (para no perder detalles en sombras)
            enhancer_contrast = ImageEnhance.Contrast(img)
            img = enhancer_contrast.enhance(1.25)
            
        elif tipo_imagen == "MEDIANA":
            # ESTRATEGIA: BALANCE
            print("[PREPROCESSOR] Aplicando estrategia MEDIANA...")
            
            # Iluminar moderado
            enhancer_bright = ImageEnhance.Brightness(img)
            img = enhancer_bright.enhance(1.15)
            
            # Autocontrast moderado
            img = ImageOps.autocontrast(img, cutoff=2)
            
            # Contraste moderado
            enhancer_contrast = ImageEnhance.Contrast(img)
            img = enhancer_contrast.enhance(1.45)
            
        else:  # CLARA
            # ESTRATEGIA: MÁS CONTRASTE, MENOS BRILLO
            print("[PREPROCESSOR] Aplicando estrategia CLARA...")
            
            # Iluminar muy poco
            enhancer_bright = ImageEnhance.Brightness(img)
            img = enhancer_bright.enhance(1.05)
            
            # Autocontrast más agresivo
            img = ImageOps.autocontrast(img, cutoff=1)
            
            # Contraste FUERTE (para oscurecer el texto)
            enhancer_contrast = ImageEnhance.Contrast(img)
            img = enhancer_contrast.enhance(1.7)
        
        # PASO 6: Nitidez (siempre aplicar)
        img = img.filter(ImageFilter.SHARPEN)
        
        # PASO 7: Guardar como PNG temporal
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