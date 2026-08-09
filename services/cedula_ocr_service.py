import cv2
import numpy as np
from google.cloud import vision
from google import genai
from pydantic import ValidationError
from config.config import Config
from models.cedula_model import CedulaVenezolana

class CedulaOcrService:
    
    @staticmethod
    def process_id_card(image_bytes: bytes) -> dict:
        optimized_bytes = CedulaOcrService._optimize_image(image_bytes)
        text_result = CedulaOcrService._extract_text(optimized_bytes)
        
        # Validación de cantidad mínima de caracteres
        if len(text_result) < Config.MIN_OCR_CHARS:
            raise ValueError("INSUFFICIENT_TEXT")
            
        # Validación de palabras clave de cédula venezolana
        texto_upper = text_result.upper()
        if not any(palabra in texto_upper for palabra in ["REPUBLICA", "BOLIVARIANA", "CEDULA", "IDENTIDAD", "VENEZUELA"]):
            raise ValueError("INVALID_DOCUMENT_TYPE")

        structured_data = CedulaOcrService._extract_structured_data(text_result)
        return structured_data.model_dump()

    @staticmethod
    def _optimize_image(image_bytes: bytes) -> bytes:
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
        if laplacian_var < Config.MIN_LAPLACIAN_SCORE:
            raise ValueError("IMAGE_TOO_BLURRY")

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

        success, encoded_image = cv2.imencode('.png', denoised)
        if not success:
            raise ValueError("INVALID_IMAGE")
            
        return encoded_image.tobytes()

    @staticmethod
    def _extract_text(processed_image_bytes: bytes) -> str:
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

    @staticmethod
    def _extract_structured_data(ocr_text: str) -> CedulaVenezolana:
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
