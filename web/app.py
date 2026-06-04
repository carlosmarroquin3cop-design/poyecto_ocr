import os, sys, tempfile
from flask import Flask, request, jsonify, render_template

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import crear_tabla, guardar_factura, obtener_todas, obtener_por_id
from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr  import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner  import limpiar_texto, extraer_patrones
from extractors.ai_extractor import extraer_texto_con_ia, extraer_con_ia_desde_imagen
from models.factura import Factura

app = Flask(__name__)
crear_tabla()

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
EXTENSIONES_PDF    = {".pdf"}


def _procesar_archivo(ruta: str, nombre: str) -> Factura:
    """
    Lógica central. Detecta el tipo de archivo y elige la estrategia correcta:
    - Imagen directa         → IA vision (Groq llama-4-scout)
    - PDF digital            → pdfplumber + IA texto (Groq llama-3.3)
    - PDF escaneado          → OCR tesseract + IA texto (Groq llama-3.3)
    """
    ext = os.path.splitext(nombre)[1].lower()

    if ext in EXTENSIONES_IMAGEN:
        tipo        = "imagen"
        texto_limpio = f"[Imagen procesada con IA vision]"
        datos       = extraer_con_ia_desde_imagen(ruta)

    elif ext in EXTENSIONES_PDF:
        if es_pdf_escaneado(ruta):
            tipo       = "escaneado"
            texto_crudo = extraer_texto_ocr(ruta)
        else:
            tipo       = "digital"
            texto_crudo = extraer_texto_pdf(ruta)

        texto_limpio = limpiar_texto(texto_crudo)
        datos        = extraer_texto_con_ia(texto_limpio)

        # Respaldo con regex si la IA no devuelve nada
        if not any(datos.values()):
            datos = extraer_patrones(texto_limpio)
    else:
        raise ValueError(f"Formato no soportado: {ext}. Usa PDF, JPG o PNG.")

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio,
        banco=datos.get("banco", ""),
        total=datos.get("total", ""),
        fecha=datos.get("fecha", ""),
        proveedor=datos.get("proveedor", "")
    )

    guardar_factura(
        factura.nombre_archivo, factura.tipo_pdf, factura.texto_extraido,
        factura.banco, factura.total, factura.fecha, factura.proveedor
    )
    return factura


# ── API REST ─────────────────────────────────────────────────────

@app.route("/api/procesar", methods=["POST"])
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


@app.route("/api/facturas", methods=["GET"])
def api_listar():
    """GET /api/facturas → devuelve todas las facturas guardadas"""
    return jsonify([dict(f) for f in obtener_todas()])


@app.route("/api/facturas/<int:factura_id>", methods=["GET"])
def api_detalle(factura_id):
    """GET /api/facturas/5 → detalle de una factura por ID"""
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "No encontrada"}), 404
    return jsonify(dict(factura))


# ── UI WEB (se mantiene igual que antes) ─────────────────────────

@app.route("/")
def index():
    return render_template("index.html", facturas=obtener_todas())


@app.route("/factura/<int:factura_id>")
def detalle_factura(factura_id):
    factura = obtener_por_id(factura_id)
    if not factura:
        return "Factura no encontrada", 404
    return render_template("index.html",
                           facturas=obtener_todas(),
                           factura_seleccionada=factura)


if __name__ == "__main__":
    print("API corriendo en:        http://127.0.0.1:5000")
    print("Endpoint para subir:     POST /api/procesar")
    print("Endpoint para listar:    GET  /api/facturas")
    app.run(host="0.0.0.0", port=5000, debug=True)