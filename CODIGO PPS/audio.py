import pyaudio
import openai
import os
import wave
import time
import keyboard  # Importar la biblioteca keyboard
from configuracion import CLAVE_API_OPENAI

# Configura tu clave API de OpenAI

client = openai.OpenAI(api_key=CLAVE_API_OPENAI)

def grabar_audio(duracion=5, nombre_archivo="audio_temp.wav"):
    # Configuración de PyAudio
    formato = pyaudio.paInt16  # Formato de las muestras de audio
    canales = 1  # Mono
    frecuencia_muestreo = 44100  # Frecuencia de muestreo
    tamaño_bloque = 1024  # Tamaño del bloque de audio

    p = pyaudio.PyAudio()

    # Abrir el flujo de audio
    stream = p.open(format=formato,
                    channels=canales,
                    rate=frecuencia_muestreo,
                    input=True,
                    frames_per_buffer=tamaño_bloque)

    print("Grabando...")

    # Leer datos del micrófono
    frames = []
    for _ in range(0, int(frecuencia_muestreo / tamaño_bloque * duracion)):
        data = stream.read(tamaño_bloque)
        frames.append(data)

    print("Grabación finalizada.")

    # Detener y cerrar el flujo de audio
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Guardar la grabación en un archivo WAV
    wf = wave.open(nombre_archivo, 'wb')
    wf.setnchannels(canales)
    wf.setsampwidth(p.get_sample_size(formato))
    wf.setframerate(frecuencia_muestreo)
    wf.writeframes(b''.join(frames))
    wf.close()

    return nombre_archivo


def transcribir_audio(nombre_archivo):
    """
    Transcribe un archivo de audio utilizando OpenAI Whisper.

    Args:
        nombre_archivo (str): Ruta al archivo de audio.

    Returns:
        str: Texto transcrito del audio.
    """
    try:
        # Abre el archivo de audio en modo binario
        with open(nombre_archivo, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text
    except Exception as e:
        # Manejo de errores
        print(f"Error al transcribir el audio: {e}")
        return None


def obtener_respuesta(prompt):
    instrucciones = (
        "Debes responder con exactamente tres cadenas de texto. La primera sera una forma, la segunda sera un color y la tercera es un numero"
        "El usuario mencionará o insinuará una forma y un color explicita o implicitamente, ademas de un numero de depósito. Tu tarea será interpretar y responder"
        "Tu respuesta tendrá el formato 'FORMA' 'COLOR' 'NUMERO' (el número debera responderse con un caracter numerico)"
        "Las formas disponibles como respuesta son: 'CILINDRO' y 'CUBO'"
        "Los colores disponibles como respuesta son: 'ROJO' y 'NEGRO'" 
        "Tus respuesta irá directo a los datos de entrada para mover un robot el cual tomará la forma, color y numero como instrucción. Por este motivo es importante que solo respondas con el formato indicado"
        "Como unico caso excepcional en donde responderas algo que sea diferente, es cuando las instrucciones no tengan sentido o no brinden la informacion suficiente. En este caso deberas responder 'Instruccion no reconocida'"
        "No agregues ningún texto ni caracter adicional."
        "Ten en cuenta que la entrada puede no ser del todo explicita y en ese caso deberás entender que es lo que el usuario quiere hacer"
    )

    mensajes = [
        {"role": "system", "content": instrucciones},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=mensajes,
        max_tokens=20,
        temperature=0
    )

    respuesta = response.choices[0].message.content.strip()
    return respuesta


def obtener_comando_por_voz():
    nombre_archivo = grabar_audio(duracion=5)
    texto_transcrito = transcribir_audio(nombre_archivo)
    print(f"Texto transcrito: {texto_transcrito}")
    respuesta =  obtener_respuesta(texto_transcrito)
    print(respuesta)
    os.remove(nombre_archivo)
    
    return respuesta


def esperar_y_grabar():
    print("Presiona la barra espaciadora para comenzar a grabar...")
    while True:
        if keyboard.is_pressed('space'):
            print("Barra espaciadora presionada. Grabando...")
            try:
                return obtener_comando_por_voz()
            except Exception as e:
                print(f"Error al grabar o procesar el audio: {e}")
                return None
        time.sleep(0.1)  # Pequeña pausa para evitar sobrecargar la CPU                  

#esperar_y_grabar()
