# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                                  main.py                                   ||
||                      NÚCLEO PRINCIPAL (CON GUI)                            ||
||                                                                            ||
================================================================================
"""

import logging
import config
from controlador_brazo import ControladorBrazo
from sistema_vision import SistemaVision
from sistema_audio import SistemaAudio
from sistema_voz import SistemaVoz
from logica_tesis import LogicaTesis
from interfaz_grafica import InterfazGrafica

def configurar_logging():
    """Configura el sistema de logging para mostrar mensajes informativos."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
    )

def main():
    """
    Función principal que orquesta la inicialización de los módulos
    y lanza la interfaz gráfica.
    """
    configurar_logging()
    logging.info("==================================================")
    logging.info("==   INICIANDO SISTEMA DE CONTROL               ==")
    logging.info("==================================================")

    controlador = None
    vision = None
    
    try:
        controlador = ControladorBrazo(
            puerto=config.PUERTO_COM,
            baud_rate=config.TASA_BAUDIOS
        )
        vision = SistemaVision(
            url_camara=config.URL_CAMARA
        )
        audio = SistemaAudio(
            clave_api=config.CLAVE_API_OPENAI
        )
        # Se inicializa el sistema de voz offline
        voz = SistemaVoz()
        
        # Se le pasa el sistema de voz a la lógica principal
        logica_principal = LogicaTesis(controlador, vision, audio, voz)

        # Mensaje de bienvenida inicial
        voz.decir("....Sistema Voice bot inicializado. Esperando instrucciones.")

    except Exception as e:
        logging.error(f"Error fatal durante la inicialización de los módulos de backend: {e}")
        logging.error("El programa no puede continuar. Verifica las conexiones y la configuración.")
        if controlador:
            controlador.cerrar_conexion()
        if vision:
            vision.liberar_camara()
        return

    try:
        logging.info("Lanzando la Interfaz Gráfica de Usuario (GUI)...")
        
        app = InterfazGrafica(
            controlador=controlador,
            sistema_vision=vision,
            sistema_audio=audio,
            logica_tesis=logica_principal
        )
        
        app.mainloop()

    except Exception as e:
        logging.error(f"Ha ocurrido un error fatal en la aplicación de la GUI: {e}")
    finally:
        logging.info("La GUI se ha cerrado. Iniciando secuencia de apagado...")
        controlador.cerrar_conexion()
        vision.liberar_camara()
        logging.info("Sistema apagado correctamente. ¡Adiós!")


if __name__ == "__main__":
    main()