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

## Ejecución (Servidor Web)

Asegúrate de tener tu entorno virtual activo y ejecuta el archivo principal para levantar la API en el puerto `5000`:

```bash
python app.py
```

### Probar el Endpoint
El servidor esperará peticiones `POST` en `/api/extract-id`. Puedes probarlo enviando una imagen con `curl`:

```bash
curl -X POST http://localhost:5000/api/extract-id -F "image=@tu_foto_de_cedula.jpeg"
```
