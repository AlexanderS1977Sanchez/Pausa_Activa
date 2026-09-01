from pydantic import BaseModel, ConfigDict
from typing import Optional

class AreaCreate(BaseModel):
    nombre: str

class PausaBase(BaseModel):
    fecha: str          # Formato YYYY-MM-DD
    hora: str           # Formato HH:MM
    area_nombre: str
    mensaje: Optional[str] = "¡Hora de realizar la Pausa Activa!"
    color_fondo: Optional[str] = "#1E1E2E"
    imagen_path: Optional[str] = ""

class PausaCreate(PausaBase):
    pass

# ESQUEMA DE SALIDA (Este es el que te falta para la tabla del Admin)
class PausaResponse(PausaBase):
    id: int
    titulo: Optional[str] = "Pausa Activa"
    completada: Optional[int] = 0
    area_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class RespuestaCreate(BaseModel):
    pausa_id: int
    usuario: str
    estado: str         