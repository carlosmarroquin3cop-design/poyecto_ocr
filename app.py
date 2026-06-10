import os
from flask import Flask, render_template

from database.db_manager import crear_tabla, obtener_todas, obtener_por_id
from controllers.api_controller import registrar_rutas

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)

crear_tabla()

registrar_rutas(app)

@app.route("/")
def index():
    return render_template(
        "index.html",
        facturas=obtener_todas()
    )


@app.route("/factura/<int:factura_id>")
def detalle_factura(factura_id):

    factura = obtener_por_id(factura_id)

    if not factura:
        return "Factura no encontrada", 404

    return render_template(
        "index.html",
        facturas=obtener_todas(),
        factura_seleccionada=factura
    )

if __name__ == "__main__":

    print("API corriendo en:        http://127.0.0.1:5000")
    print("Endpoint para subir:     POST /api/procesar")
    print("Endpoint para listar:    GET  /api/facturas")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )