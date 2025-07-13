import serial
import time
import numpy as np
from scipy.optimize import least_squares


# Definición del sistema de ecuaciones
def sistema(vars, Px, Py, Pz, A):
    Q1, Q2, Q3, Q5 = vars

    f1 = Px - ((-12000*np.sin(Q2) - 12286*np.sin(Q2 + Q3) - 13000*np.sin(Q2 + Q3 + Q5) + 835) * np.cos(Q1) / 100)
    f2 = Py - ((-12000*np.sin(Q2) - 12286*np.sin(Q2 + Q3) - 13000*np.sin(Q2 + Q3 + Q5) + 835) * np.sin(Q1) / 100)
    f3 = Pz - (120*np.cos(Q2) + 6143*np.cos(Q2 + Q3)/50 + 130*np.cos(Q2 + Q3 + Q5) + 603/10)
    f4 = A - (Q5 - Q2 + Q3)

    return [f1, f2, f3, f4]

def clamp(x, a, b):
    return max(a, min(x, b))

def toservo(solution):
    solution_grados = np.degrees(solution) # Convierto solucion a grados
    Q1= clamp(solution_grados[0],0,180)
    Q2= clamp(solution_grados[1]+85,0,180) #Hago las equivalencias entre el DH y los grados de los servos reales
    Q3= clamp(90-solution_grados[2],0,180) #El clamp es para evitar que los valores resulten en negativos o mayores a 180
    Q5= clamp(solution_grados[3]+90,0,180)
    # Recordar que Q4 y Q6 son fijos
    solution_grados_servo = [Q1,Q2,Q3,Q5]
    return solution_grados_servo

def transformacion_coordenadas(cx,cy):
    #Esta funcion transforma los centros de los objetos a coordenadas del robot
    p_xy=[0,0]
    o_xy=[180,40] #esquina del primer aruco
    alfa=0.75 #angulo de inclinacion del eje de los aruco respecto al del robot en radianes (40° de prueba)
    p_xy[0]=np.cos(alfa)*cx-np.sin(alfa)*cy+o_xy[0]
    p_xy[1]=np.sin(alfa)*cx+np.cos(alfa)*cy+o_xy[1]

    return p_xy

def to_arduino(Q1,Q2,Q3,Q4,Q5,Q6,depo):

    print(depo)
    #Se envian los datos al arduino para mover el robot
    arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)  # Cambia COM3 según tu puerto


    time.sleep(2)  # Esperar a que el Arduino se inicie
    data= f"{170},{85},{166},{125},{45},{80}\n" #Posicion INICIAL
    arduino.write(data.encode())
    time.sleep(3)  # Esperar

    #data= f"{122},{81},{168},{125},{55},{80}\n" #Posicion NEUTRA
    #arduino.write(data.encode())
    #time.sleep(3)  # Esperar a que el Arduino se inicie

    data= f"{Q1},{81},{168},{125},{55},{80}\n" #Posicion NEUTRA 2
    arduino.write(data.encode())
    time.sleep(2)  # Esperar a que el Arduino se inicie

    data = f"{Q1},{Q2},{Q3},{Q4},{Q5},{Q6}\n" #Posicion del objeto
    arduino.write(data.encode())
    time.sleep(2)

    data = f"{Q1},{Q2},{Q3},{Q4},{Q5},{15}\n" #Tomar objeto
    arduino.write(data.encode())
    time.sleep(2)

    print(f"Datos enviados: {data}")

    data= f"{Q1},{81},{168},{125},{55},{15}\n" #Posicion NEUTRA
    arduino.write(data.encode())
    time.sleep(1)  # Esperar a que el Arduino se inicie

    data= f"{90},{90},{177},{125},{45},{15}\n" #Posicion NEUTRA
    arduino.write(data.encode())
    time.sleep(2)  # Esperar a que el Arduino se inicie

    data= f"{60},{90},{177},{125},{45},{15}\n" #Posicion NEUTRA
    arduino.write(data.encode())
    time.sleep(2)  # Esperar a que el Arduino se inicie
    #DEPO 1: 56 53 139 125 45 45

    if depo == '1':
        data= f"{56},{53},{139},{125},{45},{15}\n" #Posicion PREVIA A DEPO 1
        arduino.write(data.encode())
        time.sleep(2)

        #data= f"{56},{53},{139},{125},{45},{10}\n" #Posicion DEPO 1
        #arduino.write(data.encode())
        #time.sleep(2)

        data= f"{56},{53},{139},{125},{45},{60}\n" #Soltar objeto
        arduino.write(data.encode())
        time.sleep(2)

    elif depo == '2':
        data= f"{26},{49},{131},{125},{45},{15}\n" #Posicion PREVIA A DEPO 2 26.0,49.0,131.0,125,45.0,45
        arduino.write(data.encode())
        time.sleep(1)

        data= f"{26},{49},{131},{125},{45},{60}\n" #Posicion PREVIA A DEPO 2
        arduino.write(data.encode())
        time.sleep(1)
        #data= f"{27},{49},{131},{125},{40},{10}\n" #Posicion DEPO 2
        #arduino.write(data.encode())
        #time.sleep(2)
    else:
        print("Deposito no reconocido")

    data= f"{60},{90},{177},{125},{45},{45}\n" #Posicion NEUTRA
    arduino.write(data.encode())
    time.sleep(1)  # Esperar a que el Arduino se inicie


    #DEPO 1: 56 53 139 125 45 45
    #DEPO 1: 51,43,138,125,45,45
    #DEPO 1 PREVIO: 51, 49, 127, 125, 45, 45

    #DEPO 2: 25, 35, 122, 125, 40, 45
    #DEOP 2 PREVIO: 25, 37, 105, 125, 35, 45

    # Agregar un pequeño retraso
    time.sleep(2)
    data= f"{170},{50},{135},{125},{45},{45}\n"
    arduino.write(data.encode())
    return True

