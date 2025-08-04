# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                           controlador_brazo.py                             ||
||                CAPA DE ABSTRACCIÓN DE HARDWARE Y CINEMÁTICA                ||
||                                                                            ||
================================================================================
Descripción:
Versión final corregida que carga y aplica los offsets de calibración de los
servos a TODOS los movimientos, incluyendo el posicionamiento inicial a HOME.
"""

import math
import serial
import time
import logging
import config
import numpy as np

class ControladorBrazo:
    def __init__(self, puerto, baud_rate, timeout=2):
        # Parámetros físicos
        self.L1Z, self.L1X, self.L2, self.L3, self.L4 = 60.3, 13.06, 120.0, 120.0, 130.5
        self.SERVO_MIN, self.SERVO_MAX = 0.0, 180.0
        self.ALTURA_Z_PICKING = config.ALTURA_PICKING_Z
        
        # --- CORRECCIÓN: Cargar los offsets de los servos al inicializar ---
        self.offsets_servos = np.array([
            config.OFFSET_SERVO_BASE,
            config.OFFSET_SERVO_HOMBRO,
            config.OFFSET_SERVO_CODO,
            config.OFFSET_SERVO_PITCH
        ], dtype=np.float32)
        
        self.puerto = puerto
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.arduino = None
        
        # Secuencia de inicialización
        self.conectar()
        self.mover_a_posicion_home() # Ahora usará los offsets
        self.cerrar_pinza()

    def conectar(self):
        try:
            logging.info(f"Conectando con Arduino en {self.puerto}...")
            self.arduino = serial.Serial(self.puerto, self.baud_rate, timeout=self.timeout)
            time.sleep(2)
            while self.arduino.in_waiting:
                linea = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                if linea: logging.info(f"Arduino (init): {linea}")
            logging.info("Conexión con Arduino establecida.")
        except serial.SerialException as e:
            logging.error(f"Error al conectar con Arduino: {e}")
            raise e

    def cerrar_conexion(self):
        if self.arduino and self.arduino.is_open:
            logging.info("Cerrando conexión con Arduino.")
            self.arduino.close()

    def _enviar_comando_y_esperar(self, comando):
        if not self.arduino or not self.arduino.is_open: return False
        try:
            logging.info(f"Enviando comando a Arduino: \"{comando.strip()}\"")
            self.arduino.write(comando.encode('utf-8'))
            tiempo_inicio = time.time()
            while time.time() - tiempo_inicio < 10:
                if self.arduino.in_waiting > 0:
                    respuesta = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if respuesta and "alcanzada" in respuesta:
                        logging.info("Confirmación de movimiento recibido.")
                        return True
                time.sleep(0.05)
            logging.warning("No se recibió confirmación de movimiento (timeout).")
            return False
        except Exception as e:
            logging.error(f"Error durante la comunicación con Arduino: {e}")
            return False

    def mover_a_posicion_home(self):
        """Mueve a HOME aplicando siempre los offsets de servo configurados."""
        logging.info("Moviendo el brazo a la posición HOME.")
        # Suma los offsets a la posición teórica de HOME
        angulos_home = np.array(config.POSICION_HOME[:4]) + self.offsets_servos
        comando = f"P,{angulos_home[0]:.2f},{angulos_home[1]:.2f},{angulos_home[2]:.2f},{angulos_home[3]:.2f}\n"
        return self._enviar_comando_y_esperar(comando)

    def mover_a_coordenadas(self, px, py, pz=None):
      """Mueve a coordenadas que ya son finales."""
      if pz is None: pz = self.ALTURA_Z_PICKING
    
    # Ya no se aplica inversión aquí, se confía en las coordenadas recibidas.
      px_final = px
      py_final = py
    
      logging.info(f"Calculando IK para (X:{px_final:.1f}, Y:{py_final:.1f}, Z:{pz:.1f})...")
      resultado_ik = self._find_ik_solution(px_final, py_final, pz)
      if resultado_ik:
          _, servo_positions = resultado_ik
          servo_positions_finales = np.array(servo_positions) + self.offsets_servos
          comando = f"P,{servo_positions_finales[0]:.2f},{servo_positions_finales[1]:.2f},{servo_positions_finales[2]:.2f},{servo_positions_finales[3]:.2f}\n"
          return self._enviar_comando_y_esperar(comando)
      else:
          logging.warning(f"Punto (X:{px_final:.1f}, Y:{py_final:.1f}, Z:{pz:.1f}) es inalcanzable.")
          return False

    def abrir_pinza(self):
        comando = f"G,{config.ANGULO_PINZA_ABIERTA:.2f}\n"
        return self._enviar_comando_y_esperar(comando)

    def cerrar_pinza(self):
        comando = f"G,{config.ANGULO_PINZA_CERRADA:.2f}\n"
        return self._enviar_comando_y_esperar(comando)

    def _map_angles_to_servos(self, q_angles):
        q1, q2, q3, q4 = q_angles
        return (q1, q2, 90 - q3, 90 + q4)
        
    def _check_servo_limits(self, servo_angles):
        # Esta comprobación ahora es menos crítica si los offsets son pequeños,
        # pero se mantiene por seguridad.
        for angle in servo_angles:
            if not (self.SERVO_MIN <= angle <= self.SERVO_MAX):
                return False
        return True
        
    def _calculate_ik_for_pitch(self, px, py, pz, pitch_deg):
        try:
            q1_rad = math.atan2(py, px)
            R = math.sqrt(px**2 + py**2)
            r_tip, z_tip = R - self.L1X, pz - self.L1Z
            pitch_rad = math.radians(pitch_deg)
            r_w, z_w = r_tip - self.L4 * math.cos(pitch_rad), z_tip - self.L4 * math.sin(pitch_rad)
            cos_q3_arg = (r_w**2 + z_w**2 - self.L2**2 - self.L3**2) / (2 * self.L2 * self.L3)
            if not (-1 <= cos_q3_arg <= 1): return None
            q3_rad_sol1, q3_rad_sol2 = -math.acos(cos_q3_arg), math.acos(cos_q3_arg)
            for q3_rad in [q3_rad_sol1, q3_rad_sol2]:
                q2_rad = math.atan2(z_w, r_w) - math.atan2(self.L3 * math.sin(q3_rad), self.L2 + self.L3 * math.cos(q3_rad))
                q4_rad = pitch_rad - q2_rad - q3_rad
                q_angles_deg = (math.degrees(q1_rad), math.degrees(q2_rad), math.degrees(q3_rad), math.degrees(q4_rad))
                servo_positions = self._map_angles_to_servos(q_angles_deg)
                if self._check_servo_limits(servo_positions):
                    return q_angles_deg, servo_positions
            return None
        except (ValueError, ZeroDivisionError):
            return None
            
    def _find_ik_solution(self, px, py, pz):
        for pitch in range(-90, 91, 5):
            result = self._calculate_ik_for_pitch(px, py, pz, float(pitch))
            if result:
                return result
        return None
