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

## Ejecución de la API

La aplicación ha sido refactorizada usando una arquitectura Modelo-Servicio-Controlador. Para encender el servidor Flask, primero debes activar tu entorno virtual y luego ejecutar el script:

1. Activa el entorno virtual en tu terminal:
```powershell
.\venv\Scripts\activate
```

2. Ejecuta el archivo principal:
```bash
python app.py
```

El servidor quedará escuchando en `http://localhost:5000`.

---

## Cómo invocar el Endpoint

La API expone una única ruta para procesar las imágenes:

**Endpoint:** `POST /api/extract-id`

### Usando cURL (Terminal)

```bash
curl -X POST http://localhost:5000/api/extract-id -F "image=@ruta/a/tu_foto_de_cedula.jpeg"
```

### Respuestas
*   **Éxito (HTTP 200)**: Devolverá un JSON con `cedula`, `nombres`, `apellidos` y `fecha_nacimiento`.
*   **Fallo (HTTP 400/500)**: Devolverá un JSON con `codigo` y `error` detallando si la imagen estaba borrosa (`IMAGE_TOO_BLURRY`), mal encuadrada (`INSUFFICIENT_TEXT`), o si hubo problemas con las APIs de Google.
