# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                                 config.py                                  ||
||                      PARÁMETROS DE CONFIGURACIÓN CENTRAL                   ||
||                                                                            ||
================================================================================
"""

# --- Configuración de Conexiones ---
PUERTO_COM = 'COM3'
TASA_BAUDIOS = 9600
URL_CAMARA = 1

# --- Claves de APIs Externas ---
CLAVE_API_OPENAI = '' ### KEY DE OPENAI API, EN CASO DE NECESITAR REALIZAR PRUEBAS SOLICITARLAS A LOS ADMINISTRADORES DEL PROYECTO

# --- Posiciones Predefinidas del Brazo ---
POSICION_HOME = [90, 140, 170, 10]
POSICION_A1 = (-180, 150, 0) # Depósito 1
POSICION_A2 = (180, 150, 0)  # Depósito 2

# --- Parámetros de Operación ---
ALTURA_SEGURA_Z = 90
ALTURA_PICKING_Z = -38

# --- Parámetros del Gripper (Pinza) ---
ANGULO_PINZA_ABIERTA = 80
ANGULO_PINZA_CERRADA = 0

# --- Parámetros de Calibración del Área de Trabajo ---
AREA_TRABAJO_ANCHO_MM = 148.0
AREA_TRABAJO_ALTO_MM = 78.0
ORIGEN_AREA_TRABAJO_X_MM = 0
ORIGEN_AREA_TRABAJO_Y_MM = 224.0

# --- Offsets de Servos (en grados) ---
OFFSET_SERVO_BASE = -21
OFFSET_SERVO_HOMBRO = -8.0
OFFSET_SERVO_CODO = -3.0
OFFSET_SERVO_PITCH = 0.0

# --- Inversión de Ejes ---
INVERTIR_EJE_X = True
INVERTIR_EJE_Y = True

# --- Offsets de Posición por Cuadrante (en mm) ---
OFFSET_Q1_CENTRO_X_MM = -53 # Este es el valor que ya tenías para el centro
OFFSET_Q1_CENTRO_Y_MM = 15
OFFSET_Q1_BORDE_X_MM = -44  # NUEVO: Ajusta este valor para el borde de las X+
OFFSET_Q1_BORDE_Y_MM = 2   # NUEVO: Probablemente el Y no cambie mucho
OFFSET_Q2_X_MM = -20
OFFSET_Q2_Y_MM = 2
OFFSET_Q3_X_MM = -10
OFFSET_Q3_Y_MM = 53
OFFSET_Q4_X_MM = -5
OFFSET_Q4_Y_MM = 51
OFFSET_PICKING_Z_MM = 0.0


# ==============================================================================
# ===         NUEVOS PARÁMETROS PARA APILADO DE PIEZAS                     ===
# ==============================================================================

# --- Altura de las Piezas (en mm) ---
ALTURA_PIEZA_MM = 30

# --- Coordenadas para las Bases de las Pilas (X, Y) ---
POSICION_APILADO_FORMA_CUBO = (18, 160)
POSICION_APILADO_FORMA_CILINDRO = (18, 160)

POSICION_APILADO_COLOR_NEGRO = (18, 160)
POSICION_APILADO_COLOR_AZUL = (18, 160)
POSICION_APILADO_COLOR_ROJO = (18, 160)