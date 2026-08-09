from flask import Flask
# Cargar configuración y variables de entorno primero
import config.config

from google.cloud import vision
from google import genai

from services.cedula_ocr_service import CedulaOcrService
from controllers.ocr_controller import create_ocr_blueprint

# Inicializar Flask
app = Flask(__name__)

# --- RAÍZ DE COMPOSICIÓN (DI) ---
# 1. Instanciar los clientes externos (Singletons)
vision_client = vision.ImageAnnotatorClient()
genai_client = genai.Client()

# 2. Inyectar dependencias por constructor en el servicio
ocr_service = CedulaOcrService(vision_client=vision_client, genai_client=genai_client)

# 3. Inyectar el servicio en la fábrica del controlador
ocr_blueprint = create_ocr_blueprint(ocr_service)
# ---------------------------------

# Registrar rutas
app.register_blueprint(ocr_blueprint)

if __name__ == '__main__':
    # Para desarrollo local, correr en el puerto 5000
    app.run(host='0.0.0.0', port=5000)
