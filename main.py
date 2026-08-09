import os
import cv2
import numpy as np
from dotenv import load_dotenv
from google.cloud import vision
from google import genai
from pydantic import BaseModel, Field
from typing import Optional

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# ==========================================
# 1. ESQUEMA PYDANTIC
# ==========================================
class CedulaVenezolana(BaseModel):
    cedula: int = Field(..., description="Número de cédula de identidad, solo números, sin puntos ni letras")
    nombres: str = Field(..., description="Nombres de la persona, en mayúsculas")
    apellidos: str = Field(..., description="Apellidos de la persona, en mayúsculas")
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento en formato exacto YYYY-MM-DD")

# ==========================================
# 2. PREPROCESAMIENTO DE IMAGEN
# ==========================================
def optimize_id_card(image_bytes: bytes) -> bytes:
    """
    Aplica pre-procesamiento para mejorar el OCR sin binarizar.
    Redimensiona, pasa a grises y mejora el contraste (CLAHE).
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("No se pudo decodificar la imagen de entrada.")

    # Redimensionar si es muy grande
    height, width = img.shape[:2]
    if width > 1280:
        scaling_factor = 1280 / width
        img = cv2.resize(img, (1280, int(height * scaling_factor)))

    # Escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Mejorar contraste local con CLAHE (Ecualización de histograma)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Reducción de ruido sutil manteniendo bordes afilados
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

    # Codificar la imagen procesada de vuelta a bytes PNG
    success, encoded_image = cv2.imencode('.png', denoised)
    if not success:
        raise RuntimeError("Fallo al codificar la imagen procesada.")
        
    return encoded_image.tobytes()

# ==========================================
# 3. EXTRACCIÓN DE TEXTO CON GOOGLE VISION
# ==========================================
def extract_text_with_google_vision(processed_image_bytes: bytes) -> str:
    """
    Envía la imagen a Google Cloud Vision API.
    """
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=processed_image_bytes)

    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise RuntimeError(f"Error en Google Cloud Vision API: {response.error.message}")

    full_text = response.full_text_annotation.text
    return full_text if full_text else ""

# ==========================================
# 4. ESTRUCTURACIÓN CON GEMINI
# ==========================================
def extract_structured_data_with_gemini(ocr_text: str) -> CedulaVenezolana:
    """
    Envía el texto crudo del OCR a Gemini para estructurarlo según el esquema Pydantic.
    """
    client = genai.Client()
    
    prompt = f"""
    Eres un experto extrayendo datos de cédulas de identidad venezolanas.
    A continuación te proporciono el texto crudo extraído mediante OCR.
    
    Tu tarea es extraer los siguientes datos y devolverlos estructurados:
    - Número de cédula (solo los números, ignora V- o E-)
    - Nombres
    - Apellidos
    - Fecha de nacimiento (conviértela y formatea ESTRICTAMENTE como YYYY-MM-DD. Si no logras descifrarla, devuelve null).
    
    Texto OCR:
    {ocr_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': CedulaVenezolana,
            'temperature': 0.1 # Temperatura baja para que sea determinista
        }
    )
    
    try:
        structured_data = CedulaVenezolana.model_validate_json(response.text)
        return structured_data
    except Exception as e:
        raise RuntimeError(f"Fallo validando los datos con Pydantic: {e}")

# ==========================================
# EJEMPLO DE USO
# ==========================================
if __name__ == "__main__":
    sample_path = "cedula_test.jpeg"
    
    if os.path.exists(sample_path):
        try:
            with open(sample_path, "rb") as f:
                raw_bytes = f.read()
                
            print("1. Optimizando imagen (Grises + CLAHE)...")
            optimized_bytes = optimize_id_card(raw_bytes)
            
            print("2. Extrayendo texto con Google Vision API...")
            text_result = extract_text_with_google_vision(optimized_bytes)
            print(f"   [Texto extraído: {len(text_result)} caracteres]")
            
            print("3. Estructurando datos con Gemini 2.5 Flash...")
            structured_data = extract_structured_data_with_gemini(text_result)
            
            print("\n--- RESULTADO FINAL (VALIDADO) ---")
            print(structured_data.model_dump_json(indent=4))
            
        except Exception as e:
            print(f"\n[ERROR] Ocurrió un problema durante el proceso:\n{e}")
    else:
        print(f"Por favor, coloca una imagen llamada '{sample_path}' en este directorio.")
