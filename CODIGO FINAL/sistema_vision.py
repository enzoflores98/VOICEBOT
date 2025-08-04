# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                           sistema_vision.py                                ||
||                   MÓDULO DE VISIÓN POR COMPUTADORA PARA TESIS              ||
||          -- Versión Final con Función de Ayuda para Calibrador --          ||
||                                                                            ||
================================================================================
"""

import cv2
import cv2.aruco as aruco
import numpy as np
import threading
import time
import logging
import yaml
import os
import math
import config
import json

class SistemaVision:
    def __init__(self, url_camara):
        self.url_camara = url_camara
        self.cap = None
        self.is_running = False
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
        self.aruco_params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        try:
            self.camera_matrix = np.load('camera_matrix.npy')
            self.dist_coeffs = np.load('dist_coeffs.npy')
            self.calibracion_cargada = True
            logging.info("Calibración de lente cargada.")
        except FileNotFoundError:
            self.calibracion_cargada = False
            logging.warning("No se encontró calibración de lente.")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.lab_data = self._cargar_configuracion_yaml(os.path.join(script_dir, "lab_config.yaml"))
        self.sensibilidad_forma = self._cargar_configuracion_json(os.path.join(script_dir, "forma_config.json"))
        
        if not self.lab_data: raise RuntimeError("No se pudo cargar 'lab_config.yaml'.")
        self.iniciar_captura()

    def _cargar_configuracion_yaml(self, ruta_archivo):
        if not os.path.exists(ruta_archivo): return {}
        with open(ruta_archivo, 'r') as file:
            return yaml.safe_load(file)

    def _cargar_configuracion_json(self, ruta_archivo):
        sensibilidad_defecto = 0.03
        if not os.path.exists(ruta_archivo):
            logging.warning(f"No se encontró '{os.path.basename(ruta_archivo)}'. Usando sensibilidad por defecto: {sensibilidad_defecto}")
            return sensibilidad_defecto
        with open(ruta_archivo, 'r') as file:
            config = json.load(file)
            sensibilidad = config.get('sensibilidad', sensibilidad_defecto)
            logging.info(f"Sensibilidad de forma cargada: {sensibilidad}")
            return sensibilidad

    def iniciar_captura(self):
        self.cap = cv2.VideoCapture(self.url_camara)
        if not self.cap.isOpened(): raise ConnectionError("Cámara no disponible.")
        self.is_running = True
        self.thread_captura = threading.Thread(target=self._bucle_captura, daemon=True)
        self.thread_captura.start()

    def _bucle_captura(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                if self.calibracion_cargada:
                    h, w = frame.shape[:2]
                    new_cam_mtx, roi = cv2.getOptimalNewCameraMatrix(self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h))
                    frame_corregido = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs, None, new_cam_mtx)
                    x, y, w, h = roi
                    frame_corregido = frame_corregido[y:y+h, x:x+w]
                else:
                    frame_corregido = frame
                
                with self.frame_lock:
                    self.latest_frame = frame_corregido
            else: 
                time.sleep(0.1)
    
    def obtener_frame_actual(self):
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def _obtener_puntos_fuente(self, corners, ids):
        ids_req = [0, 1, 3, 4]
        if all(i in ids for i in ids_req):
            return np.array([corners[np.where(ids == i)[0][0]][0][0] for i in ids_req], dtype="float32")
        return None

    def _detectar_forma(self, contorno):
        epsilon = self.sensibilidad_forma * cv2.arcLength(contorno, True)
        approx = cv2.approxPolyDP(contorno, epsilon, True)
        if len(approx) >= 8: return "CILINDRO"
        elif len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            if 0.65 <= (float(w) / h if h > 0 else 0) <= 1.45: return "CUBO"# if 0.85 <= (float(w) / h if h > 0 else 0) <= 1.15: return "CUBO"
        return "OTRO"

    def _convertir_pixeles_a_reales(self, centro_pixel, dim_frame):
        px, py = centro_pixel
        frame_w, frame_h = dim_frame
        local_x = (px/frame_w)*config.AREA_TRABAJO_ANCHO_MM - (config.AREA_TRABAJO_ANCHO_MM/2)
        local_y = (1-(py/frame_h))*config.AREA_TRABAJO_ALTO_MM
        inv_x = -1 if config.INVERTIR_EJE_X else 1
        inv_y = -1 if config.INVERTIR_EJE_Y else 1
        return (local_x*inv_x)+config.ORIGEN_AREA_TRABAJO_X_MM, (local_y*inv_y)+config.ORIGEN_AREA_TRABAJO_Y_MM

    def _detectar_objetos_y_dibujar(self, image_warped, dibujar_coords=False):
        lab = cv2.cvtColor(image_warped, cv2.COLOR_BGR2LAB)
        objetos = []
        for color, rango in self.lab_data.items():
            if 'min' not in rango or 'max' not in rango: continue
            mask = cv2.inRange(lab, np.array(rango['min']), np.array(rango['max']))
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                if cv2.contourArea(c) > 500:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                        forma = self._detectar_forma(c)
                        if forma != "OTRO":
                            obj_data = {'color':color.upper(), 'forma':forma, 'centro_pixel':(cx,cy)}
                            if dibujar_coords:
                                h, w, _ = image_warped.shape
                                obj_data['coord_reales'] = self._convertir_pixeles_a_reales((cx,cy), (w,h))
                            objetos.append(obj_data)
        
        if dibujar_coords:
            for obj in objetos:
                (cx, cy) = obj['centro_pixel']
                texto = f"{obj['forma']} {obj['color']}"
                cv2.circle(image_warped, (cx, cy), 15, (0, 255, 0), 2)
                cv2.putText(image_warped, texto, (cx - 40, cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        return objetos, image_warped

    def analizar_snapshot(self, frame_snapshot):
        if frame_snapshot is None: return [], None
        return self._procesar_frame(frame_snapshot, es_analisis_completo=True)

    def obtener_frame_para_display(self):
        frame = self.obtener_frame_actual()
        if frame is None: return None
        _, imagen = self._procesar_frame(frame, es_analisis_completo=False, dibujar=True)
        return imagen

    def _procesar_frame(self, frame_actual, es_analisis_completo=False, dibujar=False):
        image_warped = self._procesar_frame_para_calibracion(frame_actual)

        # Si la corrección de perspectiva falló (image_warped es None), no se puede analizar.
        # Devolvemos una lista de objetos vacía y la imagen original con un aviso.
        if image_warped is None:
            imagen_con_aviso = frame_actual.copy()
            # Añade un texto de aviso visual para el usuario en la GUI
            cv2.putText(imagen_con_aviso, "AREA NO DETECTADA", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            return [], imagen_con_aviso

        # Si la corrección fue exitosa, procedemos con la detección como siempre.
        lista_obj, imagen_dibujada = self._detectar_objetos_y_dibujar(
            image_warped,
            dibujar_coords=es_analisis_completo or dibujar
        )
        return lista_obj, imagen_dibujada

    def _procesar_frame_para_calibracion(self, frame_actual):
        """Realiza solo el procesamiento geométrico y devuelve la imagen lista."""
        if frame_actual is None: return None
        
        corners, ids, _ = self.detector.detectMarkers(frame_actual)
        if ids is not None and all(i in ids for i in [0, 1, 3, 4]):
            p_fuente = self._obtener_puntos_fuente(corners, ids.flatten())
            # Si no se obtienen los puntos, la corrección falla
            if p_fuente is None:
                return None
            
            h, w, _ = frame_actual.shape
            p_destino = np.array([[0,0], [w,0], [w,h], [0,h]], dtype="float32")
            M = cv2.getPerspectiveTransform(p_fuente, p_destino)
            image_warped = cv2.warpPerspective(frame_actual, M, (w,h))
            return image_warped
        else:
            # Si los marcadores no se detectan, la corrección falla
            return None

    def liberar_camara(self):
        self.is_running = False
        if hasattr(self, 'thread_captura'): 
            self.thread_captura.join(timeout=1.0)
        if self.cap: 
            self.cap.release()
            self.cap = None