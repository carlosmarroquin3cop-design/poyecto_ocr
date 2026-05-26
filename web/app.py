from flask import Flask, render_template, request
from config.imports import *

# se agrega la raiz del proyecto al PATH de Python
# Asi flask puede encontrar los modulos 'database', 'config', etc.

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import obtener_todas, obtener_por_id

# Flask (__name__) crea la aplicacion web
# __name__ le dice a Flask donde esta el archivo para encontrar templates y static
app = Flask(__name__)

@app.route("/")
def index():
    """pagina principal: muestra la lista de todas las facturas."""

    facturas = obtener_todas()
    return render_template("index.html", facturas=facturas)
    #render_template busca index.html en la carpeta templates y lo envia al navegador
    #facturas=facturas le "pasa" los datos a la plantilla HTML


@app.route("/factura/<int:factura_id>")
def detalle_factura(factura_id):
    """Muestra eñ detalle completo de una factura especifica"""
    factura = obtener_por_id(factura_id)
    if not factura:
        return "Factura no encontrada", 404 #404 = codigo HTTP de "no encontrado"
    return render_template("index.html", facturas=obtener_todas(), factura_seleccionada=factura)

if __name__ == "__main__":
    print("servidor web corriendo en: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True) #debug=True recarga el servidor automaticamente al guardar cambios