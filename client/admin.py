import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from config import SERVER_URL

class VentanaAdminPausas:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - Configuración de Pausas Activas")
        self.root.geometry("980x680")
        self.root.resizable(False, False)
        
        self.bg_color = "#1E1E2E"
        self.card_color = "#2A2A3C"
        self.accent_color = "#7289DA"
        self.fg_color = "#FFFFFF"
        self.color_seleccionado = "#1E1E2E"
        self.pausa_id_seleccionada = None

        self.pausas_cache = {}

        self.root.configure(bg=self.bg_color)
        self.crear_interfaz()
        self.cargar_areas()
        self.cargar_tabla_pausas()

    def crear_interfaz(self):
        lbl_titulo = tk.Label(self.root, text="⚙️ Configuración de Pausas Activas", font=("Helvetica", 20, "bold"), bg=self.bg_color, fg=self.fg_color)
        lbl_titulo.pack(pady=15)

        frame_main = tk.Frame(self.root, bg=self.bg_color)
        frame_main.pack(fill="both", expand=True, padx=20, pady=10)

        # --- FORMULARIO DE PROGRAMACIÓN / EDICIÓN ---
        frame_form = tk.LabelFrame(frame_main, text=" Programación / Edición ", font=("Helvetica", 11, "bold"), bg=self.card_color, fg=self.accent_color, padx=15, pady=10)
        frame_form.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(frame_form, text="Fecha (AAAA-MM-DD):", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_fecha = tk.Entry(frame_form, font=("Helvetica", 10), width=24)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha.pack(pady=(0, 8))

        tk.Label(frame_form, text="Hora (HH:MM) 24 hrs:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_hora = tk.Entry(frame_form, font=("Helvetica", 10), width=24)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.entry_hora.pack(pady=(0, 8))

        tk.Label(frame_form, text="Área Convocada:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.combo_area = ttk.Combobox(frame_form, state="readonly", font=("Helvetica", 10), width=22)
        self.combo_area.pack(pady=(0, 8))

        tk.Label(frame_form, text="Mensaje de Alerta:", bg=self.card_color, fg=self.fg_color).pack(anchor="w")
        self.entry_mensaje = tk.Entry(frame_form, font=("Helvetica", 10), width=24)
        self.entry_mensaje.insert(0, "¡Hora de la Pausa Activa!")
        self.entry_mensaje.pack(pady=(0, 8))

        # --- SELECTOR DE COLORES PRIMARIOS ---
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

        self.btn_guardar = tk.Button(frame_form, text="🚀 Guardar y Programar", font=("Helvetica", 10, "bold"), bg="#43B581", fg="white", cursor="hand2", command=self.guardar_pausa)
        self.btn_guardar.pack(fill="x", pady=(10, 5))

        self.btn_limpiar = tk.Button(frame_form, text="🔄 Limpiar Formulario", font=("Helvetica", 9), bg="#4F545C", fg="white", cursor="hand2", command=self.limpiar_formulario)
        self.btn_limpiar.pack(fill="x", pady=2)

        # --- PESTAÑAS: PAUSAS Y CRUD DE ÁREAS ---
        frame_derecho = tk.Frame(frame_main, bg=self.bg_color)
        frame_derecho.pack(side="right", fill="both", expand=True)

        notebook = ttk.Notebook(frame_derecho)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Pausas Programadas (Tabla + CRUD Horarios)
        tab_pausas = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(tab_pausas, text="Pausas Programadas")

        cols = ("ID", "Fecha/Hora", "Área", "Estado")
        self.tree = ttk.Treeview(tab_pausas, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar_pausa)

        # Panel inferior de acciones CRUD de Pausas
        frame_acciones_pausa = tk.Frame(tab_pausas, bg=self.bg_color)
        frame_acciones_pausa.pack(fill="x", pady=5)

        btn_editar = tk.Button(frame_acciones_pausa, text="✏️ Cargar para Editar", bg="#FAA61A", fg="white", font=("Helvetica", 10, "bold"), command=self.cargar_pausa_para_editar)
        btn_editar.pack(side="left", padx=5)

        btn_eliminar = tk.Button(frame_acciones_pausa, text="❌ Eliminar Pausa", bg="#F04747", fg="white", font=("Helvetica", 10, "bold"), command=self.eliminar_pausa)
        btn_eliminar.pack(side="left", padx=5)

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
        self.pausas_cache.clear()
        try:
            res = requests.get(f"{SERVER_URL}/api/pausas", timeout=3)
            if res.status_code == 200:
                for p in res.json():
                    p_id = p["id"]
                    self.pausas_cache[p_id] = p
                    estado = "Completada" if p.get("completada") == 1 else "Pendiente"
                    self.tree.insert("", "end", iid=p_id, values=(p_id, p["fecha_hora"], p["area_nombre"], estado))
        except Exception as e:
            print(f"Error cargando pausas: {e}")

    def al_seleccionar_pausa(self, event):
        sel = self.tree.selection()
        if sel:
            self.pausa_id_seleccionada = int(sel[0])

    def cargar_pausa_para_editar(self):
        if not self.pausa_id_seleccionada or self.pausa_id_seleccionada not in self.pausas_cache:
            messagebox.showwarning("Atención", "Por favor selecciona una pausa de la lista.")
            return

        pausa = self.pausas_cache[self.pausa_id_seleccionada]
        
        try:
            fecha, hora = pausa["fecha_hora"].split(" ")
        except Exception:
            fecha, hora = datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M")

        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, fecha)

        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, hora)

        if pausa.get("area_nombre") in self.combo_area["values"]:
            self.combo_area.set(pausa["area_nombre"])

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, pausa.get("mensaje", ""))

        color = pausa.get("color_fondo", "#1E1E2E")
        self.seleccionar_color(color)

        self.btn_guardar.configure(text=f"💾 Actualizar Pausa #{self.pausa_id_seleccionada}", bg="#FAA61A")

    def limpiar_formulario(self):
        self.pausa_id_seleccionada = None
        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))

        if self.combo_area["values"]:
            self.combo_area.current(0)

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, "¡Hora de la Pausa Activa!")

        self.seleccionar_color("#1E1E2E")
        self.btn_guardar.configure(text="🚀 Guardar y Programar", bg="#43B581")

    def guardar_pausa(self):
        payload = {
            "fecha": self.entry_fecha.get().strip(),
            "hora": self.entry_hora.get().strip(),
            "area_nombre": self.combo_area.get(),
            "mensaje": self.entry_mensaje.get().strip(),
            "color_fondo": self.color_seleccionado
        }
        
        try:
            if self.pausa_id_seleccionada:
                # PUT para actualizar horario existente
                res = requests.put(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", json=payload, timeout=3)
                mensaje_ok = f"¡Pausa #{self.pausa_id_seleccionada} actualizada correctamente!"
            else:
                # POST para crear nuevo horario
                res = requests.post(f"{SERVER_URL}/api/pausas", json=payload, timeout=3)
                mensaje_ok = "¡Pausa Activa programada correctamente!"

            if res.status_code == 200:
                messagebox.showinfo("Éxito", mensaje_ok)
                self.limpiar_formulario()
                self.cargar_tabla_pausas()
            else:
                messagebox.showerror("Error", f"Ocurrió un error: {res.text}")
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def eliminar_pausa(self):
        if not self.pausa_id_seleccionada:
            messagebox.showwarning("Atención", "Por favor selecciona una pausa de la lista para eliminar.")
            return

        confirmar = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar la pausa ID #{self.pausa_id_seleccionada}?")
        if confirmar:
            try:
                res = requests.delete(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", timeout=3)
                if res.status_code == 200:
                    messagebox.showinfo("Eliminada", f"Pausa #{self.pausa_id_seleccionada} eliminada exitosamente.")
                    self.limpiar_formulario()
                    self.cargar_tabla_pausas()
                else:
                    messagebox.showerror("Error", f"No se pudo eliminar: {res.text}")
            except Exception as e:
                messagebox.showerror("Error de conexión", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaAdminPausas(root)
    root.mainloop()