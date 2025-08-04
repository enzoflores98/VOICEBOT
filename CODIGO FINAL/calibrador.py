# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                              calibrador.py                                 ||
||             HERRAMIENTA DE CALIBRACIÓN MANO-OJO PARA LA TESIS              ||
||                                                                            ||
================================================================================
Descripción:
Este script aislado permite calibrar la relación espacial entre el sistema de
coordenadas de la cámara (definido por los ArUcos) y el sistema de coordenadas
del robot.

Instrucciones de Uso:
1. Ejecuta este script.
2. Una ventana de OpenCV mostrará la vista de la cámara. Asegúrate de que los
   4 marcadores ArUco (0, 1, 3, 4) sean visibles.
3. El script dibujará un punto de mira (crosshair) en el centro del área de
   trabajo detectada.
4. Usa las teclas W, A, S, D para mover el brazo robótico.
5. Mueve físicamente la punta de la pinza del robot hasta que esté perfectamente
   alineada con el centro del punto de mira en la pantalla.
6. Una vez alineado, presiona la tecla 'c' para calcular y guardar la calibración.
7. El script imprimirá en la consola los valores de configuración que debes
   copiar y pegar en tu archivo `config.py`.
8. Presiona 'q' para salir.
"""

import cv2
import numpy as np
import logging
import config
from sistema_vision import SistemaVision
from controlador_brazo import ControladorBrazo

class Calibrador:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        # Inicializar los módulos principales
        logging.info("Inicializando módulos...")
        self.vision = SistemaVision(config.URL_CAMARA)
        self.controlador = ControladorBrazo(config.PUERTO_COM, config.TASA_BAUDIOS)
        
        # Estado de la calibración
        self.posicion_actual_robot = [0.0, 150.0] # Posición inicial segura (X, Y)
        self.paso_movimiento = 2.0 # Movimiento en mm por cada tecla presionada

    def _dibujar_ayudas_visuales(self, frame, centro_pixel):
        """Dibuja el punto de mira y el texto de ayuda en la imagen."""
        # Dibujar punto de mira en el centro del área de trabajo
        if centro_pixel:
            cx, cy = centro_pixel
            cv2.circle(frame, (cx, cy), 10, (0, 255, 255), 2)
            cv2.line(frame, (cx - 15, cy), (cx + 15, cy), (0, 255, 255), 2)
            cv2.line(frame, (cx, cy - 15), (cx, cy + 15), (0, 255, 255), 2)

        # Dibujar texto de ayuda
        cv2.putText(frame, "Usa WASD para mover. +/- para Z. 'c' para calibrar. 'q' para salir.", 
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Mostrar la posición actual del robot
        pos_texto = f"Robot (X,Y): ({self.posicion_actual_robot[0]:.1f}, {self.posicion_actual_robot[1]:.1f})"
        cv2.putText(frame, pos_texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

    def _mover_brazo_manual(self, tecla):
        """Actualiza la posición del robot según la tecla presionada."""
        x, y = self.posicion_actual_robot
        
        if tecla == ord('w'): y += self.paso_movimiento
        elif tecla == ord('s'): y -= self.paso_movimiento
        elif tecla == ord('a'): x -= self.paso_movimiento
        elif tecla == ord('d'): x += self.paso_movimiento
        else: return # No hacer nada si no es una tecla de movimiento

        self.posicion_actual_robot = [x, y]
        logging.info(f"Moviendo a nueva posición: {self.posicion_actual_robot}")
        # Mueve el brazo a la nueva posición a la altura de picking
        self.controlador.mover_a_coordenadas(x, y, config.ALTURA_PICKING_Z)

    def iniciar_calibracion_manual(self):
        """Bucle principal de la herramienta de calibración."""
        logging.info("Iniciando herramienta de calibración manual...")
        
        while True:
            # Obtener el frame corregido por perspectiva
            frame_original = self.vision.obtener_frame_actual()
            if frame_original is None:
                time.sleep(0.1)
                continue
            
            _, frame_corregido = self.vision.analizar_snapshot(frame_original)

            if frame_corregido is None:
                cv2.imshow("Calibrador", frame_original)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
                continue

            # El centro del área de trabajo en píxeles es el centro del frame corregido
            h, w, _ = frame_corregido.shape
            centro_area_pixel = (w // 2, h // 2)

            # Dibujar ayudas visuales
            self._dibujar_ayudas_visuales(frame_corregido, centro_area_pixel)
            
            cv2.imshow("Calibrador - Alinea la pinza con el punto de mira", frame_corregido)
            
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                logging.info("Saliendo de la herramienta de calibración.")
                break
            elif key in [ord('w'), ord('a'), ord('s'), ord('d')]:
                self._mover_brazo_manual(key)
            elif key == ord('c'):
                self.calcular_y_mostrar_resultados()
                # Esperar a que el usuario presione 'q' para salir
                while True:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                break

        self.controlador.cerrar_conexion()
        self.vision.liberar_camara()
        cv2.destroyAllWindows()

    def calcular_y_mostrar_resultados(self):
        """Calcula y muestra los valores de calibración finales."""
        logging.info("Calculando resultados de la calibración...")
        
        # La posición actual del robot (que hemos movido manualmente) corresponde
        # al centro del área de trabajo (el punto (0,0) del sistema de la cámara).
        origen_x_robot = self.posicion_actual_robot[0]
        origen_y_robot = self.posicion_actual_robot[1]

        print("\n" + "="*60)
        print("=== ¡CALIBRACIÓN COMPLETADA! ===")
        print("="*60)
        print("\nPor favor, copia las siguientes líneas y pégalas en tu archivo 'config.py',")
        print("reemplazando los valores de calibración existentes.")
        print("\n" + "-"*60)
        print(f"ORIGEN_AREA_TRABAJO_X_MM = {origen_x_robot:.2f}")
        print(f"ORIGEN_AREA_TRABAJO_Y_MM = {origen_y_robot:.2f}")
        print("-"*60)
        print("\nPresiona 'q' en la ventana de la cámara para salir.")

if __name__ == "__main__":
    calibrador = Calibrador()
    calibrador.iniciar_calibracion_manual()
