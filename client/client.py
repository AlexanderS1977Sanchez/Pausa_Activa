import os
import sys
import json
import requests
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import socketio
import pygame
from PIL import Image, ImageTk

from config import SERVER_URL

pygame.mixer.init()
sio = socketio.Client()
event_queue = queue.Queue()
CONFIG_FILE = "user_config.json"

def obtener_o_pedir_datos_usuario():
    """Lee la configuración local o despliega un selector para registrar nombre y área."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "area" in data and "usuario" in data:
                    return data["usuario"], data["area"]
        except Exception:
            pass

    areas = ["Sistemas", "Contabilidad", "Recursos Humanos", "Ventas", "Marketing", "Administración"]
    try:
        r = requests.get(f"{SERVER_URL}/api/areas", timeout=3)
        if r.status_code == 200:
            areas = [a["nombre"] for a in r.json()]
    except Exception:
        pass

    win = tk.Tk()
    win.title("Registro del Equipo")
    win.geometry("380x260")
    win.configure(bg="#1E1E2E")
    win.resizable(False, False)
    win.eval('tk::PlaceWindow . center')

    tk.Label(win, text="Registro de Equipo / Cliente", font=("Helvetica", 12, "bold"), fg="#FFD166", bg="#1E1E2E").pack(pady=10)

    tk.Label(win, text="Nombre del Usuario / Equipo:", font=("Helvetica", 10), fg="white", bg="#1E1E2E").pack(anchor="w", padx=35, pady=(5, 2))
    entry_usuario = tk.Entry(win, font=("Helvetica", 10), width=30)
    entry_usuario.pack(padx=35, pady=(0, 10))

    tk.Label(win, text="Selecciona tu Área:", font=("Helvetica", 10), fg="white", bg="#1E1E2E").pack(anchor="w", padx=35, pady=(5, 2))
    combo = ttk.Combobox(win, values=areas, state="readonly", font=("Helvetica", 10), width=28)
    if areas:
        combo.current(0)
    combo.pack(padx=35, pady=(0, 15))

    resultado = {}

    def guardar():
        usr = entry_usuario.get().strip()
        area_sel = combo.get().strip()
        if not usr:
            messagebox.showwarning("Atención", "Ingresa tu nombre para continuar.", parent=win)
            return
        resultado["usuario"] = usr
        resultado["area"] = area_sel
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"usuario": usr, "area": area_sel}, f, indent=4)
        win.destroy()

    btn = tk.Button(win, text="Guardar Registro", command=guardar, bg="#43B581", fg="white", font=("Helvetica", 10, "bold"), cursor="hand2")
    btn.pack(pady=5)
    win.mainloop()

    return resultado.get("usuario", "Usuario_PC"), resultado.get("area", areas[0] if areas else "General")

NOMBRE_USUARIO, AREA_USUARIO = obtener_o_pedir_datos_usuario()
print(f" [ CLIENTE INICIADO ] Usuario: {NOMBRE_USUARIO} | Área Registrada: {AREA_USUARIO}")

class AppVentanaAlerta:
    def __init__(self):
        self.root = None
        self.pausa_id = None
        self.bg_image_tk = None

    def procesar_cola_eventos(self):
        try:
            while not event_queue.empty():
                evento, data = event_queue.get_nowait()
                if evento == "alerta_pausa":
                    print(f" [ EVENTO RECIBIDO EN CLIENTE ] Datos: {data}")
                    self.mostrar_ventana_alerta(data)
        except Exception as e:
            print(f" Error procesando evento en GUI: {e}")
        
        if self.root:
            self.root.after(100, self.procesar_cola_eventos)

    def iniciar_bucle_oculto(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Inicia oculto en la bandeja / background
        self.root.after(100, self.procesar_cola_eventos)
        self.root.mainloop()

    def mostrar_ventana_alerta(self, data):
        area_destino = str(data.get("area", "TODAS LAS AREAS")).strip().upper()
        mi_area = str(AREA_USUARIO).strip().upper()
        
        # Validación de Área
        if area_destino != "TODAS LAS AREAS" and area_destino != mi_area:
            print(f" [ ALERTA IGNORADA ] La alerta es para '{area_destino}', pero este equipo está registrado como '{mi_area}'")
            return

        print(" [ DESPLEGANDO PANTALLA COMPLETA ]...")
        self.pausa_id = data.get("id")
        mensaje = data.get("mensaje", "¡Hora de la Pausa Activa!")
        color_fondo = data.get("color_fondo", "#1E1E2E")
        imagen_path = data.get("imagen_path", "")

        # Limpiar widgets antiguos de la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Configuración para forzar la ventana emergente sobre todo en Windows
        self.root.deiconify()
        self.root.state('normal')
        self.root.title("Pausa Activa")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.configure(bg=color_fondo)

        self.reproducir_sonido_alerta()

        # Cargar imagen de fondo si aplica
        if imagen_path:
            try:
                full_url = f"{SERVER_URL}{imagen_path}" if imagen_path.startswith("/") else f"{SERVER_URL}/{imagen_path}"
                img_data = requests.get(full_url, timeout=3).content
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                img = img.resize((sw, sh), Image.Resampling.LANCZOS)
                self.bg_image_tk = ImageTk.PhotoImage(img)

                label_bg = tk.Label(self.root, image=self.bg_image_tk)
                label_bg.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print(f" No se pudo cargar la imagen de fondo: {e}")

        frame_central = tk.Frame(self.root, bg=color_fondo)
        frame_central.pack(expand=True)

        tk.Label(frame_central, text=mensaje.upper(), font=("Helvetica", 36, "bold"), fg="#FFFFFF", bg=color_fondo).pack(pady=15)
        tk.Label(frame_central, text=f"USUARIO: {NOMBRE_USUARIO.upper()} | ÁREA: {AREA_USUARIO.upper()}", font=("Helvetica", 20, "bold"), fg="#FFD166", bg=color_fondo).pack(pady=10)

        frame_inst = tk.Frame(self.root, bg="#111118", padx=30, pady=20)
        frame_inst.pack(side="bottom", fill="x", pady=40)
        tk.Label(frame_inst, text="Presiona [ ENTER ] para unirte   |   Presiona [ ESC ] si estás ocupado", font=("Helvetica", 18, "bold"), fg="#FFFFFF", bg="#111118").pack()

        # Bindings de teclas
        self.root.bind("<Return>", self.evento_unirse)
        self.root.bind("<KP_Enter>", self.evento_unirse)
        self.root.bind("<Escape>", self.evento_ocupado)

    def reproducir_sonido_alerta(self):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ruta_audio = os.path.join(base_dir, "assets", "alerta.mp3")
        if os.path.exists(ruta_audio):
            try:
                pygame.mixer.music.load(ruta_audio)
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    def detener_audio_y_ocultar(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if self.root:
            for widget in self.root.winfo_children():
                widget.destroy()
            self.root.attributes("-topmost", False)
            self.root.withdraw()

    def evento_unirse(self, event=None):
        try:
            sio.emit("respuesta_usuario", {
                "usuario": NOMBRE_USUARIO,
                "area_usuario": AREA_USUARIO,
                "estado": "UNIDO",
                "pausa_id": self.pausa_id
            })
            print(" [ RESPUESTA ENVIADA ] Estado: UNIDO")
        except Exception as e:
            print(f" Error emitiendo respuesta: {e}")
        self.detener_audio_y_ocultar()

    def evento_ocupado(self, event=None):
        try:
            sio.emit("respuesta_usuario", {
                "usuario": NOMBRE_USUARIO,
                "area_usuario": AREA_USUARIO,
                "estado": "OCUPADO",
                "pausa_id": self.pausa_id
            })
            print(" [ RESPUESTA ENVIADA ] Estado: OCUPADO")
        except Exception as e:
            print(f" Error emitiendo respuesta: {e}")
        self.detener_audio_y_ocultar()

app_gui = AppVentanaAlerta()

@sio.event
def alerta_pausa(data):
    # Pasar el evento a la cola para que lo procese la GUI en su hilo principal
    event_queue.put(("alerta_pausa", data))

def conectar_socket():
    try:
        sio.connect(SERVER_URL)
        print(" [ SOCKET.IO ] Conectado exitosamente al servidor.")
        sio.wait()
    except Exception as e:
        print(f" Error de conexión Socket.IO: {e}")

if __name__ == "__main__":
    socket_thread = threading.Thread(target=conectar_socket, daemon=True)
    socket_thread.start()
    app_gui.iniciar_bucle_oculto()