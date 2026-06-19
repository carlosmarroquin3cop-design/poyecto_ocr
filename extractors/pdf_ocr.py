from config.imports import *
from PIL import ImageEnhance
from config.settings import TESSERACT_PATH, POPPLER_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extraer_texto_ocr(ruta_pdf):
    """
    Lee un PDF escaneado, convierte cada pagina en imagen y luego lee la imagen.
    Es util para recibos fisicos escaneados, facturas en papel, etc.
    """

    texto_completo = ""

    try:
        # Convertir el PDF en lista de imagenes: una imagen por pagina.
        # dpi=300 da buena resolucion para OCR, aunque puede ser mas lento.
        paginas = convert_from_path(
            ruta_pdf,
            dpi=400,
            poppler_path=POPPLER_PATH
        )

        for numero_pagina, imagen in enumerate(paginas, start=1):
            print(f"Procesando pagina {numero_pagina} con OCR...")

            # --oem 3 usa el mejor motor disponible.
            # --psm 6 asume un bloque uniforme de texto.
            # -l spa+eng usa espanol e ingles para facturas mixtas.
            config_ocr = (
                "--oem 3 "
                "--psm 6 "
                "-l spa+eng "
                "-c preserve_interword_spaces=1"
            )

            # Convertir a escala de grises
            imagen = imagen.convert("L")

            # Aumentar contraste
            imagen = ImageEnhance.Contrast(imagen).enhance(2.5)

            #MEjorar nitidez
            imagen = imagen.point(
                lambda x: 255 if x > 170 else 0,
                mode='1'
            )

            # OCR
            texto = pytesseract.image_to_string(
                imagen,
                config=config_ocr
            )

            if texto.strip():
                texto_completo += f"\n--- Pagina {numero_pagina} (OCR) ---\n"
                texto_completo += texto
    except Exception as e:
        print(f"Error en OCR de {ruta_pdf}: {e}")
        return ""

    return texto_completo


def es_pdf_escaneado(ruta_pdf):
    """
    Detecta automaticamente si un PDF es escaneado o tiene texto real.
    Asi el programa decide solo que metodo usar.
    """

    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()

            # Si hay menos de 30 caracteres, se asume que es escaneado.
            if texto is None or len(texto.strip()) < 30:
                return True

            return False
    except Exception:
        return True
