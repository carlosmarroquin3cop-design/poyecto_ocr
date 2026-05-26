#definen regex y otras cosas para la lectura de los pdf.

from config.imports import *

def limpiar_texto(texto):
    """ 
    Limpia el texto extraido SIN eliminar caracteres especiales importantes.
    Elimina solo ruido (espacios dobles, saltos de linea excesivos, etc)

    """
    if not texto:
        return ""
    
    #reemplaza multiples espacios seguidos por uno solo
    #\s+ = uno o mas espacios en blanco (incluye tabs)
    texto = re.sub(r' {2,}', ' ', texto)

    # Reemplaza multiples espacios seguidos por uno maximo 2
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Elimina espacios al inicio y final de cada linea
    lineas = [linea.strip() for linea in texto.split('\n')]
    texto = '\n'.join(lineas)

    return texto.strip()

def extraer_patrones(texto):
    """
    Busca patrones especificos de facturas en el texto extraido.
    Usa expresiones regulares (regex) para encontrar datos concretos
    retorna un diccionario con los datos encontrados, o vacio si no se encuentra nada.
    """

    datos = {
        "total": "",
        "fecha": "",
        "proveedor": "",
        "banco": ""
    }

    # --- BUSCAR TOTAL / VALOR ---
    # Busca patrones como: "TOTAL $1.500.000", "Total: 25.000", "VALOR 50,000"
    # \$? = signo de dólar opcional
    # [\d.,]+ = uno o más dígitos, puntos o comas (para números con separadores)

    patron_total = re.search(
        r'(?:TOTAL|Total|VALOR|Valor|SUBTOTAL|VALOR PAGO|Subtotal|VALOR VENTA|VENTA|VALOR NETO ABONADO)[:\s]*[\$]?\s*([\d.,]+)',
        texto
    )
    if patron_total:

        #.group(1) trae el primer grupo capturado (lo que esta entre parentesis en el patron)
        datos["total"] = patron_total.group(1).strip()

    # --- BUSCAR FECHA ---
    # Busca formatos: 01/01/2024, 01-01-2024, 2024-01-01
    patron_fecha = re.search(
        r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',
        texto
    )
    if patron_fecha:
        datos["fecha"] = patron_fecha.group(0)

    # --- BUSCAR BANCO ---
    # Lista de bancos colombianos

    bancos = [
        "Bancolombia", "Davivienda", "Banco de Bogotá", "Banco de Occidente", "Banco Popular", "Banco AV Villas",
        "Nequi", "BBVA", "Colpatria", "Daviplata", "Banco Agrario", "Banco Occidente Colombia"
    ]

    # re.IGNORECASE = no distingue mayusculas/minusculas
    for banco in bancos:
        if re.search(banco, texto, re.IGNORECASE):
            datos["banco"] = banco
            break

    # --- BUSCAR PROVEEDOR ---
    # Buscar lineas que contengan S.A.S, S.A., LTDA
    patron_empresa = re.search(
        r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s\-\&\.]+(?:S\.A\.S|S\.A|LTDA|SAS|SA|LTDA\.))',
        texto
    )
    if patron_empresa:
        datos["proveedor"] = patron_empresa.group(0).strip()

    else:
        # Buscar nombres en mayusculas tipo COPSERVIR, LA REBAJA ETC
        patron_mayus = re.search(
            r'\b([A-ZÁÉÍÓÚÑ]{4,}(?:\s+[A-ZÁÉÍÓÚÑ]{2,})*)\.?\b',
            texto
        )

        if patron_mayus:
            datos["proveedor"] = patron_mayus.group(1).strip()

    return datos
