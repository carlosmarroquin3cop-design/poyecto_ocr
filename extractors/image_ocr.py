from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
import tempfile
import os

from extractors.pdf_ocr import extraer_texto_ocr


def extraer_texto_imagen(ruta_imagen):

    print("Procesando imagen con OCR mediante PDF temporal...")

    try:

        imagen = Image.open(ruta_imagen)

        MAX_SIZE = 1200

        ancho, alto = imagen.size

        if max(ancho, alto) > MAX_SIZE:

            proporcion = MAX_SIZE / max(ancho, alto)

            imagen = imagen.resize(
                (
                    int(ancho * proporcion),
                    int(alto * proporcion)
                )
            )

        imagen = imagen.convert("L")

        imagen = imagen.convert("L")

        imagen = ImageOps.autocontrast(imagen)

        imagen = ImageEnhance.Contrast(imagen).enhance(1.15)

        imagen = ImageEnhance.Sharpness(imagen).enhance(1.05)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as tmp:

            ruta_pdf_temporal = tmp.name

        imagen.convert("RGB").save(
            ruta_pdf_temporal,
            "PDF"
        )

        texto = extraer_texto_ocr(
            ruta_pdf_temporal
        )

        os.remove(ruta_pdf_temporal)

        return texto

    except Exception as e:

        print(f"Error en OCR de imagen: {e}")

        return ""