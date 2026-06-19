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

    # Si ambos son iguales
    if ocr == vision:
        return ocr

    # Si uno contiene al otro, usar el más largo
    if ocr in vision:
        return vision

    if vision in ocr:
        return ocr

    # Si tienen longitudes parecidas, confiar en visión
    if abs(len(vision) - len(ocr)) <= 2:
        return vision

    # Si no, conservar OCR
    return ocr