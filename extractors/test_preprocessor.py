from extractors.image_preprocessor import procesar_imagen_fotografia
from PIL import Image

# PRUEBA 1: Ver la imagen preprocesada directamente
ruta_tu_foto = r"C:\Users\cmarroquin\Documents\web para api\static\uploads\17823124147173957361011920302968.jpg"  # Reemplaza con tu archivo

imagen_procesada_path = procesar_imagen_fotografia(ruta_tu_foto)

if imagen_procesada_path:
    img = Image.open(imagen_procesada_path)
    img.show()  # Ver la imagen preprocesada
    print(f"✅ Imagen guardada en: {imagen_procesada_path}")
else:
    print("❌ Error en preprocesamiento")