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
        r'NIT[:\s]*([\d.\,\-]+)',
        texto,
        re.IGNORECASE
    )

    if patron:
        datos["nit"] = patron.group(1)


    #-------------------CLIENTE------------

    patron = re.search(
        r'CLIENTE[:;\s]*([A-Z0-9]+)',
        texto,
        re.IGNORECASE
    )

    if patron:
        datos["cliente"] = patron.group(1)


    #---------------NOMBRE CLIENTE---------

    coincidencias = re.findall(
        r'NOMBRE[:;\s]*([A-ZÁÉÍÓÚÑ ]+)',
        texto,
        re.IGNORECASE
    )

    for nombre in coincidencias:

        nombre = nombre.strip()

        if (
            "SW" not in nombre.upper()
            and len(nombre) > 5
        ):

            datos["nombre_cliente"] = nombre


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