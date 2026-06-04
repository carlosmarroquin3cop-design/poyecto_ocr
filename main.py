from config.imports import *
from config.settings import PDF_FOLDER
from database.db_manager import crear_tabla, guardar_factura
from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner import limpiar_texto, extraer_patrones
from models.factura import Factura
from extractors.ai_extractor import extraer_texto_con_ia

def procesar_pdf(ruta_pdf):
    nombre = os.path.basename(ruta_pdf)
    print(f"\nProcesando: {nombre}")

    if es_pdf_escaneado(ruta_pdf):
        print("Tipo: escaneado → OCR + IA")
        tipo = "escaneado"
        texto_crudo = extraer_texto_ocr(ruta_pdf)
    else:
        print("Tipo: digital → extracción directa + IA")
        tipo = "digital"
        texto_crudo = extraer_texto_pdf(ruta_pdf)

    texto_limpio = limpiar_texto(texto_crudo)

    # IA reemplaza los regex, pero si falla usamos regex como respaldo
    datos = extraer_texto_con_ia(texto_limpio)
    if not any(datos.values()):
        print("IA no respondió, usando regex como respaldo...")
        datos = extraer_patrones(texto_limpio)

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio,
        banco=datos["banco"],
        total=datos["total"],
        fecha=datos["fecha"],
        proveedor=datos["proveedor"]
    )

    guardar_factura(
        factura.nombre_archivo,
        factura.tipo_pdf,
        factura.texto_extraido,
        factura.banco,
        factura.total,
        factura.fecha,
        factura.proveedor
    )

    print(f"Proveedor : {factura.proveedor or 'No detectado'}")
    print(f"Banco     : {factura.banco     or 'No detectado'}")
    print(f"Total     : {factura.total     or 'No detectado'}")
    print(f"Fecha     : {factura.fecha     or 'No detectada'}")
    return factura


def main():
    print("Iniciando procesamiento de facturas...\n")

    crear_tabla()
    os.makedirs(PDF_FOLDER, exist_ok=True)

    archivos_pdf = [
        f for f in os.listdir(PDF_FOLDER)
        if f.lower().endswith(".pdf")
    ]

    if not archivos_pdf:
        print(f"No hay PDFs en la carpeta: {PDF_FOLDER}")
        print("Mete tus archivos PDF en esa carpeta y vuelve a correr el programa.")
        return

    print(f"Se encontraron {len(archivos_pdf)} PDF(s) para procesar.\n")

    for archivo in archivos_pdf:
        ruta_completa = os.path.join(PDF_FOLDER, archivo)
        procesar_pdf(ruta_completa)

    print(f"\nListo! {len(archivos_pdf)} factura(s) procesada(s) y guardada(s).")
    print("Ahora corre 'python web/app.py' para ver la visualizacion web.\n")


if __name__ == "__main__":
    main()
