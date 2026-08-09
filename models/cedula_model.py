from pydantic import BaseModel, Field
from typing import Optional

class CedulaVenezolana(BaseModel):
    cedula: int = Field(..., description="Número de cédula de identidad, solo números, sin puntos ni letras")
    nombres: str = Field(..., description="Nombres de la persona, en mayúsculas")
    apellidos: str = Field(..., description="Apellidos de la persona, en mayúsculas")
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento en formato exacto YYYY-MM-DD")
