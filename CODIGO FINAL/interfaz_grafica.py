# interfaz_grafica.py (Versión con la corrección del AttributeError)
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import threading
import logging
import queue
import time
import cv2
import os
import subprocess
import sys

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    def emit(self, record):
        self.log_queue.put(self.format(record))

class InterfazGrafica(tk.Tk):
    def __init__(self, controlador, sistema_vision, sistema_audio, logica_tesis):
        super().__init__()
        self.controlador = controlador
        self.sistema_vision = sistema_vision
        self.sistema_audio = sistema_audio
        self.logica_tesis = logica_tesis
        self.video_running, self.is_recording = False, False
        self.lista_de_botones = []
        self.title("Panel de Control - VOICEBOT Tesis vFinal")
        self.geometry("1800x960")
        self.configure(bg="#1D1B1A")
        self.configurar_estilos()
        self.crear_widgets()
        self.log_queue = queue.Queue()
        logging.getLogger().addHandler(QueueHandler(self.log_queue))
        self.after(100, self.procesar_cola_logs)
        self.bloquear_controles(False) 
        self.iniciar_stream_video()
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        COLOR_FONDO = "#1D1B1A"
        COLOR_DORADO = "#D9B85F"
        style.configure("TFrame", background=COLOR_FONDO)
        style.configure("TLabel", background=COLOR_FONDO, foreground="#FFFFFF", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=COLOR_FONDO, foreground=COLOR_DORADO, font=("Segoe UI", 24, "bold"), anchor="center")
        style.configure("Info.TLabel", background=COLOR_FONDO, foreground="#FFFFFF", font=("Segoe UI", 11))
        style.configure("TLabelframe", background=COLOR_FONDO, bordercolor="#4f4f4f")
        style.configure("TLabelframe.Label", background=COLOR_FONDO, foreground=COLOR_DORADO, font=("Segoe UI", 14, "bold"))
        style.configure("Ready.TLabel", background="#28a745", foreground="#FFFFFF", font=("Segoe UI", 12, "bold"), anchor="center", padding=5)
        style.configure("Busy.TLabel", background="#dc3545", foreground="#FFFFFF", font=("Segoe UI", 12, "bold"), anchor="center", padding=5)
        style.configure("TButton", background="#3c3c3c", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=10, relief="flat", borderwidth=0)
        style.map("TButton", background=[('active', "#4f4f4f")])
        style.configure("Record.TButton", background="#990000", foreground="#FFFFFF")
        style.map("Record.TButton", background=[('active', '#cc0000')])

    def crear_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1); main_frame.columnconfigure(0, weight=1)

        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ttk.Label(header_frame, text="Panel de Control VOICEBOT", style="Title.TLabel").pack(fill="x", expand=True)

        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.rowconfigure(0, weight=3); content_frame.rowconfigure(1, weight=2)
        content_frame.columnconfigure(0, weight=2); content_frame.columnconfigure(1, weight=2); content_frame.columnconfigure(2, weight=1)

        live_cam_frame = ttk.LabelFrame(content_frame, text=" Video en Vivo ")
        live_cam_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        self.live_video_label = tk.Label(live_cam_frame, bg="#1D1B1A")
        self.live_video_label.pack(fill="both", expand=True, padx=5, pady=5)

        analysis_frame = ttk.LabelFrame(content_frame, text=" Resultado del Análisis ")
        analysis_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
        self.analysis_label = tk.Label(analysis_frame, bg="#1D1B1A")
        self.analysis_label.pack(fill="both", expand=True, padx=5, pady=5)

        status_panel = ttk.LabelFrame(content_frame, text=" Estado del Sistema ")
        status_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", pady=(0, 10))
        status_inner_frame = ttk.Frame(status_panel, padding=15)
        status_inner_frame.pack(fill="both", expand=True)
        
        self.lbl_robot_status = ttk.Label(status_inner_frame, text=" ESTADO: INICIANDO... ")
        self.lbl_robot_status.pack(fill="x", pady=(0, 20))
        ttk.Separator(status_inner_frame).pack(fill="x", pady=10)
        
        # --- ETIQUETAS DE ESTADO RESTAURADAS ---
        ttk.Label(status_inner_frame, text="OBJETOS DETECTADOS:", style="TLabelframe.Label").pack(fill="x", anchor="w")
        self.info_lbl_objetos = ttk.Label(status_inner_frame, text="---", style="Info.TLabel")
        self.info_lbl_objetos.pack(fill="x", pady=5, anchor="w")
        ttk.Separator(status_inner_frame).pack(fill="x", pady=10)

        # --- BOTONES DE ACCIÓN ---
        self.btn_grabar = ttk.Button(status_inner_frame, text="Grabar Comando de Voz", command=self.toggle_grabacion_thread)
        self.btn_grabar.pack(fill="x", pady=5, ipady=10)
        
        self.btn_home = ttk.Button(status_inner_frame, text="Volver a Home", command=self.volver_a_home_thread)
        self.btn_home.pack(fill="x", pady=5, ipady=10)

        ttk.Separator(status_inner_frame).pack(fill="x", pady=10)
        
        self.btn_limpiar = ttk.Button(status_inner_frame, text="Limpiar Escena (Botón)", command=self.limpiar_escena_thread)
        self.btn_limpiar.pack(fill="x", pady=5, ipady=10)

        self.btn_clasificar = ttk.Button(status_inner_frame, text="Clasificar por Forma (Botón)", command=self.clasificar_objetos_thread)
        self.btn_clasificar.pack(fill="x", pady=5, ipady=10)
        
        ttk.Separator(status_inner_frame).pack(fill="x", pady=10)

        self.btn_calibracion = ttk.Button(status_inner_frame, text="Abrir Calibrador", command=self.lanzar_calibrador)
        self.btn_calibracion.pack(fill="x", pady=5, ipady=10)
        
        self.lista_de_botones.extend([self.btn_grabar, self.btn_home, self.btn_limpiar, self.btn_clasificar, self.btn_calibracion])

        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_voicebot.png")
            logo_image = Image.open(logo_path).resize((280, 280), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(status_inner_frame, image=self.logo_photo)
            logo_label.pack(side="bottom", expand=True, pady=20)
        except FileNotFoundError: pass

        terminal_frame = ttk.LabelFrame(content_frame, text=" Consola de Ejecución ")
        terminal_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        self.terminal_output = ScrolledText(terminal_frame, height=10, bg="#0A0A0A", fg="#00FF00", insertbackground="#D9B85F", relief="flat")
        self.terminal_output.pack(fill="both", expand=True, padx=5, pady=5)
        self.terminal_output.configure(state='disabled')

    def lanzar_calibrador(self):
        logging.info("Lanzando la herramienta de calibración...")
        self.logica_tesis.sistema_voz.decir("Abriendo el modo de calibración.")
        
        self.video_running = False
        time.sleep(0.5) 
        self.sistema_vision.liberar_camara()
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "depurador_final.py"], check=True, cwd=script_dir)
            messagebox.showinfo("Calibración Guardada", "Los nuevos valores se han guardado. Por favor, reinicia el programa para aplicar los cambios.")
            self.logica_tesis.sistema_voz.decir("Calibración guardada. Por favor, reinicia la aplicación.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar 'depurador_final.py': {e}")
            self.sistema_vision.iniciar_captura()
            self.iniciar_stream_video()

    def bloquear_controles(self, bloquear=True):
        estado, style = ("disabled", "Busy.TLabel") if bloquear else ("normal", "Ready.TLabel")
        self.lbl_robot_status.config(text=f" ESTADO: {('OCUPADO' if bloquear else 'LISTO')} ", style=style)
        for boton in self.lista_de_botones:
            if boton.winfo_exists(): boton.config(state=estado)

    def actualizar_status_analisis(self):
        count = len(self.logica_tesis.ultimos_objetos_detectados)
        self.info_lbl_objetos.config(text=f"{count} objeto(s) detectado(s)")

    def chequear_hilo_activo(self, thread):
        if not self.winfo_exists(): return
        if thread.is_alive(): self.after(100, self.chequear_hilo_activo, thread)
        else:
            if self.winfo_exists():
                self.bloquear_controles(False)
                self.actualizar_status_analisis()
                if self.logica_tesis.imagen_resultado_analisis is not None:
                    self.actualizar_visor_analisis(self.logica_tesis.imagen_resultado_analisis)

    def actualizar_visor_con_frame(self, label_widget, frame):
        if frame is None: return
        try:
            h, w, _ = frame.shape
            lw, lh = label_widget.winfo_width(), label_widget.winfo_height()
            if lw < 2 or lh < 2: return
            scale = min(lw/w, lh/h)
            img = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
            img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
            label_widget.configure(image=img)
            label_widget.image = img
        except Exception: pass

    def actualizar_video_en_vivo(self):
        while self.video_running:
            try:
                if not self.winfo_exists(): break
                frame = self.sistema_vision.obtener_frame_para_display()
                if frame is not None: self.actualizar_visor_con_frame(self.live_video_label, frame)
                time.sleep(0.033)
            except Exception: pass
        
    def actualizar_visor_analisis(self, frame):
        if self.winfo_exists(): self.actualizar_visor_con_frame(self.analysis_label, frame)
        
    def _iniciar_hilo_y_chequear(self, target_func, args=()):
        self.bloquear_controles(True)
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()
        self.chequear_hilo_activo(thread)
    
    def toggle_grabacion_thread(self):
        if not self.is_recording:
            self.is_recording = True
            self.btn_grabar.config(text="Detener y Procesar", style="Record.TButton")
            self.sistema_audio.iniciar_grabacion()
        else:
            self.is_recording = False
            self.btn_grabar.config(text="Grabar Comando de Voz", style="TButton")
            self._iniciar_hilo_y_chequear(self.logica_tesis.procesar_y_ejecutar_comando_voz)

    def volver_a_home_thread(self): 
        self._iniciar_hilo_y_chequear(self.controlador.mover_a_posicion_home)

    def limpiar_escena_thread(self): 
        self._iniciar_hilo_y_chequear(self.logica_tesis.ejecutar_limpieza)

    def clasificar_objetos_thread(self): 
        self._iniciar_hilo_y_chequear(self.logica_tesis.ejecutar_clasificacion, args=("FORMA",))
            
    def iniciar_stream_video(self):
        if not self.video_running:
            self.video_running = True
            self.video_thread = threading.Thread(target=self.actualizar_video_en_vivo, daemon=True)
            self.video_thread.start()

    def al_cerrar(self):
        if messagebox.askokcancel("Salir", "¿Estás seguro?"):
            self.video_running = False
            self.destroy()

    def procesar_cola_logs(self):
        try:
            while True:
                record = self.log_queue.get(block=False)
                self.terminal_output.configure(state='normal')
                self.terminal_output.insert(tk.END, record + '\n')
                self.terminal_output.see(tk.END)
                self.terminal_output.configure(state='disabled')
        except queue.Empty: pass
        self.after(100, self.procesar_cola_logs)