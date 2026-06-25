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
        .replace("\n", "")
        .replace("\r", "")
        .strip()
    )


    #-----------------NUMERO FACTURA-----------------

    patrones_factura = [

        # Caso:
        # FACTURA ... NO. 2669
        # 126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{3,})\s*\n+\s*([A-Z0-9]{3,})',

        # Caso:
        # FACTURA ... NO. 2669 126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{3,})\s+([A-Z0-9]{3,})',

        # Caso:
        # FACTURA ... NO.2669126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{8,})'
    ]

    for patron in patrones_factura:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if not encontrado:
            continue

        if len(encontrado.groups()) == 2:

            parte1 = encontrado.group(1).replace(" ", "").upper()
            parte2 = encontrado.group(2).replace(" ", "").upper()

            datos["numero_factura"] = parte1 + parte2

        else:

            datos["numero_factura"] = (
                encontrado.group(1)
                .replace(" ", "")
                .upper()
            )

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

    prioridades = [
        "VALOR NETO A PAGAR",
        "TOTAL A PAGAR",
        "VALOR TOTAL",
        "VALOR VENTA",
        "SUBTOTAL"
    ]

    lineas = texto.splitlines()

    for prioridad in prioridades:

        for i, linea in enumerate(lineas):

            if prioridad not in linea.upper():
                continue

            # Revisar la línea actual y las dos siguientes
            bloque = "\n".join(lineas[i:i+3])

            # Buscar únicamente valores precedidos por $
            encontrados = re.findall(
                r'\$\s*([\d][\d\.,]{2,})',
                bloque
            )

            if encontrados:
                datos["total"] = encontrados[-1]
                break

        if datos["total"]:
            break

    return datos