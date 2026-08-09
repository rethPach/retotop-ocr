# OCR Cédula Venezolana (Vision + Gemini)

Este proyecto extrae datos estructurados (Cédula, Nombres, Apellidos, Fecha de Nacimiento) a partir de una imagen de una cédula de identidad venezolana.

Utiliza **Google Cloud Vision** para un OCR robusto en documentos con texturas/hologramas, y **Google GenAI (Gemini)** junto con **Pydantic** para limpiar, estructurar y validar la información.

## Requisitos Previos

Necesitas dos cosas de Google:
1.  **Clave API de Gemini:** Obtenla en [Google AI Studio](https://aistudio.google.com/).
2.  **Credenciales de Google Cloud Vision:** Un archivo JSON de cuenta de servicio de GCP con permisos para Cloud Vision API.

## Configuración del Entorno

Asegúrate de llenar tus credenciales en el archivo `.env`:
```env
GEMINI_API_KEY="TU_CLAVE_API_DE_GEMINI"
GOOGLE_APPLICATION_CREDENTIALS="ruta/al/archivo/credenciales-gcp.json"
```

## Ejecución

Coloca una imagen de prueba llamada `cedula_test.jpg` en este directorio, asegúrate de tener tu entorno virtual activo y ejecuta el script:

```bash
python main.py
```
