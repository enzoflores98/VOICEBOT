# -*- coding: utf-8 -*-
"""
================================================================================
||                                                                            ||
||                            sistema_audio.py                                ||
||                  MÓDULO DE PROCESAMIENTO DE VOZ PARA TESIS                 ||
||                                                                            ||
================================================================================
"""

import pyaudio
import openai
import os
import wave
import logging
import threading
import json

class SistemaAudio:
    def __init__(self, clave_api):
        if not clave_api:
            raise ValueError("La clave de la API de OpenAI no puede estar vacía.")
        
        logging.info("Inicializando el cliente de OpenAI para el sistema de audio.")
        self.client = openai.OpenAI(api_key=clave_api)
        
        self.FORMATO = pyaudio.paInt16
        self.CANALES = 1
        self.FRECUENCIA_MUESTREO = 44100
        self.TAMANO_BLOQUE = 1024
        self.NOMBRE_ARCHIVO_TEMP = "comando_voz_temp.wav"

        self.is_recording = False
        self.frames = []
        self.recording_thread = None

    def _bucle_grabacion(self):
        """Bucle que se ejecuta en un hilo para capturar audio."""
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMATO,
                        channels=self.CANALES,
                        rate=self.FRECUENCIA_MUESTREO,
                        input=True,
                        frames_per_buffer=self.TAMANO_BLOQUE)
        
        logging.info("Hilo de grabación iniciado. Capturando audio...")
        while self.is_recording:
            data = stream.read(self.TAMANO_BLOQUE)
            self.frames.append(data)
            
        logging.info("Hilo de grabación detenido.")
        stream.stop_stream()
        stream.close()
        p.terminate()

    def iniciar_grabacion(self):
        """Inicia la grabación de audio en un hilo de fondo."""
        if self.is_recording:
            logging.warning("Ya se está grabando.")
            return

        self.is_recording = True
        self.frames = []
        self.recording_thread = threading.Thread(target=self._bucle_grabacion, daemon=True)
        self.recording_thread.start()
        
    def detener_y_procesar_audio(self):
        """Detiene la grabación y procesa el audio capturado."""
        if not self.is_recording:
            logging.warning("No hay ninguna grabación en curso para detener.")
            return "{\"accion\": \"ERROR\", \"detalle\": \"No se estaba grabando\"}"

        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
            
        if not self.frames:
            logging.warning("No se capturó audio durante la grabación.")
            return "{\"accion\": \"ERROR\", \"detalle\": \"Grabacion vacia\"}"

        logging.info("Guardando audio capturado en archivo temporal...")
        with wave.open(self.NOMBRE_ARCHIVO_TEMP, 'wb') as wf:
            p = pyaudio.PyAudio()
            wf.setnchannels(self.CANALES)
            wf.setsampwidth(p.get_sample_size(self.FORMATO))
            wf.setframerate(self.FRECUENCIA_MUESTREO)
            wf.writeframes(b''.join(self.frames))
            p.terminate()

        try:
            texto_transcrito = self._transcribir_audio(self.NOMBRE_ARCHIVO_TEMP)
            if texto_transcrito:
                comando_final = self._interpretar_prompt_con_gpt(texto_transcrito)
                return comando_final
            else:
                return "{\"accion\": \"ERROR\", \"detalle\": \"Error en transcripcion\"}"
        finally:
            if os.path.exists(self.NOMBRE_ARCHIVO_TEMP):
                os.remove(self.NOMBRE_ARCHIVO_TEMP)

    def _transcribir_audio(self, nombre_archivo):
        logging.info(f"Enviando archivo '{nombre_archivo}' a la API de Whisper...")
        try:
            with open(nombre_archivo, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            logging.info(f"Texto transcrito recibido: '{transcription.text}'")
            return transcription.text
        except Exception as e:
            logging.error(f"Error al transcribir audio: {e}")
            return None

    def _interpretar_prompt_con_gpt(self, prompt):
        instrucciones = (
            "Tu tarea es analizar y clasificar la petición de un usuario para un robot. Tu respuesta debe estar en formato JSON.\n"
            "1. LIMPIEZA: Si pide limpiar o recoger todo, responde: {\"accion\": \"LIMPIAR\"}.\n"
            "2. CLASIFICACIÓN: Si pide clasificar por 'forma' o 'color', responde: {\"accion\": \"CLASIFICAR\", \"criterio\": \"FORMA\"} o {\"accion\": \"CLASIFICAR\", \"criterio\": \"COLOR\"}.\n"
            "3. APILADO: Si pide apilar por 'forma' o 'color', responde: {\"accion\": \"APILAR\", \"criterio\": \"FORMA\"} o {\"accion\": \"APILAR\", \"criterio\": \"COLOR\"}.\n"
            "4. SECUENCIA: Si da órdenes para mover una o más piezas específicas a depósitos, extrae cada movimiento como un diccionario JSON dentro de una lista. Cada diccionario debe tener las claves \"forma\" (CUBO o CILINDRO), \"color\" (en INGLÉS y MAYÚSCULAS) y \"deposito\" (1 o 2). Ejemplo: {\"accion\": \"SECUENCIA\", \"comandos\": [{\"forma\": \"CILINDRO\", \"color\": \"BLACK\", \"deposito\": 1}]}.\n"
            "5. CONFIRMACION: Si el usuario dice 'sí', 'procede', 'ok', 'dale', etc., responde: {\"accion\": \"CONFIRMAR\"}.\n"
            "6. NEGACION: Si el usuario dice 'no', 'cancela', 'para', etc., responde: {\"accion\": \"CANCELAR\"}.\n"
            "7. DESARMAR: Si el usuario pide desarmar, desmontar o devolver las pilas, responde: {\"accion\": \"DESARMAR\"}.\n"
            "Si no entiendes la petición, devuelve: {\"accion\": \"ERROR\"}."
        )
        
        mensajes = [{"role": "system", "content": instrucciones}, {"role": "user", "content": prompt}]
        
        logging.info("Enviando prompt a la API de GPT para interpretación de acción...")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes,
                max_tokens=250,
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            respuesta_str = response.choices[0].message.content
            logging.info(f"Respuesta JSON de GPT: {respuesta_str}")
            return respuesta_str

        except Exception as e:
            logging.error(f"Error al obtener respuesta de GPT: {e}")
            return "{\"accion\": \"ERROR\"}"