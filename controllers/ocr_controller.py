from flask import Blueprint, request, jsonify
from services.cedula_ocr_service import CedulaOcrService

ocr_blueprint = Blueprint('ocr', __name__)

@ocr_blueprint.route('/api/extract-id', methods=['POST'])
def extract_id():
    # Validar presencia de archivo
    if 'image' not in request.files or request.files['image'].filename == '':
        return jsonify({"codigo": "FILE_MISSING", "error": "No se adjuntó ninguna imagen en la petición (campo 'image')."}), 400

    try:
        image_bytes = request.files['image'].read()
        
        # Delegar el procesamiento completo al servicio
        resultado_json = CedulaOcrService.process_id_card(image_bytes)
        
        # Devolver resultado exitoso
        return jsonify(resultado_json), 200

    except ValueError as e:
        error_code = str(e)
        mensajes = {
            "INVALID_IMAGE": "El archivo enviado no pudo ser decodificado como imagen.",
            "IMAGE_TOO_BLURRY": "La imagen es demasiado borrosa para procesar. Por favor envíe una imagen más nítida.",
            "INSUFFICIENT_TEXT": "El OCR no logró detectar suficiente texto. Asegúrese de que el documento esté bien iluminado y encuadrado.",
            "INVALID_DOCUMENT_TYPE": "El documento enviado no parece pertenecer a una cédula de identidad venezolana.",
            "DATA_EXTRACTION_FAILED": "El LLM no logró estructurar de forma confiable la información extraída de la imagen."
        }
        msg = mensajes.get(error_code, "Error de validación desconocido.")
        return jsonify({"codigo": error_code, "error": msg}), 400
        
    except RuntimeError as e:
        return jsonify({"codigo": "EXTERNAL_SERVICE_ERROR", "error": "Error interno comunicándose con los servicios de Google Cloud o Gemini."}), 500
        
    except Exception as e:
        return jsonify({"codigo": "INTERNAL_SERVER_ERROR", "error": str(e)}), 500
