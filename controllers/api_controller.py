from flask import jsonify, request
from database.db_manager import obtener_todas, obtener_por_id
import os
import tempfile

from services.factura_service import _procesar_archivo


def api_procesar():
    """
    POST /api/procesar
    Body: multipart/form-data  campo: 'archivo'  (PDF, JPG o PNG)
    """
    if "archivo" not in request.files:
        return jsonify({"error": "Falta el campo 'archivo' en el form-data"}), 400

    archivo = request.files["archivo"]
    if not archivo.filename:
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    sufijo = os.path.splitext(archivo.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        archivo.save(tmp.name)
        ruta_tmp = tmp.name

    try:
        factura = _procesar_archivo(ruta_tmp, archivo.filename)
        return jsonify({
            "ok": True,
            "datos": {
                "nombre_archivo": factura.nombre_archivo,
                "tipo":           factura.tipo_pdf,
                "proveedor":      factura.proveedor,
                "total":          factura.total,
                "fecha":          factura.fecha,
                "banco":          factura.banco
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    finally:
        os.unlink(ruta_tmp)


def api_listar():
    """GET /api/facturas → devuelve todas las facturas guardadas"""
    return jsonify([dict(f) for f in obtener_todas()])


def api_detalle(factura_id):
    """GET /api/facturas/5 → detalle de una factura por ID"""
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "No encontrada"}), 404
    return jsonify(dict(factura))

def registrar_rutas(app):

    app.add_url_rule(
        "/api/procesar",
        view_func=api_procesar,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/facturas",
        view_func=api_listar,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>",
        view_func=api_detalle,
        methods=["GET"]
    )

def registrar_rutas(app):

    app.add_url_rule(
        "/api/procesar",
        view_func=api_procesar,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/facturas",
        view_func=api_listar,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>",
        view_func=api_detalle,
        methods=["GET"]
    )