# sistema_voz.py
import pyttsx3
import logging

class SistemaVoz:
    def __init__(self):
        """
        Guarda la configuración de la voz a utilizar.
        """
        # --- CONFIGURACIÓN DE VOZ ---
        # Pega aquí el ID de la voz masculina que elegiste.
    
        self.id_de_voz = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-ES_HELENA_11.0"
        
        self.rate = 160  # Velocidad de la voz
        self.volume = 1.0  # Volumen (0.0 a 1.0)
        logging.info("Sistema de voz configurado. Se creará un motor nuevo en cada llamada.")

    def decir(self, texto):
        """
        Crea un motor, dice el texto y lo destruye.
        Este es el método más robusto para múltiples llamadas.
        """
        try:
            # 1. Crear un motor de voz nuevo
            engine = pyttsx3.init()

            # 2. Configurar las propiedades
            engine.setProperty('voice', self.id_de_voz)
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # ==================================================================
           
            # Se agregaron espacios para crear un "buffer" de silencio y evitar cortes.
            mensaje_con_buffer = f"      {texto}      "
            
            # ==================================================================
            
            # 3. Decir el texto modificado
            logging.info(f"Generando voz para el texto: '{texto}'")
            engine.say(mensaje_con_buffer)
            engine.runAndWait() # Procesa la cola de comandos y espera
            
            # 4. Detener el motor
            engine.stop()

        except Exception as e:
            logging.error(f"Error en el sistema de voz (pyttsx3): {e}")

        except Exception as e:
            logging.error(f"Error en el sistema de voz (pyttsx3): {e}")