def control_brazo(centro):
    
    depo=centro[2] #Se asigna el deposito correspondiente a la variable depo

    #Transformacion de la deteccion a coordenadas del robot
    factorx=0.15 #Pixeles a CM
    factory=0.2828 #Pixeles a CM
    cx=centro[0]*factorx
    cy=centro[1]*factory
    punto=transformacion_coordenadas(cx,cy)

    #Resolucion de la cinematica 
    Px=punto[0]
    Py=punto[1]
    Pz=75 #Se propone un valor de Z
    print("Punto al que se dirige: ")
    print("Px: ",Px)
    print("Py: ",Py)
    print("Pz: ",Pz)

    A=-np.pi/6 #Este angulo será la inclinacion del efector respecto a la horizontal
    initial_guess = [np.pi/2,0,0,0]
    lower_bounds = [    0.0, -np.pi, -np.pi, -np.pi]  # Q1 limitado entre 0 y pi/2
    upper_bounds = [ np.pi,  np.pi,  np.pi,  np.pi]
    solution = least_squares(
    sistema,
    x0=initial_guess,
    bounds=(lower_bounds, upper_bounds),
    args=(Px, Py, Pz, A),
    method='trf',      # Trust Region Reflective (permite límites)
    xtol=1e-10, ftol=1e-10, gtol=1e-10  # tolerancias ajustadas para mayor precisión)
    )
    Q1, Q2, Q3, Q5 = solution.x

    solution_radDH = [Q1,Q2,Q3,Q5]
    solution_servo = toservo(solution_radDH)

    Q1=np.round(solution_servo[0],2)
    Q2=np.round(solution_servo[1],2)
    Q3=np.round(solution_servo[2],2)
    QF = 125 # VALOR FIJO DEL SERVO QUE NO SE MUEVE
    Q5=np.round(solution_servo[3],2)
    Q6 = 80
    #Se envian los datos al arduino
    to_arduino(Q1,Q2,Q3,QF,Q5,Q6,depo)
    #time.sleep(15)
    #if flag:
    #    to_arduino(180,35,125,Q4,Q5,Q6)
    return True
'''
# Bucle para probar script aislado

# Configurar la comunicación serial con el Arduino
arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)  # Cambia COM3 según tu puerto
time.sleep(2)  # Esperar a que el Arduino se inicie

# Valores iniciales coordenadas servo a DH
zero_point = [180, 10, 85, 125, 125, 45]


# Bucle principal
try:
    while True:
        # Pedir los valores de Px, Py, y Pz
        Px = float(input("Ingrese el valor de Px: "))
        Py = float(input("Ingrese el valor de Py: "))
        Pz = float(input("Ingrese el valor de Pz: "))

        # Valores iniciales para las incógnitas
        initial_guess = [0, 0, 0]

        # Resolver el sistema de ecuaciones
        solution = fsolve(equations, initial_guess, args=(Px, Py, Pz))
        solution_grados = np.degrees(solution)

        print(f"Solución en grados: {solution_grados}")

        solucion_real = toservo(solution_grados)
        print(f"Posición en el robot (valores ajustados): {solucion_real}")

        # Permitir ajustar manualmente Q1, Q2 y Q3 si es necesario
        Q1 = float(input("Ingrese el valor de Q1 (grados ajustados): "))
        Q2 = float(input("Ingrese el valor de Q2 (grados ajustados): "))
        Q3 = float(input("Ingrese el valor de Q3 (grados ajustados): "))
        Q5 = float(input("Ingrese el valor de Q5 (grados ajustados): "))
        Q4 = 125  # Puedes ajustar este valor según sea necesario
        #Q5 = 55
        Q6 = 45

        # Enviar datos al Arduino
        data = f"{Q1},{Q2},{Q3},{Q4},{Q5},{Q6}\n"
        arduino.write(data.encode())
        print(f"Datos enviados: {data}")

        # Agregar un pequeño retraso antes de repetir
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nPrograma terminado por el usuario.")
    arduino.close()
'''