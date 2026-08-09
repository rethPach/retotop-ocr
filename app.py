import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.cloud import vision
from google import genai
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

load_dotenv()

# ==========================================
# CONFIGURACIÓN DE UMBRALES (THRESHOLDS)
# ==========================================
MIN_LAPLACIAN_SCORE = 70.0
MIN_OCR_CHARS = 150

app = Flask(__name__)

# ==========================================
# ESQUEMA PYDANTIC
# ==========================================
class CedulaVenezolana(BaseModel):
    cedula: int = Field(..., description="Número de cédula de identidad, solo números, sin puntos ni letras")
    nombres: str = Field(..., description="Nombres de la persona, en mayúsculas")
    apellidos: str = Field(..., description="Apellidos de la persona, en mayúsculas")
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento en formato exacto YYYY-MM-DD")

# ==========================================
# FUNCIONES CORE
# ==========================================
def optimize_id_card(image_bytes: bytes) -> bytes:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("INVALID_IMAGE")

    height, width = img.shape[:2]
    if width > 1280:
        scaling_factor = 1280 / width
        img = cv2.resize(img, (1280, int(height * scaling_factor)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < MIN_LAPLACIAN_SCORE:
        raise ValueError("IMAGE_TOO_BLURRY")

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

    success, encoded_image = cv2.imencode('.png', denoised)
    if not success:
        raise ValueError("INVALID_IMAGE")
        
    return encoded_image.tobytes()

def extract_text_with_google_vision(processed_image_bytes: bytes) -> str:
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=processed_image_bytes)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise RuntimeError("EXTERNAL_SERVICE_ERROR")
            
        full_text = response.full_text_annotation.text
        return full_text if full_text else ""
    except Exception:
        raise RuntimeError("EXTERNAL_SERVICE_ERROR")

def extract_structured_data_with_gemini(ocr_text: str) -> CedulaVenezolana:
    try:
        client = genai.Client()
        prompt = f"""
        Eres un experto extrayendo datos de cédulas de identidad venezolanas.
        Tu tarea es extraer los siguientes datos y devolverlos estructurados:
        - Número de cédula (solo números)
        - Nombres
        - Apellidos
        - Fecha de nacimiento (formato YYYY-MM-DD o null).
        
        Texto OCR:
        {ocr_text}
        """
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': CedulaVenezolana,
                'temperature': 0.1
            }
        )
        return CedulaVenezolana.model_validate_json(response.text)
    except ValidationError:
        raise ValueError("DATA_EXTRACTION_FAILED")
    except Exception:
        raise RuntimeError("EXTERNAL_SERVICE_ERROR")

# ==========================================
# ENDPOINT DE LA API
# ==========================================
@app.route('/api/extract-id', methods=['POST'])
def extract_id():
    # 1. Validar presencia de archivo
    if 'image' not in request.files:
        return jsonify({"codigo": "FILE_MISSING", "error": "No se adjuntó ninguna imagen en la petición (campo 'image')."}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"codigo": "FILE_MISSING", "error": "No se adjuntó ninguna imagen en la petición (campo 'image')."}), 400

    try:
        image_bytes = file.read()
        
        # 2. Preprocesamiento y validación de nitidez
        optimized_bytes = optimize_id_card(image_bytes)
        
        # 3. Extracción de texto con Google Vision
        text_result = extract_text_with_google_vision(optimized_bytes)
        
        # 4. Validar cantidad mínima de caracteres
        if len(text_result) < MIN_OCR_CHARS:
            return jsonify({"codigo": "INSUFFICIENT_TEXT", "error": "El OCR no logró detectar suficiente texto. Asegúrese de que el documento esté bien iluminado y encuadrado."}), 400
            
        # 5. Validar palabras clave de cédula venezolana
        texto_upper = text_result.upper()
        if not any(palabra in texto_upper for palabra in ["REPUBLICA", "BOLIVARIANA", "CEDULA", "IDENTIDAD", "VENEZUELA"]):
            return jsonify({"codigo": "INVALID_DOCUMENT_TYPE", "error": "El documento enviado no parece pertenecer a una cédula de identidad venezolana."}), 400

        # 6. Estructurar con Gemini
        structured_data = extract_structured_data_with_gemini(text_result)
        
        # 7. Devolver resultado exitoso
        return jsonify(structured_data.model_dump()), 200

    except ValueError as e:
        error_code = str(e)
        mensajes = {
            "INVALID_IMAGE": "El archivo enviado no pudo ser decodificado como imagen.",
            "IMAGE_TOO_BLURRY": "La imagen es demasiado borrosa para procesar. Por favor envíe una imagen más nítida.",
            "DATA_EXTRACTION_FAILED": "El LLM no logró estructurar de forma confiable la información extraída de la imagen."
        }
        msg = mensajes.get(error_code, "Error de validación desconocido.")
        return jsonify({"codigo": error_code, "error": msg}), 400
        
    except RuntimeError as e:
        return jsonify({"codigo": "EXTERNAL_SERVICE_ERROR", "error": "Error interno comunicándose con los servicios de Google Cloud o Gemini."}), 500
        
    except Exception as e:
        return jsonify({"codigo": "INTERNAL_SERVER_ERROR", "error": str(e)}), 500

if __name__ == '__main__':
    # Para desarrollo local, correr en el puerto 5000
    app.run(host='0.0.0.0', port=5000)
