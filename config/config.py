import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Umbrales de procesamiento
    MIN_LAPLACIAN_SCORE = 70.0
    MIN_OCR_CHARS = 150
