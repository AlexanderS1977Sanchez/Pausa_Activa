import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from config import SERVER_URL

class VentanaAdminPausas:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - Configuración de Pausas Activas")
        self.root.geometry("900x650")
        self.root.resizable(False, False)
        
        self.bg_color = "#1E1E2E"
        self.card_color = "#2A2A3C"
        self.accent_color = "#7289DA"
        self.fg_color = "#FFFFFF"
        self.color_seleccionado = "#1E1E2E"

        self.root.configure(bg=self.bg_color)
        self.crear_interfaz()
        self.cargar_areas()
        self.cargar_tabla_pausas()

    def crear_interfaz(self):
        lbl_titulo = tk.Label(self.root, text="⚙️ Configuración de Pausa Activa", font=("Helvetica", 20, "bold"), bg=self.bg_color, fg=self.fg_color)
        lbl_titulo.pack(pady=15)

        frame_main = tk.Frame(self.root, bg=self.bg_color)
        frame_main.pack(fill="both", expand=True, padx=20, pady=10)

        # --- FORMULARIO DE PROGRAMACIÓN ---
        frame_form = tk.LabelFrame(frame_main, text=" Programar Nueva Alerta ", font=("Helvetica", 11, "bold"), bg=self.card_color, fg=self.accent_color, padx=15, pady=10)
        frame_form.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(frame_form, text="Fecha (AAAA-MM-DD):", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_fecha = tk.Entry(frame_form, font=("Helvetica", 10), width=22)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha.pack(pady=(0, 8))

        tk.Label(frame_form, text="Hora (HH:MM) 24 hrs:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_hora = tk.Entry(frame_form, font=("Helvetica", 10), width=22)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.entry_hora.pack(pady=(0, 8))

        tk.Label(frame_form, text="Área Convocada:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.combo_area = ttk.Combobox(frame_form, state="readonly", font=("Helvetica", 10), width=20)
        self.combo_area.pack(pady=(0, 8))

        tk.Label(frame_form, text="Mensaje de Alerta:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_mensaje = tk.Entry(frame_form, font=("Helvetica", 10), width=22)
        self.entry_mensaje.insert(0, "¡Hora de la Pausa Activa!")
        self.entry_mensaje.pack(pady=(0, 8))

        # --- SELECTOR DE 6 COLORES PRIMARIOS (1-CLICK) ---
        tk.Label(frame_form, text="Color de Fondo (1-Clic):", bg=self.card_color, fg=self.fg_color).pack(anchor="w", pady=(5, 2))
        
        frame_colores = tk.Frame(frame_form, bg=self.card_color)
        frame_colores.pack(pady=5)

        colores_primarios = [
            ("#1E1E2E", "Oscuro"),
            ("#1E3A8A", "Azul"),
            ("#991B1B", "Rojo"),
            ("#065F46", "Verde"),
            ("#D97706", "Naranja"),
            ("#5B21B6", "Morado")
        ]

        for hex_code, nombre in colores_primarios:
            btn_c = tk.Button(
                frame_colores, 
                bg=hex_code, 
                width=3, height=1, 
                cursor="hand2",
                command=lambda c=hex_code: self.seleccionar_color(c)
            )
            btn_c.pack(side="left", padx=2)

        self.lbl_color_actual = tk.Label(frame_form, text="Color: #1E1E2E", bg=self.color_seleccionado, fg="white", font=("Helvetica", 9, "bold"), pady=3)
        self.lbl_color_actual.pack(fill="x", pady=5)

        btn_programar = tk.Button(frame_form, text="🚀 Guardar y Programar", font=("Helvetica", 11, "bold"), bg="#43B581", fg="white", cursor="hand2", command=self.guardar_pausa)
        btn_programar.pack(fill="x", pady=(10, 5))

        # --- PESTAÑAS: PAUSAS Y CRUD DE ÁREAS ---
        frame_derecho = tk.Frame(frame_main, bg=self.bg_color)
        frame_derecho.pack(side="right", fill="both", expand=True)

        notebook = ttk.Notebook(frame_derecho)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Pausas Programadas
        tab_pausas = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(tab_pausas, text="Pausas Programadas")

        cols = ("ID", "Fecha/Hora", "Área", "Estado")
        self.tree = ttk.Treeview(tab_pausas, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=5)

        # Tab 2: CRUD de Áreas
        tab_areas = tk.Frame(notebook, bg=self.card_color)
        notebook.add(tab_areas, text="Gestión de Áreas (CRUD)")

        tk.Label(tab_areas, text="Nombre del Área:", bg=self.card_color, fg="white", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
        self.entry_nueva_area = tk.Entry(tab_areas, font=("Helvetica", 11), width=25)
        self.entry_nueva_area.pack(anchor="w", padx=15, pady=5)

        btn_crear_a = tk.Button(tab_areas, text="➕ Crear Área", bg="#43B581", fg="white", font=("Helvetica", 10, "bold"), command=self.crear_area)
        btn_crear_a.pack(anchor="w", padx=15, pady=5)

        self.list_areas = tk.Listbox(tab_areas, font=("Helvetica", 10), bg="#1E1E2E", fg="white", height=7)
        self.list_areas.pack(fill="x", padx=15, pady=10)

        btn_elim_a = tk.Button(tab_areas, text="❌ Eliminar Área Seleccionada", bg="#F04747", fg="white", font=("Helvetica", 10, "bold"), command=self.eliminar_area)
        btn_elim_a.pack(anchor="w", padx=15, pady=5)

    def seleccionar_color(self, hex_code):
        self.color_seleccionado = hex_code
        self.lbl_color_actual.configure(text=f"Color: {hex_code}", bg=hex_code)

    def cargar_areas(self):
        try:
            res = requests.get(f"{SERVER_URL}/api/areas", timeout=3)
            if res.status_code == 200:
                areas = res.json()
                nombres = [a["nombre"] for a in areas]
                nombres_combo = ["TODAS LAS AREAS"] + nombres
                self.combo_area["values"] = nombres_combo
                self.combo_area.current(0)

                self.list_areas.delete(0, tk.END)
                for a in areas:
                    self.list_areas.insert(tk.END, f"{a['id']} - {a['nombre']}")
        except Exception as e:
            print(f"Error cargando áreas: {e}")

    def crear_area(self):
        nombre = self.entry_nueva_area.get().strip()
        if nombre:
            try:
                requests.post(f"{SERVER_URL}/api/areas", data={"nombre": nombre})
                self.entry_nueva_area.delete(0, tk.END)
                self.cargar_areas()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def eliminar_area(self):
        sel = self.list_areas.curselection()
        if sel:
            texto = self.list_areas.get(sel[0])
            area_id = texto.split(" - ")[0]
            try:
                requests.delete(f"{SERVER_URL}/api/areas/{area_id}")
                self.cargar_areas()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def cargar_tabla_pausas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            res = requests.get(f"{SERVER_URL}/api/pausas", timeout=3)
            if res.status_code == 200:
                for p in res.json():
                    estado = "Completada" if p.get("completada") == 1 else "Pendiente"
                    self.tree.insert("", "end", values=(p["id"], p["fecha_hora"], p["area_nombre"], estado))
        except Exception as e:
            print(f"Error cargando pausas: {e}")

    def guardar_pausa(self):
        payload = {
            "fecha": self.entry_fecha.get().strip(),
            "hora": self.entry_hora.get().strip(),
            "area_nombre": self.combo_area.get(),
            "mensaje": self.entry_mensaje.get().strip(),
            "color_fondo": self.color_seleccionado
        }
        try:
            res = requests.post(f"{SERVER_URL}/api/pausas", json=payload, timeout=3)
            if res.status_code == 200:
                messagebox.showinfo("Éxito", "¡Pausa Activa programada correctamente!")
                self.cargar_tabla_pausas()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaAdminPausas(root)
    root.mainloop()