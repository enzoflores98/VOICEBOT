#import deteccion
#import instrucciones_por_voz
#import DH5GL_inversa
#import control_braccio
import cv2
from deteccion_modular import inicializar_captura, capturar_y_analizar
from audio import obtener_comando_por_voz
from cinematica import control_brazo


#def procesar_orden(centros_orden):
 
def proceso_orden(comando, centros):
    orden=comando.split()
    print("orden es ",orden)
    centro_objeto = [0, 0, 0]
    for centro in centros:
        if centro[0] == orden[0] and centro[1] == orden[1]:
            centro_objeto[0] = centro[2]
            centro_objeto[1] = centro[3]
            centro_objeto[2] = orden[2] #Se asigna el deposito a la posicion [2] del vector (mejorable en cuanto a nomenclatura)
            break
    
    return centro_objeto 
  
def main():
    cap = inicializar_captura()  # Inicia la captura de la cámara

    if not cap.isOpened():
        print("Error al abrir la cámara.")
        return

    print('Presiona "q" para salir. El sistema esperará tu comando para capturar y analizar la imagen.')

    while True:
        # Captura un frame de la cámara para mostrarlo en tiempo real
        ret, frame = cap.read()
        if not ret:
            print("No se pudo obtener el frame")
            break

        # Mostrar el video en tiempo real para que el usuario vea lo que está captando
        cv2.imshow('Presiona "q" para salir', frame)

        # Verifica si se presionó la tecla "q" para salir
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Saliendo del sistema...")
            break

        # Detectar si el usuario presiona la barra espaciadora para comenzar el flujo
        if key == ord(' '):  # Barra espaciadora
            print("Barra espaciadora presionada. Capturando imagen para análisis...")

            # Captura un frame estático para analizar
            ret, captured_frame = cap.read()
            if not ret:
                print("No se pudo capturar la imagen para analizar.")
                continue

            print("Imagen capturada, iniciando análisis...")
            centros = capturar_y_analizar(captured_frame)  # Ahora pasa la imagen capturada

            # Cerrar la cámara después de capturar y analizar la imagen
            cap.release()
            cv2.destroyAllWindows()
            print("Cámara cerrada después de capturar la imagen.")

            if centros:  # Si se detectaron objetos
                print(f"Objetos detectados: {centros}")
                # Ahora comienza la grabación de audio
                print("Comenzando grabación de audio...")
                comando = obtener_comando_por_voz()
            else:
                print("No se detectaron objetos válidos en la imagen capturada.")
                comando = None

            if comando:
                print(f"Comando recibido: {comando}")
                # Matcheo comando y objetos detectados
                coor=proceso_orden(comando,centros)
                print("coordenadas del centro",coor)
                control_brazo(coor)

            else:
                print("No se pudo grabar o procesar el audio. Intentando nuevamente...")

            # Salir del bucle principal después de procesar el flujo
            break

    # Asegúrate de liberar cualquier recurso restante si se interrumpe el flujo
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


