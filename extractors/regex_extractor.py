import re

def extraer_con_regex(texto: str) -> dict:

    datos = {
        "proveedor": "",
        "total": "",
        "fecha": "",
        "nit": "",
        "cliente": "",
        "nombre_cliente": "",
        "numero_factura": "",
        "banco": ""
    }

    #-------------NIT---------------

    patron = re.search(
        r'NIT[:\s]*([\d\.\,\-\s]+)',
        texto,
        re.IGNORECASE
    )

    if patron:
        datos["nit"] = ( 
            patron.group(1)
            .replace(" ", "")
        )


    #-----------------NUMERO FACTURA-----------------

    patrones_factura = [

        r'FACTURA.*?NO\.?\s*([A-Z0-9]{3,})\s*\n\s*([A-Z0-9]{3,})',

        r'FACTURA.*?NO\.?\s*([A-Z0-9]{3,})\s+([A-Z0-9]{3,})'

    ]

    for patron in patrones_factura:

        encontrado = re.search(

            patron,

            texto,

            re.IGNORECASE

        )

        if encontrado:

            parte1 = encontrado.group(1).upper()
            parte2 = encontrado.group(2).upper()

            datos["numero_factura"] = parte1 + parte2

            break
 
        



    #-------------------PROVEEDOR----------------

    patron = re.search(
        r'(REBAJA PLUS.*)',

        texto,

        re.IGNORECASE
    )

    if patron:

        datos["proveedor"] = patron.group(1).strip()

    #-------------------CLIENTE------------

    patrones_cliente = [

        r'CLIENTE[:;\s]*([0-9]{6,})',

        r'CLIENTE[.;:\s]*([0-9]{6,})'

    ]

    for patron in patrones_cliente:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE | re.DOTALL

        )

        if encontrado:

            datos["cliente"] = encontrado.group(1)
            break



    #---------------NOMBRE CLIENTE---------

    patrones_nombre = [

        r'NOMBRE[:;\s]*([A-ZÁÉÍÓÚÑ ]+)',

        r'NOMBRE[.;:\s]*([A-ZÁÉÍÓÚÑ ]+)',

        r'NOMBRE.*?([A-ZÁÉÍÓÚÑ ]{5,})'
        
    ]

    for patron in patrones_nombre:

        coincidencias = re.findall(

            patron,
            texto,
            re.IGNORECASE | re.DOTALL

        )

        for nombre in coincidencias:

            nombre = nombre.strip()

            if (
                "SW" not in nombre.upper()
                and "FINANCIERO" not in nombre.upper()
                and "CARVAJAL" not in nombre.upper()
                and len(nombre) > 5
            ):

                datos["nombre_cliente"] = nombre
                break


    #-----------FECHA---------------
    patron = re.search(
        r'(\d{4}-\d{2}-\d{2})',
        texto
    )

    if patron:
        datos["fecha"] = patron.group(1)


    #---------TOTAL-----------------

    PATRONES_TOTAL = [

        r'VALOR NETO A PAGAR.*?([\d\.,]+)',
        r'TOTAL A PAGAR.*?([\d\.,]+)',
        r'VALOR TOTAL.*?([\d\.,]+)',
        r'VALOR VENTA.*?([\d\.,]+)',
        r'TOTAL.*?([\d\.,]+)',
        r'VALOR.*?([\d\.,]+)'
    ]

    for patron in PATRONES_TOTAL:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if encontrado:

            datos["total"] = encontrado.group(1)
            break

    return datos