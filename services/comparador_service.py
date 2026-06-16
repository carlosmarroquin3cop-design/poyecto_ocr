import re


def elegir_cliente(ocr, vision):

    return ocr if ocr else vision


def elegir_nombre_cliente(ocr, vision):

    return ocr if ocr else vision


def elegir_nit(ocr, vision):

    return vision if vision else ocr


def elegir_fecha(ocr, vision):

    return vision if vision else ocr


def elegir_total(ocr, vision):

    return vision if vision else ocr


def elegir_proveedor(ocr, vision):

    if not vision:
        return ocr

    if not ocr:
        return vision

    if len(vision) > len(ocr):
        return vision

    return ocr


def elegir_numero_factura(ocr, vision):

    if not vision:
        return ocr

    if not ocr:
        return vision

    # Si visión contiene letras sospechosas y OCR es numérico,
    # preferimos OCR
    if re.search(r'[A-Za-z]', vision):

        if ocr.isdigit():

            return ocr

    return vision