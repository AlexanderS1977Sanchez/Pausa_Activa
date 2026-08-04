import os
import shutil
import socketio
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import init_db, get_connection
from app.models import PausaCreate
from app.scheduler import verificar_y_emitir_pausas

# Configuración del servidor Socket.io
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
fastapi_app = FastAPI(title="Servidor Local de Pausas Activas")

# Crear carpeta para almacenamiento de imágenes
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
fastapi_app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = socketio.ASGIApp(sio, fastapi_app)
scheduler = AsyncIOScheduler()

init_db()

# --- EVENTOS SOCKET.IO ---

@sio.event
async def connect(sid, environ):
    print(f" [ RED LOCAL ] Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f" [ RED LOCAL ] Cliente desconectado: {sid}")

@sio.event
async def respuesta_usuario(sid, data):
    usuario = data.get("usuario")
    area_usuario = data.get("area_usuario", "Sin Área")
    estado = data.get("estado")
    pausa_id = data.get("pausa_id")

    if not usuario or not estado or not pausa_id:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO respuestas (pausa_id, usuario_pc, area_usuario, estado) VALUES (?, ?, ?, ?)",
        (pausa_id, usuario, area_usuario, estado)
    )
    conn.commit()
    conn.close()

# --- RUTAS REST DE ÁREAS (CRUD) ---

@fastapi_app.get("/api/areas")
async def listar_areas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM areas ORDER BY nombre ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@fastapi_app.post("/api/areas")
async def crear_area(nombre: str = Form(...), imagen: UploadFile = File(None)):
    img_path = ""
    if imagen:
        file_location = os.path.join(UPLOADS_DIR, imagen.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        img_path = f"/uploads/{imagen.filename}"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO areas (nombre, imagen_path) VALUES (?, ?)", (nombre, img_path))
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="El área ya existe.")
    conn.close()
    return {"status": "ok", "mensaje": "Área creada exitosamente"}

@fastapi_app.put("/api/areas/{area_id}")
async def actualizar_area(area_id: int, nombre: str = Form(None), imagen: UploadFile = File(None)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM areas WHERE id = ?", (area_id,))
    area = cursor.fetchone()
    if not area:
        conn.close()
        raise HTTPException(status_code=404, detail="Área no encontrada")

    nuevo_nombre = nombre if nombre else area["nombre"]
    img_path = area["imagen_path"]

    if imagen:
        file_location = os.path.join(UPLOADS_DIR, imagen.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        img_path = f"/uploads/{imagen.filename}"

    cursor.execute("UPDATE areas SET nombre = ?, imagen_path = ? WHERE id = ?", (nuevo_nombre, img_path, area_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "mensaje": "Área actualizada"}

@fastapi_app.delete("/api/areas/{area_id}")
async def eliminar_area(area_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM areas WHERE id = ?", (area_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "mensaje": "Área eliminada"}

# --- RUTAS REST DE PAUSAS ---

@fastapi_app.post("/api/pausas")
async def crear_pausa(pausa: PausaCreate):
    fecha_hora = f"{pausa.fecha} {pausa.hora}"
    
    img_path = ""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT imagen_path FROM areas WHERE nombre = ?", (pausa.area_nombre,))
    area_row = cursor.fetchone()
    if area_row and area_row["imagen_path"]:
        img_path = area_row["imagen_path"]

    cursor.execute(
        """
        INSERT INTO pausas_activas (fecha_hora, area_nombre, mensaje, color_fondo, imagen_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        (fecha_hora, pausa.area_nombre, pausa.mensaje, pausa.color_fondo, img_path)
    )
    conn.commit()
    pausa_id = cursor.lastrowid
    conn.close()
    return {"status": "ok", "pausa_id": pausa_id, "mensaje": "Pausa programada exitosamente"}

@fastapi_app.get("/api/pausas")
async def listar_pausas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pausas_activas ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@fastapi_app.on_event("startup")
async def startup_event():
    scheduler.add_job(verificar_y_emitir_pausas, 'interval', seconds=15, args=[sio])
    scheduler.start()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)