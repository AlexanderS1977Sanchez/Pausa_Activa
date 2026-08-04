from pydantic import BaseModel
from typing import Optional

class AreaCreate(BaseModel):
    nombre: str

class PausaCreate(BaseModel):
    fecha: str          # Formato YYYY-MM-DD
    hora: str           # Formato HH:MM
    area_nombre: str
    mensaje: Optional[str] = "¡Hora de realizar la Pausa Activa!"
    color_fondo: Optional[str] = "#1E1E2E"
    imagen_path: Optional[str] = ""

class RespuestaCreate(BaseModel):
    pausa_id: int
    usuario: str
    estado: str         # "UNIDO" u "OCUPADO"