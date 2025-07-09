import cv2
import cv2.aruco as aruco
import numpy as np

# Diccionario de ArUco y parámetros de detección
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
parameters = aruco.DetectorParameters()

# Definición de rangos de color en HSV
COLOR_RANGES = {
    'ROJO': [
        [(0, 120, 70), (10, 255, 255)],
        [(170, 120, 70), (180, 255, 255)]
    ],
    'NEGRO': [[(0, 0, 0), (180, 255, 50)]],
}

def inicializar_captura():
    """Inicializa la cámara y devuelve el objeto de captura."""
    cap = cv2.VideoCapture('http://192.168.1.34:4747/video')
    #cap = cv2.VideoCapture(0)
    return cap

def arucos(image):
    corners, ids, _ = aruco.detectMarkers(image, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) >= 4:
        image = aruco.drawDetectedMarkers(image, corners, ids)
        
        src_points = obtener_puntos_fuente(corners, ids)
        if src_points is not None and src_points.shape == (4, 2):
            M = cv2.getPerspectiveTransform(src_points, np.array(
                [[0, 0], [image.shape[1], 0], [image.shape[1], image.shape[0]], [0, image.shape[0]]],
                dtype="float32"))
            warped = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))
            
            return warped
        else:
            print("No se encontraron puntos suficientes para la transformación.")
            return None
    else:
        print("No se encontraron suficientes marcadores ArUco.")
        return None

def obtener_puntos_fuente(corners, ids):
    ids_requeridos = [0, 1, 2, 3]
    if all(i in ids for i in ids_requeridos):
        esquinas_ordenadas = [corners[np.where(ids == i)[0][0]][0][0] for i in ids_requeridos]
        return np.array(esquinas_ordenadas, dtype="float32")
    return None

def detectar_color(hsv, x, y, w, h):
    roi = hsv[y:y+h, x:x+w]
    for color, ranges in COLOR_RANGES.items():
        for lower, upper in ranges:
            mask = cv2.inRange(roi, np.array(lower), np.array(upper))
            if cv2.countNonZero(mask) > 0:
                return color
    return "desconocido"

def calcular_centro(x, y, w, h):
    return (x + w // 2, y + h // 2)

def analizar_imagen(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, th3 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(th3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centros_objetos = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 1000:
            continue
        approx = cv2.approxPolyDP(contour, 0.03 * cv2.arcLength(contour, True), True)
        x, y, w, h = cv2.boundingRect(approx)

        if len(approx) == 4 or len(approx) == 5:
            shape = "CUBO"
        elif len(approx) > 8:
            shape = "CILINDRO"
        elif len(approx) == 3:
            shape = "TRIANGULO"
        else:
            shape = "CILINDRO"
        print(len(approx))
        color = detectar_color(hsv, x, y, w, h)
        cx, cy = calcular_centro(x, y, w, h)
        centros_objetos.append((shape, color, cx, cy))
    imagen_contornos = image.copy()
    cv2.drawContours(imagen_contornos, contours, -1, (0, 255, 0), 2)
    cv2.imshow("Contornos detectados", imagen_contornos)
    cv2.waitKey(1)
        
    return centros_objetos

def capturar_y_analizar(frame):
    """Analiza un frame capturado."""
    if frame is None:
        print("El frame proporcionado es nulo.")
        return []

    # Procesamiento de la imagen capturada
    frame2 = arucos(frame)  # Aplicar detección de ArUco
    if frame2 is not None:
        centros = analizar_imagen(frame2)  # Análisis de objetos en la imagen
        for centro in centros:
            print(f"Forma: {centro[0]}, Color: {centro[1]}, Centro: ({centro[2]}, {centro[3]})")
        return centros
    else:
        print("No se pudo obtener una imagen válida de la transformación perspectiva.")
        return []



# Función principal para ejecutar el script de forma independiente
def main():
    cap = inicializar_captura()
    print("Presiona 's' para capturar y analizar una imagen, o 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo obtener el frame")
            break

        cv2.imshow('Presiona "s" para capturar', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            # Al presionar 's', captura una imagen y la analiza
            centros = capturar_y_analizar(frame)
            print("Centros detectados:", centros)

        elif key == ord('q'):
            print("Saliendo...")
            break

    cap.release()
    cv2.destroyAllWindows()

''' #DESCOMENTAR PARA CORRERLO INDIVIDUALMENTE
if __name__ == "__main__":
    main()
'''