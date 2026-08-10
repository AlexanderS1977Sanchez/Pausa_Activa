import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from config import SERVER_URL

class VentanaAdminPausas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Pausas Activas")
        
        # Iniciar maximizado en pantalla completa
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1280x720")

        self.root.minsize(1000, 650)
        
        # Paleta Minimalista Modern Dark (Slate)
        self.bg_color = "#0F172A"       # Azul muy oscuro
        self.card_color = "#1E293B"     # Gris slate
        self.input_bg = "#334155"       # Slate claro
        self.accent_color = "#38BDF8"   # Azul cyan
        self.fg_color = "#F8FAFC"       # Blanco hueso
        self.fg_muted = "#94A3B8"       # Gris texto
        self.color_seleccionado = "#0F172A"
        self.pausa_id_seleccionada = None

        self.pausas_cache = {}
        self.areas_map = {}

        self.root.configure(bg=self.bg_color)
        self.aplicar_estilos_ttk()
        self.crear_interfaz()
        self.cargar_areas()
        self.cargar_tabla_pausas()

    def aplicar_estilos_ttk(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Estilo Pestañas Minimalistas
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.card_color, foreground=self.fg_muted, padding=[16, 8], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.accent_color)], foreground=[("selected", "#0F172A")])

        # Estilo Tabla (Treeview)
        style.configure("Treeview", 
                        background=self.card_color, 
                        fieldbackground=self.card_color, 
                        foreground=self.fg_color, 
                        rowheight=32, 
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background=self.input_bg, 
                        foreground=self.fg_color, 
                        font=("Segoe UI", 10, "bold"), 
                        borderwidth=0)
        style.map("Treeview", background=[("selected", "#0284C7")], foreground=[("selected", "#FFFFFF")])

    def crear_interfaz(self):
        # Header Superior Minimalista
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        lbl_titulo = tk.Label(header_frame, text="Pausas Activas", font=("Segoe UI", 22, "bold"), bg=self.bg_color, fg=self.fg_color)
        lbl_titulo.pack(side="left")

        lbl_subtitulo = tk.Label(header_frame, text="• Panel de Control y Programación", font=("Segoe UI", 12), bg=self.bg_color, fg=self.fg_muted)
        lbl_subtitulo.pack(side="left", padx=10, pady=(6, 0))

        # Contenedor Principal
        frame_main = tk.Frame(self.root, bg=self.bg_color)
        frame_main.pack(fill="both", expand=True, padx=25, pady=10)

        # ---------------- FORMULARIO IZQUIERDO ----------------
        frame_form = tk.Frame(frame_main, bg=self.card_color, padx=20, pady=20)
        frame_form.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(frame_form, text="PROGRAMACIÓN", font=("Segoe UI", 11, "bold"), bg=self.card_color, fg=self.accent_color).pack(anchor="w", pady=(0, 15))

        tk.Label(frame_form, text="Título de la Pausa", font=("Segoe UI", 9), bg=self.card_color, fg=self.fg_muted).pack(anchor="w")
        self.entry_titulo = tk.Entry(frame_form, font=("Segoe UI", 10), bg=self.input_bg, fg="white", bd=0, relief="flat", insertbackground="white")
        self.entry_titulo.insert(0, "Pausa Activa")
        self.entry_titulo.pack(fill="x", pady=(2, 12), ipady=6)

        tk.Label(frame_form, text="Hora (HH:MM 24h)", font=("Segoe UI", 9), bg=self.card_color, fg=self.fg_muted).pack(anchor="w")
        self.entry_hora = tk.Entry(frame_form, font=("Segoe UI", 10), bg=self.input_bg, fg="white", bd=0, relief="flat", insertbackground="white")
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.entry_hora.pack(fill="x", pady=(2, 12), ipady=6)

        tk.Label(frame_form, text="Área Convocada", font=("Segoe UI", 9), bg=self.card_color, fg=self.fg_muted).pack(anchor="w")
        self.combo_area = ttk.Combobox(frame_form, state="readonly", font=("Segoe UI", 10))
        self.combo_area.pack(fill="x", pady=(2, 12))

        tk.Label(frame_form, text="Mensaje de Alerta", font=("Segoe UI", 9), bg=self.card_color, fg=self.fg_muted).pack(anchor="w")
        self.entry_mensaje = tk.Entry(frame_form, font=("Segoe UI", 10), bg=self.input_bg, fg="white", bd=0, relief="flat", insertbackground="white")
        self.entry_mensaje.insert(0, "¡Hora de realizar tu pausa activa!")
        self.entry_mensaje.pack(fill="x", pady=(2, 12), ipady=6)

        # Paleta de Colores Minimalista
        tk.Label(frame_form, text="Color de Fondo", font=("Segoe UI", 9), bg=self.card_color, fg=self.fg_muted).pack(anchor="w", pady=(5, 4))
        frame_colores = tk.Frame(frame_form, bg=self.card_color)
        frame_colores.pack(fill="x", pady=(0, 15))

        colores = ["#0F172A", "#1E3A8A", "#881337", "#065F46", "#78350F", "#4C1D95"]
        for hex_code in colores:
            btn_c = tk.Button(
                frame_colores, 
                bg=hex_code, 
                activebackground=hex_code,
                bd=0, 
                width=3, 
                height=1, 
                cursor="hand2",
                command=lambda c=hex_code: self.seleccionar_color(c)
            )
            btn_c.pack(side="left", padx=2)

        self.lbl_color_actual = tk.Label(frame_form, text="Color: #0F172A", bg=self.color_seleccionado, fg="white", font=("Segoe UI", 8, "bold"), pady=4)
        self.lbl_color_actual.pack(fill="x", pady=(0, 15))

        # Botones de Acción Formulario
        self.btn_guardar = tk.Button(frame_form, text="✓ Guardar Pausa", font=("Segoe UI", 10, "bold"), bg="#10B981", fg="white", activebackground="#059669", activeforeground="white", bd=0, cursor="hand2", command=self.guardar_pausa)
        self.btn_guardar.pack(fill="x", pady=(0, 6), ipady=6)

        self.btn_limpiar = tk.Button(frame_form, text="🔄 Limpiar Campos", font=("Segoe UI", 9), bg=self.input_bg, fg="white", activebackground="#475569", activeforeground="white", bd=0, cursor="hand2", command=self.limpiar_formulario)
        self.btn_limpiar.pack(fill="x", ipady=4)

        # ---------------- PANEL DERECHO (PESTAÑAS) ----------------
        frame_derecho = tk.Frame(frame_main, bg=self.bg_color)
        frame_derecho.pack(side="right", fill="both", expand=True)

        notebook = ttk.Notebook(frame_derecho)
        notebook.pack(fill="both", expand=True)

        # TAB 1: PAUSAS
        tab_pausas = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(tab_pausas, text="PAUSAS PROGRAMADAS")

        frame_tabla = tk.Frame(tab_pausas, bg=self.bg_color)
        frame_tabla.pack(fill="both", expand=True, pady=(10, 5))

        scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        cols = ("ID", "Título", "Hora", "Área", "Estado")
        self.tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", yscrollcommand=scrollbar_y.set)
        scrollbar_y.config(command=self.tree.yview)

        # Configuración Inteligente de Columnas (Responsive)
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=60, minwidth=50, stretch=False, anchor="center")

        self.tree.heading("Título", text="Título")
        self.tree.column("Título", width=250, minwidth=150, stretch=True, anchor="w")

        self.tree.heading("Hora", text="Hora")
        self.tree.column("Hora", width=100, minwidth=80, stretch=False, anchor="center")

        self.tree.heading("Área", text="Área Convocada")
        self.tree.column("Área", width=200, minwidth=120, stretch=True, anchor="w")

        self.tree.heading("Estado", text="Estado")
        self.tree.column("Estado", width=120, minwidth=100, stretch=False, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar_pausa)

        # Botones Inferiores
        frame_acciones = tk.Frame(tab_pausas, bg=self.bg_color)
        frame_acciones.pack(fill="x", pady=10)

        btn_editar = tk.Button(frame_acciones, text="✏️ Editar", bg="#F59E0B", fg="white", activebackground="#D97706", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.cargar_pausa_para_editar)
        btn_editar.pack(side="left", padx=(0, 6), ipadx=15, ipady=5)

        btn_eliminar = tk.Button(frame_acciones, text="🗑️ Eliminar", bg="#EF4444", fg="white", activebackground="#DC2626", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.eliminar_pausa)
        btn_eliminar.pack(side="left", padx=6, ipadx=15, ipady=5)

        btn_eliminar_todas = tk.Button(frame_acciones, text="⚠️ Eliminar TODAS", bg="#991B1B", fg="white", activebackground="#7F1D1D", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.eliminar_todas_las_pausas)
        btn_eliminar_todas.pack(side="left", padx=6, ipadx=15, ipady=5)

        # TAB 2: ÁREAS
        tab_areas = tk.Frame(notebook, bg=self.card_color, padx=20, pady=20)
        notebook.add(tab_areas, text="GESTIÓN DE ÁREAS")

        tk.Label(tab_areas, text="Nueva Área de Trabajo", font=("Segoe UI", 10, "bold"), bg=self.card_color, fg=self.fg_color).pack(anchor="w", pady=(0, 5))
        self.entry_nueva_area = tk.Entry(tab_areas, font=("Segoe UI", 10), bg=self.input_bg, fg="white", bd=0, relief="flat", insertbackground="white")
        self.entry_nueva_area.pack(anchor="w", fill="x", pady=(0, 10), ipady=6)

        btn_crear_a = tk.Button(tab_areas, text="+ Agregar Área", bg="#10B981", fg="white", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.crear_area)
        btn_crear_a.pack(anchor="w", ipadx=15, ipady=5, pady=(0, 15))

        self.list_areas = tk.Listbox(tab_areas, font=("Segoe UI", 10), bg=self.input_bg, fg="white", bd=0, highlightthickness=0, selectbackground=self.accent_color)
        self.list_areas.pack(fill="both", expand=True, pady=(0, 10))

        btn_elim_a = tk.Button(tab_areas, text="Eliminar Área Seleccionada", bg="#EF4444", fg="white", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.eliminar_area)
        btn_elim_a.pack(anchor="w", ipadx=15, ipady=5)

    def seleccionar_color(self, hex_code):
        self.color_seleccionado = hex_code
        self.lbl_color_actual.configure(text=f"Color: {hex_code}", bg=hex_code)

    def cargar_areas(self):
        try:
            res = requests.get(f"{SERVER_URL}/api/areas", timeout=3)
            if res.status_code == 200:
                areas = res.json()
                self.areas_map = {a["nombre"]: str(a["id"]) for a in areas}
                nombres_combo = ["TODAS LAS ÁREAS"] + list(self.areas_map.keys())
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
        """Mantiene siempre la tabla limpia y ORDENADA CRONOLÓGICAMENTE"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.pausas_cache.clear()
        try:
            res = requests.get(f"{SERVER_URL}/api/pausas", timeout=3)
            if res.status_code == 200:
                pausas = res.json()
                # Garantizar orden por HORA (00:00 -> 23:59)
                pausas_ordenadas = sorted(pausas, key=lambda x: x.get("hora", ""))

                for p in pausas_ordenadas:
                    p_id = p["id"]
                    self.pausas_cache[p_id] = p
                    estado = "Completada" if p.get("completada") == 1 else "Pendiente"
                    
                    area_nombre = "TODAS"
                    if p.get("area_id"):
                        for nom, a_id in self.areas_map.items():
                            if str(a_id) == str(p["area_id"]):
                                area_nombre = nom
                                break

                    self.tree.insert("", "end", iid=p_id, values=(p_id, p.get("titulo", "Pausa"), p.get("hora", "--:--"), area_nombre, estado))
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
        
        self.entry_titulo.delete(0, tk.END)
        self.entry_titulo.insert(0, pausa.get("titulo", "Pausa Activa"))

        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, pausa.get("hora", datetime.now().strftime("%H:%M")))

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, pausa.get("mensaje", ""))

        color = pausa.get("color_fondo", "#0F172A")
        self.seleccionar_color(color)

        self.btn_guardar.configure(text=f"💾 Actualizar Pausa #{self.pausa_id_seleccionada}", bg="#F59E0B")

    def limpiar_formulario(self):
        self.pausa_id_seleccionada = None
        self.entry_titulo.delete(0, tk.END)
        self.entry_titulo.insert(0, "Pausa Activa")

        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))

        if self.combo_area["values"]:
            self.combo_area.current(0)

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, "¡Hora de realizar tu pausa activa!")

        self.seleccionar_color("#0F172A")
        self.btn_guardar.configure(text="✓ Guardar Pausa", bg="#10B981")

    def guardar_pausa(self):
        area_sel = self.combo_area.get()
        area_id = self.areas_map.get(area_sel, "")

        payload = {
            "titulo": self.entry_titulo.get().strip(),
            "mensaje": self.entry_mensaje.get().strip(),
            "hora": self.entry_hora.get().strip(),
            "color_fondo": self.color_seleccionado
        }

        if area_id:
            payload["area_id"] = str(area_id)

        try:
            if self.pausa_id_seleccionada:
                res = requests.put(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", data=payload, timeout=3)
            else:
                res = requests.post(f"{SERVER_URL}/api/pausas", data=payload, timeout=3)

            if res.status_code == 200:
                self.limpiar_formulario()
                self.cargar_tabla_pausas()
            else:
                messagebox.showerror("Error", f"Ocurrió un error ({res.status_code}): {res.text}")
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def eliminar_pausa(self):
        if not self.pausa_id_seleccionada:
            messagebox.showwarning("Atención", "Por favor selecciona una pausa para eliminar.")
            return

        if messagebox.askyesno("Confirmación", f"¿Deseas eliminar la pausa #{self.pausa_id_seleccionada}?"):
            try:
                res = requests.delete(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", timeout=3)
                if res.status_code == 200:
                    self.limpiar_formulario()
                    self.cargar_tabla_pausas()
            except Exception as e:
                messagebox.showerror("Error de conexión", str(e))

    def eliminar_todas_las_pausas(self):
        if messagebox.askyesno("Confirmación Crítica", "¿Estás seguro de que deseas eliminar TODAS las pausas?"):
            try:
                res = requests.delete(f"{SERVER_URL}/api/pausas/todas/eliminar", timeout=3)
                if res.status_code == 200:
                    self.limpiar_formulario()
                    self.cargar_tabla_pausas()
            except Exception as e:
                messagebox.showerror("Error de conexión", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaAdminPausas(root)
    root.mainloop()