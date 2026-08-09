from flask import Flask
# Cargar configuración y variables de entorno primero
import config.config

# Importar el controlador
from controllers.ocr_controller import ocr_blueprint

# Inicializar Flask
app = Flask(__name__)

# Registrar rutas
app.register_blueprint(ocr_blueprint)

if __name__ == '__main__':
    # Para desarrollo local, correr en el puerto 5000
    app.run(host='0.0.0.0', port=5000)
