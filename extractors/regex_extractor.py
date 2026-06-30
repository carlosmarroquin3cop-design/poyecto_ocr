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

    # 1. Buscar establecimientos muy comunes al inicio del documento

    patrones_proveedor = [

        r'REBAJA\s+PLUS[^\n]*',

        r'LA\s+REBAJA[^\n]*',

        r'CRUZ\s+VERDE[^\n]*',

        r'FARMATODO[^\n]*',

        r'EXITO[^\n]*',

        r'CARULLA[^\n]*',

        r'OLIMPICA[^\n]*',

        r'D1[^\n]*',

        r'ARA[^\n]*',

        r'JUMBO[^\n]*',

        r'ALKOSTO[^\n]*'

    ]

    for patron in patrones_proveedor:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if encontrado:

            datos["proveedor"] = encontrado.group(0).strip()
            break


    # 2. Si aún no encontró proveedor,
    # buscar razón social

    if not datos["proveedor"]:

        patron = re.search(
            r'([A-ZÁÉÍÓÚÑ0-9&.,\- ]{4,}(?:S\.A\.S|SAS|S\.A|SA|LTDA|E\.U|EU))',
            texto,
            re.IGNORECASE
        )

        if patron:

            datos["proveedor"] = patron.group(1).strip()

    else:

        # 2. Buscar entidades bancarias conocidas
        bancos = [

            "BANCOLOMBIA",
            "BANCO DE BOGOTA",
            "BANCO DE OCCIDENTE",
            "BANCO POPULAR",
            "BANCO AV VILLAS",
            "DAVIVIENDA",
            "DAVIPLATA",
            "BBVA",
            "SCOTIABANK",
            "COLPATRIA",
            "BANCO AGRARIO",
            "NEQUI",

            "BANCO FALABELLA",
            "BANCO CAJA SOCIAL",
            "BANCOOMEVA",
            "ITAU",
            "LULO BANK",
            "BAN100"
        ]

        for banco in bancos:

            if re.search(r"\b" + re.escape(banco) + r"\b", texto, re.IGNORECASE):

                datos["proveedor"] = banco
                datos["banco"] = banco
                break

        # 3. Buscar comercios conocidos solamente si aún no encontró proveedor
        if not datos["proveedor"]:

            comercios = [

                "EXITO",
                "CARULLA",
                "SURTIMAX",
                "OLIMPICA",
                "ARA",
                "D1",
                "ISIMO",
                "JUMBO",
                "METRO",
                "ALKOSTO",
                "KTRONIX",

                "LA REBAJA",
                "REBAJA PLUS",
                "CRUZ VERDE",
                "FARMATODO",
                "LOCATEL",

                "HOMECENTER",
                "EASY",
                "PANAMERICANA",

                "TERPEL",
                "PRIMAX",
                "BIOMAX",
                "TEXACO",
                "ESSO",

                "CLARO",
                "MOVISTAR",
                "TIGO",
                "WOM",
                "DIRECTV",

                "ENEL",
                "EPM",
                "EMCALI"
            ]

            for comercio in comercios:

                if re.search(r"\b" + re.escape(comercio) + r"\b", texto, re.IGNORECASE):

                    datos["proveedor"] = comercio
                    break

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