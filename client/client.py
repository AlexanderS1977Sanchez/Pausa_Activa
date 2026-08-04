import os
import sys
import json
import requests
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socketio
import pygame
from PIL import Image, ImageTk

from config import SERVER_URL, NOMBRE_USUARIO_PC

pygame.mixer.init()
sio = socketio.Client()
event_queue = queue.Queue()
CONFIG_FILE = "user_config.json"

def obtener_o_pedir_area():
    """Lee la configuración local o despliega un selector para registrar el área del usuario."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "area" in data:
                    return data["area"]
        except Exception:
            pass

    # Obtener listado de áreas del servidor
    areas = ["Sistemas", "Contabilidad", "Recursos Humanos", "Ventas"]
    try:
        r = requests.get(f"{SERVER_URL}/api/areas", timeout=3)
        if r.status_code == 200:
            areas = [a["nombre"] for a in r.json()]
    except Exception:
        pass

    win = tk.Tk()
    win.title("Registro de Área / Equipo")
    win.geometry("380x200")
    win.configure(bg="#1E1E2E")
    win.resizable(False, False)

    lbl = tk.Label(win, text="Selecciona el Área a la que perteneces:", font=("Helvetica", 11, "bold"), fg="white", bg="#1E1E2E")
    lbl.pack(pady=15)

    combo = ttk.Combobox(win, values=areas, state="readonly", font=("Helvetica", 11), width=25)
    combo.current(0)
    combo.pack(pady=10)

    area_seleccionada = [areas[0]]

    def guardar():
        area_seleccionada[0] = combo.get()
        with open(CONFIG_FILE, "w") as f:
            json.dump({"area": combo.get()}, f)
        win.destroy()

    btn = tk.Button(win, text="Guardar Selección", command=guardar, bg="#43B581", fg="white", font=("Helvetica", 11, "bold"))
    btn.pack(pady=10)
    win.mainloop()

    return area_seleccionada[0]

AREA_USUARIO = obtener_o_pedir_area()

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
                    self.mostrar_ventana_alerta(data)
        except Exception as e:
            print(f" Error en cola: {e}")
        
        if self.root:
            self.root.after(200, self.procesar_cola_eventos)

    def iniciar_bucle_oculto(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.after(200, self.procesar_cola_eventos)
        self.root.mainloop()

    def mostrar_ventana_alerta(self, data):
        area_destino = data.get("area", "TODAS LAS AREAS")
        
        # Filtro por área
        if area_destino != "TODAS LAS AREAS" and area_destino.upper() != AREA_USUARIO.upper():
            return

        self.pausa_id = data.get("id")
        mensaje = data.get("mensaje", "¡Hora de la Pausa Activa!")
        color_fondo = data.get("color_fondo", "#1E1E2E")
        imagen_path = data.get("imagen_path", "")

        self.root.deiconify()
        self.root.title("Pausa Activa")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=color_fondo)

        self.reproducir_sonido_alerta()

        # Renderizar imagen distintiva de área
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
                print(f"No se pudo cargar la imagen: {e}")

        frame_central = tk.Frame(self.root, bg=color_fondo)
        frame_central.pack(expand=True)

        tk.Label(frame_central, text=mensaje.upper(), font=("Helvetica", 36, "bold"), fg="#FFFFFF", bg=color_fondo).pack(pady=15)
        tk.Label(frame_central, text=f"ÁREA: {AREA_USUARIO.upper()}", font=("Helvetica", 26, "bold"), fg="#FFD166", bg=color_fondo).pack(pady=10)

        # Botón para cambiar imagen del Área
        btn_img = tk.Button(
            frame_central, 
            text="🖼️ Cambiar Imagen Distintiva de mi Área", 
            command=self.cambiar_imagen_area,
            bg="#2A2A3C", fg="white", font=("Helvetica", 10, "bold")
        )
        btn_img.pack(pady=10)

        frame_inst = tk.Frame(self.root, bg="#111118", padx=30, pady=20)
        frame_inst.pack(side="bottom", fill="x", pady=40)
        tk.Label(frame_inst, text="Presiona [ ENTER ] para unirte  |  Presiona [ ESC ] si estás ocupado", font=("Helvetica", 18, "bold"), fg="#FFFFFF", bg="#111118").pack()

        self.root.bind("<Return>", self.evento_unirse)
        self.root.bind("<KP_Enter>", self.evento_unirse)
        self.root.bind("<Escape>", self.evento_ocupado)

    def cambiar_imagen_area(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                res = requests.get(f"{SERVER_URL}/api/areas")
                area_id = None
                for a in res.json():
                    if a["nombre"].upper() == AREA_USUARIO.upper():
                        area_id = a["id"]
                        break

                if area_id:
                    with open(file_path, "rb") as f:
                        requests.put(f"{SERVER_URL}/api/areas/{area_id}", files={"imagen": f})
                    messagebox.showinfo("Éxito", f"Imagen de {AREA_USUARIO} actualizada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar la imagen: {e}")

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
            self.root.withdraw()

    def evento_unirse(self, event=None):
        try:
            sio.emit("respuesta_usuario", {
                "usuario": NOMBRE_USUARIO_PC,
                "area_usuario": AREA_USUARIO,
                "estado": "UNIDO",
                "pausa_id": self.pausa_id
            })
        except Exception:
            pass
        self.detener_audio_y_ocultar()

    def evento_ocupado(self, event=None):
        try:
            sio.emit("respuesta_usuario", {
                "usuario": NOMBRE_USUARIO_PC,
                "area_usuario": AREA_USUARIO,
                "estado": "OCUPADO",
                "pausa_id": self.pausa_id
            })
        except Exception:
            pass
        self.detener_audio_y_ocultar()

app_gui = AppVentanaAlerta()

@sio.event
def alerta_pausa(data):
    event_queue.put(("alerta_pausa", data))

def conectar_socket():
    try:
        sio.connect(SERVER_URL)
        sio.wait()
    except Exception:
        pass

if __name__ == "__main__":
    socket_thread = threading.Thread(target=conectar_socket, daemon=True)
    socket_thread.start()
    app_gui.iniciar_bucle_oculto()