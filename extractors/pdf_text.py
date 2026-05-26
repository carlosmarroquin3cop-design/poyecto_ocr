from config.imports import *

def extraer_texto_pdf(ruta_pdf):
    """
    Lee un PDF que tiene texto real, funciona con pdfs hechos en world, excel o facturas electronicas digitales.
    No lee pdf escaneeados    
    """

    texto_completo = ""

    try:
        #pdfplumber.open abre el pdf sin convertirlo a imagen
        
        with pdfplumber.open(ruta_pdf) as pdf:

            #pdf.pages es una lista de paginas
            #se itera cada pagina con un for

            for numero_pagina, pagina in enumerate(pdf.pages, start=1):

                #extract_text() saca toda la informacion hallada en una pagina
                # Mantiene caracteres especiales como *, $, /, @, etc.

                texto = pagina.extract_text(x_tolerance=2, y_tolerance=2)

                #x_tolerance y y_tolerance = margen de error en pixeles para agrupar letras
                #si esta muy bajo: puede separar letras, si esta muy alto puede juntar palabras

                if texto:
                    texto_completo += f"\n--- Página {numero_pagina} ---\n"
                    texto_completo += texto

                #tambien se intentara extraer tabla lo que es util para facturas con columnas
                tablas = pagina.extract_tables()
                for tabla in tablas:
                    texto_completo += "\n[TABLLA DETECTADA]\n"
                    for fila in tabla:
                        fila_limpia = [str(celda) if celda is not None else "" for celda in fila]
                        texto_completo += " | ".join(fila_limpia) + "\n"

    except Exception as e:
        print(f"Error al extraer texto con pdfplumber: {e}")
        return ""
    return texto_completo