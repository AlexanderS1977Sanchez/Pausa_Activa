import os
import sys

# Agregar la raíz al sys.path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
import tkinter as tk
from tkinter import ttk
import requests
import socketio
from PIL import Image, ImageTk, ImageSequence

from config import SERVER_URL, NOMBRE_USUARIO_PC

APPDATA_DIR = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'PausasActivasApp')
os.makedirs(APPDATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APPDATA_DIR, 'user_config.json')

# Inicializar Socket.IO cliente con reconexión automática robusta
sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5)

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"area_id": None, "area_nombre": "Sin Seleccionar"}

def guardar_config(area_id, area_nombre):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"area_id": area_id, "area_nombre": area_nombre}, f)


class VentanaConfigInicial(tk.Toplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.title("Configuración de Área")
        self.geometry("380x220")
        self.configure(bg="#0F172A")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback

        tk.Label(self, text="SELECCIÓN DE ÁREA DE TRABAJO", font=("Segoe UI", 11, "bold"), bg="#0F172A", fg="#38BDF8").pack(pady=(15, 5))
        tk.Label(self, text=f"Equipo: {NOMBRE_USUARIO_PC}", font=("Segoe UI", 9), bg="#0F172A", fg="#94A3B8").pack(pady=(0, 15))

        self.combo = ttk.Combobox(self, state="readonly", font=("Segoe UI", 10))
        self.combo.pack(fill="x", padx=30, pady=5)

        btn = tk.Button(self, text="Guardar y Continuar", font=("Segoe UI", 10, "bold"), bg="#10B981", fg="white", bd=0, cursor="hand2", command=self.guardar)
        btn.pack(fill="x", padx=30, pady=15, ipady=5)

        self.areas_data = {}
        self.obtener_areas()

    def obtener_areas(self):
        try:
            res = requests.get(f"{SERVER_URL}/api/areas", timeout=3)
            if res.status_code == 200:
                areas = res.json()
                self.areas_data = {a["nombre"]: a["id"] for a in areas}
                self.combo["values"] = list(self.areas_data.keys())
                if areas:
                    self.combo.current(0)
        except Exception as e:
            print(f"Error conectando al servidor: {e}")

    def guardar(self):
        nom = self.combo.get()
        a_id = self.areas_data.get(nom)
        if a_id:
            guardar_config(a_id, nom)
            if sio.connected:
                sio.emit("registrar_cliente", {"usuario_pc": NOMBRE_USUARIO_PC, "area_id": a_id})
            self.on_save_callback()
            self.destroy()


class VentanaAlertaPausa:
    def __init__(self, root_app, data):
        self.root_app = root_app
        self.data = data
        
        # Crear la ventana de alerta como Toplevel dependiente de la app principal
        self.root = tk.Toplevel(self.root_app)
        self.root.title("Pausa Activa")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        color_fondo = self.data.get("color_fondo") or "#0F172A"
        self.root.config(bg=color_fondo)

        # Forzar el foco absoluto para que pase al frente de cualquier otra app
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.grab_set()

        # Atajos de Teclado
        self.root.bind("<Return>", lambda e: self.responder("completado"))
        self.root.bind("<Escape>", lambda e: self.responder("ocupado"))

        # Variables para la animación GIF
        self.frames = []
        self.frame_index = 0
        self.anim_job = None

        self.construir_ui()

    def construir_ui(self):
        cfg = cargar_config()
        nombre_persona = self.data.get("nombre_persona") or NOMBRE_USUARIO_PC
        nombre_area = cfg.get("area_nombre") or self.data.get("nombre_area") or "Área General"

        card = tk.Frame(self.root, bg="#1E293B", padx=60, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text=f"¡Hola, {nombre_persona}!", font=("Segoe UI", 24, "bold"), fg="#38BDF8", bg="#1E293B").pack(pady=(0, 2))
        tk.Label(card, text=f"Área: {nombre_area}", font=("Segoe UI", 11), fg="#94A3B8", bg="#1E293B").pack(pady=(0, 10))

        tk.Label(card, text="ES HORA DE TU PAUSA ACTIVA", font=("Segoe UI", 15, "bold"), fg="#F8FAFC", bg="#1E293B").pack(pady=(0, 10))

        # --- CONTENEDOR DEL GIF ANIMADO (Compatibilidad PyInstaller) ---
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        gif_path = os.path.join(base_dir, "assets", "pausa.gif")

        if os.path.exists(gif_path):
            try:
                self.gif_image = Image.open(gif_path)
                # Redimensionamiento manteniendo canal de transparencia
                self.frames = [
                    ImageTk.PhotoImage(frame.copy().convert("RGBA").resize((240, 240), Image.Resampling.LANCZOS))
                    for frame in ImageSequence.Iterator(self.gif_image)
                ]
                
                self.lbl_gif = tk.Label(card, bg="#1E293B", bd=0)
                self.lbl_gif.pack(pady=(0, 15))
                self.animar_gif()
            except Exception as e:
                print(f"Error cargando GIF: {e}")

        mensaje_texto = self.data.get("mensaje", "")
        if mensaje_texto:
            tk.Label(card, text=mensaje_texto, font=("Segoe UI", 12), fg="#CBD5E1", bg="#1E293B", wraplength=550, justify="center").pack(pady=(0, 20))

        f_btn = tk.Frame(card, bg="#1E293B")
        f_btn.pack(fill="x")

        btn_si = tk.Button(f_btn, text="[ENTER] Asistiré", font=("Segoe UI", 11, "bold"), bg="#10B981", fg="white", bd=0, padx=20, pady=8, cursor="hand2", command=lambda: self.responder("completado"))
        btn_si.pack(side="left", expand=True, padx=5)

        btn_no = tk.Button(f_btn, text="[ESC] Estoy Ocupado", font=("Segoe UI", 11, "bold"), bg="#EF4444", fg="white", bd=0, padx=20, pady=8, cursor="hand2", command=lambda: self.responder("ocupado"))
        btn_no.pack(side="right", expand=True, padx=5)

    def animar_gif(self):
        if not self.frames:
            return
            
        frame = self.frames[self.frame_index]
        self.lbl_gif.configure(image=frame)
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        duracion = self.gif_image.info.get("duration", 50)
        self.anim_job = self.root.after(duracion, self.animar_gif)

    def responder(self, estado):
        # Detener el bucle after() del GIF para evitar consumo innecesario de memoria
        if self.anim_job:
            self.root.after_cancel(self.anim_job)

        if sio.connected:
            cfg = cargar_config()
            sio.emit("confirmacion_pausa", {
                "pausa_id": self.data.get("id"),
                "usuario_pc": NOMBRE_USUARIO_PC,
                "area_id": cfg.get("area_id"),
                "estado": estado
            })
        try:
            self.root.grab_release()
            self.root.destroy()
        except Exception:
            pass


class ClienteApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Ocultar la ventana principal en background

        # Registrar eventos de Socket.IO
        @sio.event
        def connect():
            print(" [ Conectado al Servidor ]")
            cfg = cargar_config()
            sio.emit("registrar_cliente", {
                "usuario_pc": NOMBRE_USUARIO_PC,
                "area_id": cfg.get("area_id")
            })

        @sio.event
        def disconnect():
            print(" [ Desconectado del Servidor ]")

        @sio.event
        def alerta_pausa(data):
            # Invocar en el hilo principal de Tkinter
            self.root.after(0, lambda: VentanaAlertaPausa(self.root, data))

        # Iniciar hilo de conexión al servidor en background
        threading.Thread(target=self.conectar_servidor_loop, daemon=True).start()

        cfg = cargar_config()
        if not cfg.get("area_id"):
            VentanaConfigInicial(self.root, lambda: None)

    def conectar_servidor_loop(self):
        while True:
            try:
                if not sio.connected:
                    sio.connect(SERVER_URL, wait_timeout=10)
                sio.sleep(5)
            except Exception:
                time.sleep(5)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ClienteApp()
    app.run()