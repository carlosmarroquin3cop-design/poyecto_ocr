import os
import sqlite3

from config.settings import DB_PATH 


def asegurar_carpeta_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def crear_tabla():
    """
    Crear la tabla 'facturas' en la base de datos si no existe todavia.
    """

    #sqlite3.connect() abre o crea si no existe en su defecto, el archivo .db
    #'with' asegura que la conexion se cierre sola aunque tenga errrores

    asegurar_carpeta_db()

    with sqlite3.connect(DB_PATH) as conn:

        cursor = conn.cursor() #Escribe en la BD

        #Este bloque creara la tabla con sus columnas.
        # IF NOT EXISTS = "solo crea la tabla si no exitste aun"

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_archivo TEXT NOT NULL,
                tipo_pdf TEXT,
                texto_extraido TEXT,
                banco TEXT,
                total TEXT,
                fecha TEXT,
                proveedor TEXT,
                fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit() #Guarda los cambios en la BD
        print("Tabla'facturas lista.")

def guardar_factura(nombre_archivo, tipo_pdf, texto_extraido, banco="", total="", fecha="", proveedor=""):
    """
    Inserta una factura nuea en la base de datos.
    Recibe los datos ya procesados y los guarda.
    
    """
    asegurar_carpeta_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        #Los signos ? son marcadores de posicion para evitar inyecciones SQL. Los valores se pasan como tupla en el segundo argumento de execute().

        cursor.execute("""
            INSERT INTO facturas
            (nombre_archivo, tipo_pdf, texto_extraido, banco, total, fecha, proveedor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre_archivo, tipo_pdf, texto_extraido, banco, total, fecha, proveedor))

        conn.commit()
        print(f"Guardado: {nombre_archivo}")


def obtener_todas():
    """
    Trae todas las facturas en la base de datos y retorna una lista de filas)
    """

    with sqlite3.connect(DB_PATH) as conn:

        #row_factory hace que cada fila se pueda usar de diccionario
        #Asi puedes escribir fila["Banco"] en vez de fila [4]
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facturas ORDER BY fecha_procesado DESC")
        return cursor.fetchall() #trae todos los resultados
    

def obtener_por_id(factura_id):
    """
    Trae una factura por su ID y retorna un diccionario con sus datos.
    Si no encuentra la factura, retorna None.
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facturas WHERE id = ?", (factura_id,))
        return cursor.fetchone() #trae solo una fila
