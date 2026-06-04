import pdfplumber
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import sys
import base64 
import json
from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL_TEXTO, GROQ_MODEL_VISION

