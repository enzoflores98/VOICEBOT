# calibrador_offset_manual.py
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import logging

# Importar los módulos de tu proyecto
import config
from controlador_brazo import ControladorBrazo
from sistema_vision import SistemaVision

class CalibradorOffsetsGUI(tk.Tk):
    def __init__(self, controlador, sistema_vision):
        super().__init__()
        self.controlador = controlador
        self.sistema_vision = sistema_vision
        
        # --- Configuración de la Ventana ---
        self.title("Asistente de Calibración de Offsets (Modo Manual)")
        self.geometry("1280x800")
        
        # --- Variables de Estado ---
        self.offsets = {'Q1': [0.0, 0.0], 'Q2': [0.0, 0.0], 'Q3': [0.0, 0.0], 'Q4': [0.0, 0.0]}
        self.quadrant_var = tk.StringVar(value="Q1")
        self.offset_x_var = tk.DoubleVar(value=0.0)
        self.offset_y_var = tk.DoubleVar(value=0.0)

        # --- Crear Widgets ---
        self.crear_widgets()
        
        # --- Iniciar Video y Bindings ---
        self.last_frame = None
        self.actualizar_video()
        self.video_label.bind("<Button-1>", self.on_video_click)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def crear_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # ==================================================================
        # === INICIO DE LA CORRECCIÓN ===
        # Se quita el guion bajo de "column_configure" y "row_configure"
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        # === FIN DE LA CORRECCIÓN ===
        # ==================================================================

        # --- Panel de Video ---
        video_frame = ttk.LabelFrame(main_frame, text="Video en Vivo (Haz clic para probar)")
        video_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill="both", expand=True)

        # --- Panel de Controles ---
        control_frame = ttk.LabelFrame(main_frame, text="Controles de Calibración")
        control_frame.grid(row=0, column=1, sticky="nsew")
        
        # Selector de Cuadrante
        ttk.Label(control_frame, text="1. Selecciona un Cuadrante:", font=("Segoe UI", 10, "bold")).pack(pady=10, anchor="w", padx=10)
        for q_text in ["Q1 (X+, Y-)", "Q2 (X-, Y-)", "Q3 (X-, Y+)", "Q4 (X+, Y+)"]:
            q_val = q_text.split(" ")[0]
            ttk.Radiobutton(control_frame, text=q_text, variable=self.quadrant_var, value=q_val, command=self.on_quadrant_select).pack(anchor="w", padx=20)
        
        ttk.Separator(control_frame).pack(fill="x", pady=15, padx=10)

        # Sliders de Offset
        ttk.Label(control_frame, text="2. Ajusta los Offsets (mm):", font=("Segoe UI", 10, "bold")).pack(pady=10, anchor="w", padx=10)
        
        # Slider X
        ttk.Label(control_frame, text="Offset X:").pack(padx=10, anchor="w")
        self.slider_x = ttk.Scale(control_frame, from_=-100, to=100, orient="horizontal", variable=self.offset_x_var, command=self.on_slider_change)
        self.slider_x.pack(fill="x", padx=10, pady=(0, 10))
        self.label_x_val = ttk.Label(control_frame, text="0.0 mm")
        self.label_x_val.pack()

        # Slider Y
        ttk.Label(control_frame, text="Offset Y:").pack(padx=10, anchor="w", pady=(10,0))
        self.slider_y = ttk.Scale(control_frame, from_=-100, to=100, orient="horizontal", variable=self.offset_y_var, command=self.on_slider_change)
        self.slider_y.pack(fill="x", padx=10, pady=(0, 10))
        self.label_y_val = ttk.Label(control_frame, text="0.0 mm")
        self.label_y_val.pack()

        ttk.Separator(control_frame).pack(fill="x", pady=15, padx=10)

        # Botones de Acción
        ttk.Label(control_frame, text="3. Finaliza y Copia:", font=("Segoe UI", 10, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.show_button = ttk.Button(control_frame, text="Mostrar Offsets en Consola", command=self.mostrar_offsets_en_consola)
        self.show_button.pack(fill="x", padx=10, pady=10, ipady=10)

        self.home_button = ttk.Button(control_frame, text="Mover Brazo a HOME", command=self.mover_a_home)
        self.home_button.pack(fill="x", padx=10, pady=10)

        self.on_quadrant_select()

    def on_quadrant_select(self):
        quadrant = self.quadrant_var.get()
        current_offsets = self.offsets[quadrant]
        self.offset_x_var.set(current_offsets[0])
        self.offset_y_var.set(current_offsets[1])
        self.label_x_val.config(text=f"{current_offsets[0]:.1f} mm")
        self.label_y_val.config(text=f"{current_offsets[1]:.1f} mm")

    def on_slider_change(self, event):
        quadrant = self.quadrant_var.get()
        new_x = self.offset_x_var.get()
        new_y = self.offset_y_var.get()
        self.offsets[quadrant] = [new_x, new_y]
        self.label_x_val.config(text=f"{new_x:.1f} mm")
        self.label_y_val.config(text=f"{new_y:.1f} mm")
    
    def on_video_click(self, event):
        if self.last_frame is None: return
        
        widget_w, widget_h = self.video_label.winfo_width(), self.video_label.winfo_height()
        frame_h, frame_w, _ = self.last_frame.shape
        scale = min(widget_w/frame_w, widget_h/frame_h)
        scaled_w, scaled_h = int(frame_w*scale), int(frame_h*scale)
        
        offset_x = (widget_w - scaled_w) // 2
        offset_y = (widget_h - scaled_h) // 2
        
        if not (offset_x <= event.x < offset_x + scaled_w and offset_y <= event.y < offset_y + scaled_h):
            return

        pixel_x = int((event.x - offset_x) / scale)
        pixel_y = int((event.y - offset_y) / scale)
        
        real_x, real_y = self.sistema_vision._convertir_pixeles_a_reales((pixel_x, pixel_y), (frame_w, frame_h))
        
        current_offsets = self.offsets[self.quadrant_var.get()]
        final_x = real_x + current_offsets[0]
        final_y = real_y + current_offsets[1]
        
        logging.info(f"Clic en ({pixel_x}, {pixel_y}). Real: ({real_x:.1f}, {real_y:.1f}). Offsets: {current_offsets}. Final: ({final_x:.1f}, {final_y:.1f})")

        self.controlador.mover_a_coordenadas(final_x, final_y, pz=config.ALTURA_PICKING_Z)
        self.controlador.mover_a_coordenadas(final_x, final_y, pz=config.ALTURA_SEGURA_Z)

    def mostrar_offsets_en_consola(self):
        """Imprime los offsets actuales en la consola para copiarlos a config.py."""
        print("\n" + "="*50)
        print("=== Offsets para copiar en config.py ===")
        print("="*50 + "\n")
        print("# --- Offsets de Posición por Cuadrante (en mm) ---")
        for q_name, values in self.offsets.items():
            print(f"OFFSET_{q_name}_X_MM = {values[0]:.1f}")
            print(f"OFFSET_{q_name}_Y_MM = {values[1]:.1f}")
        print("\n" + "="*50 + "\n")
        
        messagebox.showinfo("Valores en Consola", "Los valores de offset han sido impresos en tu consola/terminal. ¡Ya puedes copiarlos a tu archivo config.py!")

    def mover_a_home(self):
        self.controlador.mover_a_posicion_home()

    def actualizar_video(self):
        frame = self.sistema_vision.obtener_frame_para_display()
        if frame is not None:
            self.last_frame = frame
            
            h, w, _ = frame.shape
            widget_w, widget_h = self.video_label.winfo_width(), self.video_label.winfo_height()
            if widget_w > 1 and widget_h > 1:
                scale = min(widget_w/w, widget_h/h)
                img = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
                
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                img_tk = ImageTk.PhotoImage(image=img)
                
                self.video_label.config(image=img_tk)
                self.video_label.image = img_tk
        
        self.after(33, self.actualizar_video)

    def on_closing(self):
        logging.info("Cerrando calibrador de offsets...")
        self.controlador.cerrar_conexion()
        self.sistema_vision.liberar_camara()
        self.destroy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
    
    try:
        logging.info("Iniciando módulos para el calibrador...")
        controlador = ControladorBrazo(config.PUERTO_COM, config.TASA_BAUDIOS)
        vision = SistemaVision(config.URL_CAMARA)
        
        app = CalibradorOffsetsGUI(controlador, vision)
        app.mainloop()

    except Exception as e:
        logging.error(f"Error fatal al iniciar el calibrador: {e}")
        messagebox.showerror("Error de Inicio", f"No se pudieron inicializar los módulos del robot. Verifica las conexiones.\n\nError: {e}")