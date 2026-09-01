import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from config import SERVER_URL


class ModernEntry(tk.Frame):
    """Campo de entrada con borde fino y padding nativo."""
    def __init__(self, parent, bg_color, fg_color, border_color, font=("Segoe UI", 9), **kwargs):
        super().__init__(parent, bg=border_color, padx=1, pady=1)
        self.inner = tk.Frame(self, bg=bg_color, padx=6, pady=4)
        self.inner.pack(fill="both", expand=True)
        self.entry = tk.Entry(
            self.inner, bg=bg_color, fg=fg_color, bd=0, relief="flat",
            insertbackground=fg_color, font=font, **kwargs
        )
        self.entry.pack(fill="both", expand=True)

    def get(self):
        return self.entry.get()

    def insert(self, index, string):
        self.entry.insert(index, string)

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def set_theme(self, bg_color, fg_color, border_color):
        self.configure(bg=border_color)
        self.inner.configure(bg=bg_color)
        self.entry.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)


class VentanaAdminPausas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Pausas Activas")
        
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1280x750")
        self.root.minsize(1050, 680)

        self.modo_oscuro = True
        self.pausa_id_seleccionada = None
        self.color_seleccionado = "#0891B2"
        self.pausas_cache = {}
        self.areas_map = {}

        self.themes = {
            "dark": {
                "root_bg": "#0B0F17",
                "card_bg": "#1E293B",
                "card_border": "#334155",
                "input_bg": "#0F172A",
                "input_border": "#475569",
                "fg_main": "#F8FAFC",
                "fg_muted": "#94A3B8",
                "accent": "#0891B2",
                "accent_hover": "#0E7490",
                "table_header": "#0F172A",
                "table_row_even": "#1E293B",
                "table_row_odd": "#182232"
            },
            "light": {
                "root_bg": "#F1F5F9",
                "card_bg": "#FFFFFF",
                "card_border": "#E2E8F0",
                "input_bg": "#F8FAFC",
                "input_border": "#CBD5E1",
                "fg_main": "#0F172A",
                "fg_muted": "#64748B",
                "accent": "#0284C7",
                "accent_hover": "#0369A1",
                "table_header": "#E2E8F0",
                "table_row_even": "#FFFFFF",
                "table_row_odd": "#F8FAFC"
            }
        }

        self.setup_ui()
        self.cargar_areas()
        self.cargar_tabla_pausas()

    def setup_ui(self):
        t = self.themes["dark"]
        self.root.configure(bg=t["root_bg"])

        # ---------------- HEADER ----------------
        self.header_frame = tk.Frame(self.root, bg=t["root_bg"], padx=25, pady=15)
        self.header_frame.pack(fill="x")

        self.lbl_titulo = tk.Label(
            self.header_frame, text="Pausas Activas", 
            font=("Segoe UI", 18, "bold"), fg=t["fg_main"], bg=t["root_bg"]
        )
        self.lbl_titulo.pack(side="left")

        self.lbl_subtitulo = tk.Label(
            self.header_frame, text="• Panel de Control Enterprise", 
            font=("Segoe UI", 10), fg=t["fg_muted"], bg=t["root_bg"]
        )
        self.lbl_subtitulo.pack(side="left", padx=10, pady=(4, 0))

        self.btn_theme = tk.Button(
            self.header_frame, text="☀️ Modo Claro", font=("Segoe UI", 8, "bold"),
            bg=t["card_bg"], fg=t["fg_main"], activebackground=t["card_border"],
            activeforeground="white", bd=0, relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.toggle_tema
        )
        self.btn_theme.pack(side="right")

        # ---------------- MAIN CONTAINER ----------------
        self.main_container = tk.Frame(self.root, bg=t["root_bg"], padx=25, pady=0)
        self.main_container.pack(fill="both", expand=True)

        # ---------------- PANEL IZQUIERDO (FORMULARIO) ----------------
        self.card_form = tk.Frame(
            self.main_container, bg=t["card_bg"], 
            highlightbackground=t["card_border"], highlightthickness=1, padx=20, pady=20
        )
        self.card_form.pack(side="left", fill="y", padx=(0, 20), pady=(0, 25))

        self.lbl_sec_form = tk.Label(
            self.card_form, text="PROGRAMAR PAUSA", 
            font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["accent"]
        )
        self.lbl_sec_form.pack(anchor="w", pady=(0, 15))

        self.lbl_t1 = tk.Label(self.card_form, text="Título de la Pausa", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["fg_muted"])
        self.lbl_t1.pack(anchor="w")
        self.entry_titulo = ModernEntry(self.card_form, t["input_bg"], t["fg_main"], t["input_border"])
        self.entry_titulo.insert(0, "Pausa Activa")
        self.entry_titulo.pack(fill="x", pady=(2, 12))

        self.lbl_t2 = tk.Label(self.card_form, text="Hora (HH:MM 24h)", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["fg_muted"])
        self.lbl_t2.pack(anchor="w")
        self.entry_hora = ModernEntry(self.card_form, t["input_bg"], t["fg_main"], t["input_border"])
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.entry_hora.pack(fill="x", pady=(2, 12))

        self.lbl_t3 = tk.Label(self.card_form, text="Área Convocada", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["fg_muted"])
        self.lbl_t3.pack(anchor="w")
        self.combo_area = ttk.Combobox(self.card_form, state="readonly", font=("Segoe UI", 9))
        self.combo_area.pack(fill="x", pady=(2, 12))

        self.lbl_t4 = tk.Label(self.card_form, text="Mensaje de Alerta", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["fg_muted"])
        self.lbl_t4.pack(anchor="w")
        self.entry_mensaje = ModernEntry(self.card_form, t["input_bg"], t["fg_main"], t["input_border"])
        self.entry_mensaje.insert(0, "¡Hora de realizar tu pausa activa!")
        self.entry_mensaje.pack(fill="x", pady=(2, 12))

        self.lbl_t5 = tk.Label(self.card_form, text="Color Tema Alerta", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["fg_muted"])
        self.lbl_t5.pack(anchor="w", pady=(2, 4))
        self.frame_colores = tk.Frame(self.card_form, bg=t["card_bg"])
        self.frame_colores.pack(fill="x", pady=(0, 8))

        colores = ["#0891B2", "#0D9488", "#4F46E5", "#9333EA", "#E11D48", "#D97706"]
        for hex_code in colores:
            btn_c = tk.Button(
                self.frame_colores, bg=hex_code, activebackground=hex_code, bd=0, width=3, height=1,
                cursor="hand2", relief="flat", command=lambda c=hex_code: self.seleccionar_color(c)
            )
            btn_c.pack(side="left", padx=2)

        self.lbl_color_actual = tk.Label(self.card_form, text="Color: #0891B2", bg=self.color_seleccionado, fg="white", font=("Segoe UI", 8, "bold"), pady=3)
        self.lbl_color_actual.pack(fill="x", pady=(0, 15))

        self.btn_guardar = tk.Button(
            self.card_form, text="Guardar Pausa", font=("Segoe UI", 9, "bold"), bg=t["accent"], fg="white",
            activebackground=t["accent_hover"], activeforeground="white", bd=0, cursor="hand2", command=self.guardar_pausa
        )
        self.btn_guardar.pack(fill="x", pady=(0, 6), ipady=6)

        self.btn_limpiar = tk.Button(
            self.card_form, text="Limpiar Campos", font=("Segoe UI", 8), bg=t["input_bg"], fg=t["fg_main"],
            activebackground=t["card_border"], activeforeground="white", bd=0, cursor="hand2", command=self.limpiar_formulario
        )
        self.btn_limpiar.pack(fill="x", ipady=4)

        # ---------------- PANEL DERECHO ----------------
        self.card_right = tk.Frame(
            self.main_container, bg=t["card_bg"], 
            highlightbackground=t["card_border"], highlightthickness=1, padx=15, pady=15
        )
        self.card_right.pack(side="right", fill="both", expand=True, pady=(0, 25))

        self.notebook = ttk.Notebook(self.card_right)
        self.notebook.pack(fill="both", expand=True)

        self.tab_pausas = tk.Frame(self.notebook, bg=t["card_bg"])
        self.notebook.add(self.tab_pausas, text=" PAUSAS PROGRAMADAS ")

        self.frame_tabla = tk.Frame(self.tab_pausas, bg=t["card_bg"])
        self.frame_tabla.pack(fill="both", expand=True, pady=(10, 10))

        scrollbar_y = ttk.Scrollbar(self.frame_tabla, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        self.cols_keys = ("col_id", "col_titulo", "col_fecha", "col_hora", "col_area", "col_estado")
        self.tree = ttk.Treeview(self.frame_tabla, columns=self.cols_keys, show="headings", yscrollcommand=scrollbar_y.set)
        scrollbar_y.config(command=self.tree.yview)

        self.tree.heading("col_id", text="ID")
        self.tree.column("col_id", width=50, minwidth=40, stretch=False, anchor="center")
        
        self.tree.heading("col_titulo", text="Título de la Pausa")
        self.tree.column("col_titulo", width=220, minwidth=140, stretch=True, anchor="w")

        self.tree.heading("col_fecha", text="Fecha")
        self.tree.column("col_fecha", width=110, minwidth=90, stretch=False, anchor="center")

        self.tree.heading("col_hora", text="Hora")
        self.tree.column("col_hora", width=110, minwidth=90, stretch=False, anchor="center")

        self.tree.heading("col_area", text="Área Convocada")
        self.tree.column("col_area", width=160, minwidth=110, stretch=True, anchor="w")

        self.tree.heading("col_estado", text="Estado")
        self.tree.column("col_estado", width=110, minwidth=90, stretch=False, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar_pausa)
        self.tree.bind("<Double-1>", lambda event: self.cambiar_estado_pausa())

        # Action Toolbar
        self.frame_acciones = tk.Frame(self.tab_pausas, bg=t["card_bg"])
        self.frame_acciones.pack(fill="x", pady=(5, 0))

        self.btn_estado = tk.Button(self.frame_acciones, text="🔄 Cambiar Estado", bg="#0284C7", fg="white", activebackground="#0369A1", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.cambiar_estado_pausa)
        self.btn_estado.pack(side="left", padx=(0, 6), ipadx=10, ipady=5)

        self.btn_editar = tk.Button(self.frame_acciones, text="✏️ Editar", bg="#D97706", fg="white", activebackground="#B45309", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.cargar_pausa_para_editar)
        self.btn_editar.pack(side="left", padx=4, ipadx=10, ipady=5)

        self.btn_eliminar = tk.Button(self.frame_acciones, text="🗑️ Eliminar", bg="#DC2626", fg="white", activebackground="#B91C1C", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.eliminar_pausa)
        self.btn_eliminar.pack(side="left", padx=4, ipadx=10, ipady=5)

        self.btn_eliminar_todas = tk.Button(self.frame_acciones, text="⚠️ Eliminar Todo y Caché", bg="#7F1D1D", fg="white", activebackground="#991B1B", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.eliminar_todas_las_pausas)
        self.btn_eliminar_todas.pack(side="right", ipadx=10, ipady=5)

        # TAB 2: ÁREAS
        self.tab_areas = tk.Frame(self.notebook, bg=t["card_bg"], padx=15, pady=15)
        self.notebook.add(self.tab_areas, text=" GESTIÓN DE ÁREAS ")

        self.lbl_sec_area = tk.Label(self.tab_areas, text="Registrar Nueva Área", font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["fg_main"])
        self.lbl_sec_area.pack(anchor="w", pady=(0, 6))

        self.entry_nueva_area = ModernEntry(self.tab_areas, t["input_bg"], t["fg_main"], t["input_border"])
        self.entry_nueva_area.pack(anchor="w", fill="x", pady=(0, 10))

        self.btn_crear_a = tk.Button(self.tab_areas, text="+ Agregar Área", bg=t["accent"], fg="white", activebackground=t["accent_hover"], bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.crear_area)
        self.btn_crear_a.pack(anchor="w", ipadx=12, ipady=5, pady=(0, 15))

        self.list_areas = tk.Listbox(
            self.tab_areas, font=("Segoe UI", 9), bg=t["input_bg"], fg=t["fg_main"], 
            bd=0, highlightthickness=1, highlightbackground=t["input_border"], selectbackground=t["accent"]
        )
        self.list_areas.pack(fill="both", expand=True, pady=(0, 10))

        self.btn_elim_a = tk.Button(self.tab_areas, text="Eliminar Área Seleccionada", bg="#DC2626", fg="white", activebackground="#B91C1C", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", command=self.eliminar_area)
        self.btn_elim_a.pack(anchor="w", ipadx=12, ipady=5)

        self.aplicar_estilos_ttk()

    def aplicar_estilos_ttk(self):
        t = self.themes["dark" if self.modo_oscuro else "light"]
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=t["card_bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["input_bg"], foreground=t["fg_muted"], padding=[14, 6], font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", t["accent"])], foreground=[("selected", "#FFFFFF")])

        style.configure(
            "Treeview", background=t["card_bg"], fieldbackground=t["card_bg"],
            foreground=t["fg_main"], rowheight=32, font=("Segoe UI", 9), borderwidth=0
        )
        style.configure(
            "Treeview.Heading", background=t["table_header"], foreground=t["fg_main"],
            font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat"
        )
        style.map("Treeview", background=[("selected", t["accent"])], foreground=[("selected", "#FFFFFF")])

        style.configure("TCombobox", fieldbackground=t["input_bg"], background=t["input_border"], foreground=t["fg_main"], borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", t["input_bg"])], selectbackground=[("readonly", t["input_bg"])], selectforeground=[("readonly", t["fg_main"])])

    def toggle_tema(self):
        self.modo_oscuro = not self.modo_oscuro
        t = self.themes["dark" if self.modo_oscuro else "light"]

        self.root.configure(bg=t["root_bg"])
        self.btn_theme.configure(
            text="☀️ Modo Claro" if self.modo_oscuro else "🌙 Modo Oscuro",
            bg=t["card_bg"], fg=t["fg_main"]
        )

        self.header_frame.configure(bg=t["root_bg"])
        self.lbl_titulo.configure(bg=t["root_bg"], fg=t["fg_main"])
        self.lbl_subtitulo.configure(bg=t["root_bg"], fg=t["fg_muted"])
        self.main_container.configure(bg=t["root_bg"])

        for card in [self.card_form, self.card_right]:
            card.configure(bg=t["card_bg"], highlightbackground=t["card_border"])

        self.lbl_sec_form.configure(bg=t["card_bg"], fg=t["accent"])
        self.lbl_sec_area.configure(bg=t["card_bg"], fg=t["fg_main"])

        for lbl in [self.lbl_t1, self.lbl_t2, self.lbl_t3, self.lbl_t4, self.lbl_t5]:
            lbl.configure(bg=t["card_bg"], fg=t["fg_muted"])

        for entry in [self.entry_titulo, self.entry_hora, self.entry_mensaje, self.entry_nueva_area]:
            entry.set_theme(t["input_bg"], t["fg_main"], t["input_border"])

        self.frame_colores.configure(bg=t["card_bg"])
        self.frame_tabla.configure(bg=t["card_bg"])
        self.frame_acciones.configure(bg=t["card_bg"])
        self.tab_pausas.configure(bg=t["card_bg"])
        self.tab_areas.configure(bg=t["card_bg"])

        self.btn_guardar.configure(bg=t["accent"], activebackground=t["accent_hover"])
        self.btn_crear_a.configure(bg=t["accent"], activebackground=t["accent_hover"])
        self.btn_limpiar.configure(bg=t["input_bg"], fg=t["fg_main"], activebackground=t["card_border"])

        self.list_areas.configure(bg=t["input_bg"], fg=t["fg_main"], highlightbackground=t["input_border"], selectbackground=t["accent"])

        self.aplicar_estilos_ttk()
        self.cargar_tabla_pausas()

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
                requests.post(f"{SERVER_URL}/api/areas", json={"nombre": nombre})
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
        
        t = self.themes["dark" if self.modo_oscuro else "light"]

        try:
            res = requests.get(f"{SERVER_URL}/api/pausas", timeout=3)
            if res.status_code == 200:
                pausas = res.json()

                for i, p in enumerate(pausas):
                    p_id = p["id"]
                    self.pausas_cache[p_id] = p
                    
                    comp = p.get("completada")
                    estado = "Completada" if comp in (1, True, "1", "true", "True") else "Pendiente"
                    fecha = p.get("fecha") or datetime.now().strftime("%Y-%m-%d")
                    
                    hora_val = p.get("hora") or p.get("hora_inicio") or p.get("hora_pausa") or p.get("time")
                    if not hora_val or str(hora_val).strip() in ("", "None", "null"):
                        hora_val = "--:--"
                    else:
                        hora_val = str(hora_val).strip()
                        if len(hora_val) >= 5 and ":" in hora_val:
                            hora_val = hora_val[:5]

                    area_nombre = p.get("area_nombre") or "TODAS"
                    if p.get("area_id") and area_nombre == "TODAS":
                        for nom, a_id in self.areas_map.items():
                            if str(a_id) == str(p["area_id"]):
                                area_nombre = nom
                                break

                    tag = "even" if i % 2 == 0 else "odd"
                    
                    self.tree.insert(
                        "", "end", iid=p_id, tags=(tag,),
                        values=(p_id, p.get("titulo") or p.get("mensaje", "Pausa Activa"), fecha, hora_val, area_nombre, estado)
                    )

                self.tree.tag_configure("even", background=t["table_row_even"])
                self.tree.tag_configure("odd", background=t["table_row_odd"])
        except Exception as e:
            print(f"Error cargando pausas: {e}")

    def al_seleccionar_pausa(self, event):
        sel = self.tree.selection()
        if sel:
            try:
                self.pausa_id_seleccionada = int(sel[0])
            except ValueError:
                self.pausa_id_seleccionada = None

    def cambiar_estado_pausa(self):
        if not self.pausa_id_seleccionada or self.pausa_id_seleccionada not in self.pausas_cache:
            messagebox.showwarning("Atención", "Por favor selecciona una pausa de la lista.")
            return

        pausa = self.pausas_cache[self.pausa_id_seleccionada]
        estado_actual = pausa.get("completada")
        es_completada = estado_actual in (1, True, "1", "true", "True")
        nuevo_estado = False if es_completada else True

        payload = {
            "titulo": pausa.get("titulo", "Pausa Activa"),
            "mensaje": pausa.get("mensaje", ""),
            "hora": pausa.get("hora", datetime.now().strftime("%H:%M")),
            "fecha": pausa.get("fecha", datetime.now().strftime("%Y-%m-%d")),
            "color_fondo": pausa.get("color_fondo", "#0891B2"),
            "area_nombre": pausa.get("area_nombre", "TODAS"),
            "completada": nuevo_estado
        }

        try:
            res = requests.put(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", json=payload, timeout=3)
            if res.status_code == 200:
                self.cargar_tabla_pausas()
            else:
                messagebox.showerror("Error", f"No se pudo cambiar el estado: {res.text}")
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def cargar_pausa_para_editar(self):
        if not self.pausa_id_seleccionada or self.pausa_id_seleccionada not in self.pausas_cache:
            messagebox.showwarning("Atención", "Por favor selecciona una pausa de la lista.")
            return

        pausa = self.pausas_cache[self.pausa_id_seleccionada]
        hora_val = pausa.get("hora") or pausa.get("hora_inicio") or datetime.now().strftime("%H:%M")
        
        self.entry_titulo.delete(0, tk.END)
        self.entry_titulo.insert(0, pausa.get("titulo", "Pausa Activa"))

        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, hora_val)

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, pausa.get("mensaje", ""))

        area_target = pausa.get("area_nombre", "TODAS")
        values = list(self.combo_area["values"])
        if area_target in values:
            self.combo_area.current(values.index(area_target))

        color = pausa.get("color_fondo", "#0891B2")
        self.seleccionar_color(color)

        self.btn_guardar.configure(text=f"Actualizar Pausa #{self.pausa_id_seleccionada}", bg="#D97706")

    def limpiar_formulario(self):
        t = self.themes["dark" if self.modo_oscuro else "light"]
        self.pausa_id_seleccionada = None
        self.entry_titulo.delete(0, tk.END)
        self.entry_titulo.insert(0, "Pausa Activa")

        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))

        if self.combo_area["values"]:
            self.combo_area.current(0)

        self.entry_mensaje.delete(0, tk.END)
        self.entry_mensaje.insert(0, "¡Hora de realizar tu pausa activa!")

        self.seleccionar_color("#0891B2")
        self.btn_guardar.configure(text="Guardar Pausa", bg=t["accent"])

    def guardar_pausa(self):
        area_sel = self.combo_area.get()
        area_nombre = area_sel if area_sel != "TODAS LAS ÁREAS" else "TODAS"

        payload = {
            "titulo": self.entry_titulo.get().strip(),
            "mensaje": self.entry_mensaje.get().strip(),
            "hora": self.entry_hora.get().strip(),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "color_fondo": self.color_seleccionado,
            "area_nombre": area_nombre
        }

        try:
            if self.pausa_id_seleccionada:
                res = requests.put(f"{SERVER_URL}/api/pausas/{self.pausa_id_seleccionada}", json=payload, timeout=3)
            else:
                res = requests.post(f"{SERVER_URL}/api/pausas", json=payload, timeout=3)

            if res.status_code == 200:
                self.limpiar_formulario()
                self.cargar_tabla_pausas()
            else:
                messagebox.showerror("Error", f"Ocurrió un error: {res.text}")
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
        if messagebox.askyesno("Confirmación Crítica", "¿Estás seguro de que deseas eliminar TODAS las pausas y limpiar la memoria caché?"):
            try:
                res = requests.delete(f"{SERVER_URL}/api/pausas/todas/eliminar", timeout=10)
                if res.status_code == 200:
                    self.pausas_cache.clear()
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    self.pausa_id_seleccionada = None
                    self.limpiar_formulario()
                    messagebox.showinfo("Éxito", "Se eliminaron todas las pausas de la BD y se limpió el caché.")
                else:
                    messagebox.showerror("Error", f"No se pudo completar la operación: {res.text}")
            except Exception as e:
                messagebox.showerror("Error de conexión", f"No se pudo conectar con el servidor: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaAdminPausas(root)
    root.mainloop()