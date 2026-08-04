import sqlite3
import os

# Ruta absoluta para asegurar la creación del archivo de base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pausas_activas.db")

def get_connection():
    """Establece conexión con la base de datos SQLite y retorna los resultados como diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa las tablas necesarias en la base de datos e inserta áreas por defecto."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabla de Áreas (CRUD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            imagen_path TEXT DEFAULT ''
        )
    """)

    # 2. Tabla de Pausas Activas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pausas_activas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            area_nombre TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            color_fondo TEXT DEFAULT '#1E1E2E',
            imagen_path TEXT DEFAULT '',
            completada INTEGER DEFAULT 0
        )
    """)

    # 3. Tabla de Respuestas del Personal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pausa_id INTEGER NOT NULL,
            usuario_pc TEXT NOT NULL,
            area_usuario TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_respuesta DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pausa_id) REFERENCES pausas_activas (id)
        )
    """)

    # Sembrar áreas por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM areas")
    if cursor.fetchone()[0] == 0:
        areas_iniciales = [
            ("Sistemas", ""),
            ("Contabilidad", ""),
            ("Recursos Humanos", ""),
            ("Marketing", ""),
            ("Administración", "")
        ]
        cursor.executemany("INSERT INTO areas (nombre, imagen_path) VALUES (?, ?)", areas_iniciales)

    conn.commit()
    conn.close()
    print(" [ BASE DE DATOS ] Inicializada y estructurada correctamente.")