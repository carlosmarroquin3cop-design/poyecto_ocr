import os

#BASE_DIR es la ruta absoluta de la carpeta raiz del proyecto
#os.path.dirname obtiene "la carpeta que contiene este archivo"
#__file__ es la ruta de settings.py
# se hace dos veces para subir dos niveles: de config/ a proyecto_facturas/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#carpeta donde se guardan los pdfs

PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")

DB_PATH = os.path.join(BASE_DIR, "database", "facturas.db")

TESSERACT_PATH = r"C:\Users\cmarroquin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\Users\cmarroquin\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin"
