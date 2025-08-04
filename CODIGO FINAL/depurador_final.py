# depurador_final.py (Versión con verificación de config)
import cv2
import cv2.aruco as aruco
import numpy as np
import yaml
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

def seleccionar_color(config_color, window_root):
    """Muestra una ventana para que el usuario elija qué color calibrar."""
    color_seleccionado = ""
    selector_window = tk.Toplevel(window_root)
    selector_window.title("Seleccionar Color")
    selector_window.geometry("300x200")
    selector_window.resizable(False, False)
    
    ttk.Label(selector_window, text="¿Qué color deseas calibrar?", font=("Segoe UI", 12)).pack(pady=10)
    
    def on_select(color):
        nonlocal color_seleccionado
        color_seleccionado = color
        selector_window.destroy()

    for color in config_color.keys():
        ttk.Button(selector_window, text=color.capitalize(), command=lambda c=color: on_select(c)).pack(fill="x", padx=20, pady=5)
    
    window_root.wait_window(selector_window)
    return color_seleccionado

def cargar_config_existente():
    """Carga las configuraciones de color y forma existentes."""
    config_color = None
    config_forma = {'sensibilidad': 0.02}
    try:
        if os.path.exists('lab_config.yaml'):
            with open('lab_config.yaml', 'r') as file:
                config_color = yaml.safe_load(file)
                if not isinstance(config_color, dict) or not config_color:
                    messagebox.showerror("Error de Configuración", "El archivo 'lab_config.yaml' está vacío o tiene un formato incorrecto.")
                    return None, None
        else:
            messagebox.showerror("Error de Configuración", "No se encontró el archivo 'lab_config.yaml'. Por favor, créalo antes de ejecutar el calibrador.")
            return None, None

        if os.path.exists('forma_config.json'):
            with open('forma_config.json', 'r') as file:
                config_forma = json.load(file)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")
        return None, None

    return config_color, config_forma

def guardar_config_final(config_color, config_forma):
    """Guarda las configuraciones finales."""
    with open('lab_config.yaml', 'w') as file:
        yaml.dump(config_color, file, default_flow_style=False)
    print(">>> Configuración de color guardada en 'lab_config.yaml'")
    with open('forma_config.json', 'w') as file:
        json.dump(config_forma, file, indent=4)
    print(">>> Configuración de forma guardada en 'forma_config.json'")

def ejecutar_calibrador():
    root = tk.Tk()
    root.withdraw() # Ocultamos la ventana principal de Tkinter
    
    config_color, config_forma = cargar_config_existente()
    if config_color is None:
        root.destroy()
        return

    color_a_calibrar = seleccionar_color(config_color, root)
    root.destroy()

    if not color_a_calibrar:
        print("No se seleccionó ningún color. Saliendo del calibrador.")
        return

    # El resto del script es igual
    URL_CAMARA = 1
    print(f"Calibrando el color: '{color_a_calibrar}'")
    valores_iniciales = config_color[color_a_calibrar]
    sensibilidad_inicial = int(config_forma.get('sensibilidad', 0.04) * 100)
    
    try:
        camera_matrix, dist_coeffs = np.load('camera_matrix.npy'), np.load('dist_coeffs.npy')
        calibracion_cargada = True
    except FileNotFoundError:
        calibracion_cargada = False
    
    detector = aruco.ArucoDetector(aruco.getPredefinedDictionary(aruco.DICT_5X5_100), aruco.DetectorParameters())
    cap = cv2.VideoCapture(URL_CAMARA)

    cv2.namedWindow("Controles")
    cv2.createTrackbar("L Min", "Controles", valores_iniciales['min'][0], 255, lambda x:x)
    cv2.createTrackbar("L Max", "Controles", valores_iniciales['max'][0], 255, lambda x:x)
    cv2.createTrackbar("A Min", "Controles", valores_iniciales['min'][1], 255, lambda x:x)
    cv2.createTrackbar("A Max", "Controles", valores_iniciales['max'][1], 255, lambda x:x)
    cv2.createTrackbar("B Min", "Controles", valores_iniciales['min'][2], 255, lambda x:x)
    cv2.createTrackbar("B Max", "Controles", valores_iniciales['max'][2], 255, lambda x:x)
    cv2.createTrackbar("Sensibilidad Forma", "Controles", sensibilidad_inicial, 100, lambda x:x)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        if calibracion_cargada:
            h, w = frame.shape[:2]
            new_cam_mtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1, (w, h))
            frame = cv2.undistort(frame, camera_matrix, dist_coeffs, None, new_cam_mtx)
            x, y, w, h = roi
            frame = frame[y:y+h, x:x+w]
        
        image_warped = frame.copy()
        corners, ids, _ = detector.detectMarkers(frame)
        if ids is not None and all(i in ids for i in [0, 1, 3, 4]):
            p_fuente = np.array([corners[np.where(ids.flatten() == i)[0][0]][0][0] for i in [0, 1, 3, 4]], dtype="float32")
            h, w, _ = frame.shape
            p_destino = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype="float32")
            M = cv2.getPerspectiveTransform(p_fuente, p_destino)
            image_warped = cv2.warpPerspective(frame, M, (w, h))
        else:
            cv2.putText(image_warped, "ARUCOS NO DETECTADOS", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        
        lab = cv2.cvtColor(image_warped, cv2.COLOR_BGR2LAB)
        l_min,l_max,a_min,a_max,b_min,b_max = [cv2.getTrackbarPos(n,"Controles") for n in ["L Min","L Max","A Min","A Max","B Min","B Max"]]
        sensibilidad = cv2.getTrackbarPos("Sensibilidad Forma", "Controles") / 100.0
        
        mask = cv2.inRange(lab, np.array([l_min,a_min,b_min]), np.array([l_max,a_max,b_max]))
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) > 500:
                epsilon = (sensibilidad if sensibilidad > 0 else 0.001) * cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, epsilon, True)
                cv2.drawContours(image_warped, [approx], -1, (0, 255, 0), 2)
                cv2.putText(image_warped, f"VERTICES: {len(approx)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        cv2.putText(image_warped, f"Calibrando: {color_a_calibrar.upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.imshow("Imagen Procesada", image_warped)
        cv2.imshow("Mascara", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            sensibilidad_final = cv2.getTrackbarPos("Sensibilidad Forma", "Controles") / 100.0
            config_color[color_a_calibrar]['min'] = [l_min, a_min, b_min]
            config_color[color_a_calibrar]['max'] = [l_max, a_max, b_max]
            config_forma['sensibilidad'] = sensibilidad_final
            guardar_config_final(config_color, config_forma)
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ejecutar_calibrador()