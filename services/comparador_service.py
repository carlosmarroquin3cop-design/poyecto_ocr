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

    ocr = str(ocr).strip()
    vision = str(vision).strip()

    # Si ambos son iguales
    if ocr == vision:
        return ocr

    # Si uno contiene al otro, conservar el más completo
    if ocr in vision:
        return vision

    if vision in ocr:
        return ocr

    # Si la IA devuelve menos caracteres, conservar OCR
    if len(vision) < len(ocr):
        return ocr

    # Si la IA devuelve más caracteres, usar IA
    if len(vision) > len(ocr):
        return vision

    # Misma longitud:
    # la IA puede haber corregido caracteres como G↔6, O↔0, I↔1
    return vision