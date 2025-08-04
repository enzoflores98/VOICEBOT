# calibrador_brazo.py (Corregido)
import cv2
import numpy as np
import logging
import time
import re
import config
from sistema_vision import SistemaVision
from controlador_brazo import ControladorBrazo

class SuperCalibrador:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
        
        self.vision = SistemaVision(config.URL_CAMARA)
        self.controlador = ControladorBrazo(config.PUERTO_COM, config.TASA_BAUDIOS)
        
        self.offsets_servos = np.array([
            config.OFFSET_SERVO_BASE, config.OFFSET_SERVO_HOMBRO,
            config.OFFSET_SERVO_CODO, config.OFFSET_SERVO_PITCH
        ], dtype=np.float32)

        self.offsets_cuadrantes = {
            'Q1': [config.OFFSET_Q1_X_MM, config.OFFSET_Q1_Y_MM],
            'Q2': [config.OFFSET_Q2_X_MM, config.OFFSET_Q2_Y_MM],
            'Q3': [config.OFFSET_Q3_X_MM, config.OFFSET_Q3_Y_MM],
            'Q4': [config.OFFSET_Q4_X_MM, config.OFFSET_Q4_Y_MM]
        }
        
        self.paso_movimiento = 1.0
        self.paso_angular = 1.0
        self.fase_actual = "SERVOS"
        self.punto_objetivo_real = (0, 0, config.ALTURA_PICKING_Z)

    def _dibujar_hud(self, frame):
        h, w, _ = frame.shape
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (450, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        def put_text(text, y_pos, color=(255, 255, 255)):
            cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        put_text(f"--- FASE: {self.fase_actual} ---", 30, (0, 255, 255))
        
        if self.fase_actual == "SERVOS":
            put_text("Ajuste los servos a su 90 grados real.", 50)
            put_text("Teclas: [1/2] Base, [3/4] Hombro, [5/6] Codo, [7/8] Pitch", 70)
            put_text("Presione ENTER para pasar a la siguiente fase.", 90)
            put_text(f"Offsets Servos (B,H,C,P): {self.offsets_servos}", 120, (0, 255, 0))
        else:
            put_text("Alinee la pinza con el punto de mira amarillo.", 50)
            put_text("Use WASD para ajustar el offset X/Y.", 70)
            put_text("Cambiar Cuadrante: Teclas 1, 2, 3, 4", 90)
            put_text("Guardar: G | Salir: ESC", 110)
            offset_actual = self.offsets_cuadrantes[self.fase_actual]
            put_text(f"Offsets {self.fase_actual} (X,Y): {offset_actual[0]:.1f}, {offset_actual[1]:.1f}", 140, (0, 255, 0))

    def _procesar_teclas(self, tecla):
        if tecla == 27: return False # ESC
        
        if self.fase_actual == "SERVOS":
            if ord('1') <= tecla <= ord('8'):
                idx = (tecla - ord('1')) // 2
                signo = 1 if (tecla - ord('1')) % 2 else -1
                self.offsets_servos[idx] += signo * self.paso_angular
                self._mover_a_home_con_offsets()
            elif tecla == 13: # ENTER
                self.fase_actual = "Q1"
                logging.info("Fase Servos finalizada. Pasando a calibración de Offsets Q1.")
                self._mover_a_objetivo_con_offsets()
        else:
            if tecla == ord('w'): self.offsets_cuadrantes[self.fase_actual][1] += self.paso_movimiento
            elif tecla == ord('s'): self.offsets_cuadrantes[self.fase_actual][1] -= self.paso_movimiento
            elif tecla == ord('a'): self.offsets_cuadrantes[self.fase_actual][0] -= self.paso_movimiento
            elif tecla == ord('d'): self.offsets_cuadrantes[self.fase_actual][0] += self.paso_movimiento
            elif ord('1') <= tecla <= ord('4'):
                self.fase_actual = f"Q{chr(tecla)}"
                logging.info(f"Cambiando a calibración de {self.fase_actual}")
            elif tecla == ord('g'): self._guardar_configuracion()
            
            self._mover_a_objetivo_con_offsets()
                
        return True

    def _mover_a_home_con_offsets(self):
        comando = f"P,{90+self.offsets_servos[0]:.2f},{140+self.offsets_servos[1]:.2f},{170+self.offsets_servos[2]:.2f},{10+self.offsets_servos[3]:.2f}\n"
        self.controlador._enviar_comando_y_esperar(comando)
        
    def _mover_a_objetivo_con_offsets(self):
        offset_x = self.offsets_cuadrantes[self.fase_actual][0]
        offset_y = self.offsets_cuadrantes[self.fase_actual][1]
        
        x_final = self.punto_objetivo_real[0] + offset_x
        y_final = self.punto_objetivo_real[1] + offset_y
        z_final = self.punto_objetivo_real[2]
        
        logging.info(f"Moviendo a ({x_final:.1f}, {y_final:.1f}, {z_final:.1f}) para {self.fase_actual}")
        self.controlador.mover_a_coordenadas(x_final, y_final, z_final)

    def _guardar_configuracion(self):
        logging.info("Guardando configuración en config.py...")
        try:
            with open('config.py', 'r') as f:
                content = f.read()
            
            # Usamos raw f-strings (rf"...") para evitar las advertencias de sintaxis
            content = re.sub(rf"(OFFSET_SERVO_BASE\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{self.offsets_servos[0]:.1f}", content)
            content = re.sub(rf"(OFFSET_SERVO_HOMBRO\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{self.offsets_servos[1]:.1f}", content)
            content = re.sub(rf"(OFFSET_SERVO_CODO\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{self.offsets_servos[2]:.1f}", content)
            content = re.sub(rf"(OFFSET_SERVO_PITCH\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{self.offsets_servos[3]:.1f}", content)

            for q_name, values in self.offsets_cuadrantes.items():
                content = re.sub(rf"(OFFSET_{q_name}_X_MM\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{values[0]:.1f}", content)
                content = re.sub(rf"(OFFSET_{q_name}_Y_MM\s*=\s*)(-?\d+\.?\d*)", f"\\g<1>{values[1]:.1f}", content)

            with open('config.py', 'w') as f:
                f.write(content)
            
            logging.info("¡Configuración guardada exitosamente!")

        except Exception as e:
            logging.error(f"No se pudo guardar la configuración: {e}")

    def run(self):
        self._mover_a_home_con_offsets()

        while True:
            frame_original = self.vision.obtener_frame_actual()
            if frame_original is None:
                time.sleep(0.1)
                continue
            
            _, frame_corregido = self.vision.analizar_snapshot(frame_original)
            if frame_corregido is None:
                cv2.imshow("Super Calibrador", frame_original)
                if cv2.waitKey(1) & 0xFF == 27: break
                continue

            if self.fase_actual in ['Q1', 'Q2', 'Q3', 'Q4']:
                h, w, _ = frame_corregido.shape
                objetivo_pixel = (w // 2, h // 2)

                # ==================================================================
                # === INICIO DE LA CORRECCIÓN DE IndexError ===
                # Calculamos X e Y, pero mantenemos el Z definido en la configuración.
                objetivo_x, objetivo_y = self.vision._convertir_pixeles_a_reales(objetivo_pixel, (w, h))
                self.punto_objetivo_real = (objetivo_x, objetivo_y, config.ALTURA_PICKING_Z)
                # === FIN DE LA CORRECCIÓN ===
                # ==================================================================

                cv2.circle(frame_corregido, objetivo_pixel, 10, (0, 255, 255), 2)
                cv2.line(frame_corregido, (objetivo_pixel[0] - 15, objetivo_pixel[1]), (objetivo_pixel[0] + 15, objetivo_pixel[1]), (0, 255, 255), 2)
                cv2.line(frame_corregido, (objetivo_pixel[0], objetivo_pixel[1] - 15), (objetivo_pixel[0], objetivo_pixel[1] + 15), (0, 255, 255), 2)

            self._dibujar_hud(frame_corregido)
            cv2.imshow("Super Calibrador", frame_corregido)
            
            key = cv2.waitKey(1) & 0xFF
            if not self._procesar_teclas(key):
                break

        self.controlador.cerrar_conexion()
        self.vision.liberar_camara()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    calibrador = SuperCalibrador()
    calibrador.run()