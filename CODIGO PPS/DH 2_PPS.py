from spatialmath import *
from spatialmath.base import *
import matplotlib.pyplot as plt
from sympy import pi, latex, simplify, trigsimp, cos, sin
import numpy as np
import sympy as sp
from scipy.optimize import least_squares

class SE3(SE3):
    def symbolReplace(self,symbol_values):
        aux = np.eye(self.A.shape[0])
        for i in range(self.A.shape[0]):
            for j in range(self.A.shape[1]):
                try:
                    aux[i,j] = self.A[i,j].subs(symbol_values).evalf()
                except:
                    pass
        return aux

q1, q2, q3, q4 = sp.symbols('Q1 Q2 Q3 Q4')

# TABLA DH 
#    theta       d   a   alpha
# 1   q1        l1z   l1x    90
# 2   q2+90      0    l2     0
# 3   q3         0    l3     0
# 4   q4         0    l4     0

l1z = 60.3
l1x = 8.35
l2 = 120
l3 = 122.86
l4 = 130
alfa = np.pi/2


# Definimos variables articulares
#q1 = 0
#q2 = 0
#q3 = 0
#q4 = 0

#S0 = SE3()
A01 = SE3.Rz(q1)*SE3.Tz(l1z)*SE3.Tx(l1x)*SE3.Rx(alfa)
#S1 = S0 @ A01
A12 = SE3.Rz(q2+alfa)*SE3.Tx(l2)
#S2 = S1 @ A12
A23 = SE3.Rz(q3)*SE3.Tx(l3)
#S3 = S2 @ A23
A34 = SE3.Rz(q4)*SE3.Tx(l4)
#S4 = S3 @ A34
'''
trplot( S0.A, frame='S0')
trplot( S1.A, frame='S1', color  = 'red')
trplot( S2.A, frame='S2', color  = 'green')
trplot( S3.A, frame='S3', color  = 'black')
trplot( S4.A, frame='S4', color  = 'blue')
'''

#Calculo de matriz homogenea:
T= A01 * A12 * A23
T1 = A01 * A12 * A23 * A34 

# Asignamos P como filas 0 a 3 (sin incluir) y columna 3 del tensor T
P = T1.A[:3,3]

# Aplicamos simplificacion algebraica y numerica
P = [i.simplify().nsimplify(tolerance = 1e-5).simplify() for i in P]

# Desempaquetamos P
px,py,pz = P

np.set_printoptions(suppress=True)

print(px)
print(py)
print(pz)

simplified_T1 = sp.Matrix(T1.A)  # Convertimos a matriz simbólica de SymPy
simplified_T1 = simplified_T1.applyfunc(lambda x: sp.nsimplify(sp.simplify(x), tolerance=1e-5))

print("Matriz T1 simplificada:")
print(simplified_T1[:3,3])

'''
a,b,c,d = 0,0,0,0
px1_eval = px.subs([('Q1',0.7854),('Q2',-1.7042),('Q3',1.2687),('Q4',-2.4493)])
py1_eval = py.subs([('Q1',0.7854),('Q2',-1.7042),('Q3',1.2687),('Q4',-2.4493)])
pz1_eval = pz.subs([('Q1',0.7854),('Q2',-1.7042),('Q3',1.2687),('Q4',-2.4493)])

print('Posicion en X: ',float(px1_eval))
print('Posicion en Y: ',float(py1_eval))
print('Posicion en Z: ',float(pz1_eval))

#PRUEBAS CINEMATICAS
def sistema(vars, Px, Py, Pz, A):
    Q1, Q2, Q3, Q5 = vars

    f1 = Px - ((-12000*np.sin(Q2) - 12286*np.sin(Q2 + Q3) - 13000*np.sin(Q2 + Q3 + Q5) + 835) * np.cos(Q1) / 100)
    f2 = Py - ((-12000*np.sin(Q2) - 12286*np.sin(Q2 + Q3) - 13000*np.sin(Q2 + Q3 + Q5) + 835) * np.sin(Q1) / 100)
    f3 = Pz - (120*np.cos(Q2) + 6143*np.cos(Q2 + Q3)/50 + 130*np.cos(Q2 + Q3 + Q5) + 603/10)
    f4 = A - (Q5 - Q2 + Q3)

    return [f1, f2, f3, f4]


def clamp(x, a, b):
    return max(a, min(x, b))

while True:
    # Pedir datos al usuario de Px, Py y Pz
    stop = input("¿Desea continuar? (s/n): ")
    if stop.lower() == 'n':
        break
    Px = float(input("Ingrese el valor de Px: "))
    Py = float(input("Ingrese el valor de Py: "))
    Pz = float(input("Ingrese el valor de Pz: "))
    #Q1= calculo_q1(Px, Py)  # Llamar a la función para obtener Q1
    a5=-np.pi/6 #Este angulo será la inclinacion del efector respecto a la horizontal
    initial_guess = [np.pi/2,0,0,0]
    lower_bounds = [    0.0, -np.pi, -np.pi, -np.pi]  # Q1 limitado entre 0 y pi/2
    upper_bounds = [ np.pi,  np.pi,  np.pi,  np.pi]
    # Resolvemos el sistema de ecuaciones
    solution = least_squares(
    sistema,
    x0=initial_guess,
    bounds=(lower_bounds, upper_bounds),
    args=(Px, Py, Pz, a5),
    method='trf',      # Trust Region Reflective (permite límites)
    xtol=1e-10, ftol=1e-10, gtol=1e-10  # tolerancias ajustadas para mayor precisión)
    )
    Q1, Q2, Q3, Q5 = solution.x
    solution_radDH = [Q1,Q2,Q3,Q5]
    solution_degDH = np.degrees(solution_radDH)  # Convertir a grados
    
    print("solucion radianes: ",solution_radDH)
    print("solucion grados: ",solution_degDH)
    a, b, c, d = solution_radDH
    px1_eval = px.subs([('Q1',a),('Q2',b),('Q3',c),('Q4',d)])
    py1_eval = py.subs([('Q1',a),('Q2',b),('Q3',c),('Q4',d)])
    pz1_eval = pz.subs([('Q1',a),('Q2',b),('Q3',c),('Q4',d)])
    print('Posicion en X: ',float(px1_eval))
    print('Posicion en Y: ',float(py1_eval))
    print('Posicion en Z: ',float(pz1_eval))
  
'''