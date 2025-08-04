# logica_tesis.py (Versión con pausas de seguridad para ascenso y depósito)
import logging
import json
import time
import config

class LogicaTesis:
    def __init__(self, controlador, sistema_vision, sistema_audio, sistema_voz):
        self.controlador = controlador
        self.sistema_vision = sistema_vision
        self.sistema_audio = sistema_audio
        self.sistema_voz = sistema_voz
        
        self.ultimos_objetos_detectados = []
        self.imagen_resultado_analisis = None
        self.estado_pilas = {}
        self.criterio_apilado_actual = None

        self.traductor_natural = {
            "CUBO": "un cubo", "CILINDRO": "un cilindro",
            "BLUE": "azul", "RED": "rojo", "BLACK": "negro"
        }

    def analizar_escena_y_almacenar(self):
        """
        Analiza la escena de forma silenciosa y devuelve una descripción textual.
        """
        logging.info("Iniciando análisis de la escena...")
        frame = self.sistema_vision.obtener_frame_actual()
        if frame is None:
            self.sistema_voz.decir("Error de cámara. No fue posible analizar la escena.")
            return False, "Error de cámara"
            
        objetos, imagen_analizada = self.sistema_vision.analizar_snapshot(frame)
        self.ultimos_objetos_detectados = objetos
        self.imagen_resultado_analisis = imagen_analizada
        
        if not self.ultimos_objetos_detectados:
            descripcion_final = "Análisis completado. El área de trabajo se encuentra despejada."
        else:
            descripcion = "Análisis completado. Se han detectado los siguientes objetos: "
            descripciones = []
            for obj in self.ultimos_objetos_detectados:
                forma = self.traductor_natural.get(obj.get('forma'), 'forma desconocida')
                color = self.traductor_natural.get(obj.get('color'), 'color desconocido')
                descripciones.append(f"{forma} {color}")
            if len(descripciones) == 1:
                descripcion += descripciones[0]
            else:
                descripcion += ", ".join(descripciones[:-1]) + " y " + descripciones[-1]
            descripcion_final = descripcion + "."
        
        logging.info(descripcion_final)
        return True, descripcion_final

    def procesar_y_ejecutar_comando_voz(self):
        logging.info("Iniciando ciclo completo de comando de voz...")
        self.sistema_voz.decir("Un momento, analizaré la instrucción.")
        resultado_audio_str = self.sistema_audio.detener_y_procesar_audio()
        
        try:
            data = json.loads(resultado_audio_str)
            accion = data.get("accion")

            if accion == "DESARMAR":
                self.ejecutar_desarmado_con_retorno()
                return

            if self.estado_pilas and accion not in ["APILAR", "CANCELAR", "CONFIRMAR"]:
                self.sistema_voz.decir("Se han detectado pilas existentes. Procediendo a desarmarlas antes de continuar.")
                self._desarmar_y_limpiar_pilas_a_deposito()
                time.sleep(1)

            if accion in ["LIMPIAR", "CLASIFICAR", "APILAR", "SECUENCIA"]:
                exito, descripcion = self.analizar_escena_y_almacenar()
                if not exito: return
                
                if not self.ultimos_objetos_detectados and accion != "SECUENCIA":
                    self.sistema_voz.decir("El área está despejada, no hay objetos para ejecutar la tarea solicitada.")
                    return
                
                mensaje_confirmacion = ""
                
                if accion == "LIMPIAR":
                    mensaje_confirmacion = "Se iniciará el protocolo de limpieza."
                    self.sistema_voz.decir(f"{descripcion} {mensaje_confirmacion}")
                    self.ejecutar_limpieza()
                elif accion == "CLASIFICAR":
                    criterio = data.get("criterio", "FORMA")
                    mensaje_confirmacion = f"Se procederá a clasificar los objetos por {criterio.lower()}."
                    self.sistema_voz.decir(f"{descripcion} {mensaje_confirmacion}")
                    self.ejecutar_clasificacion(criterio)
                elif accion == "APILAR":
                    criterio = data.get("criterio", "FORMA")
                    mensaje_confirmacion = f"Iniciando el protocolo de apilado por {criterio.lower()}."
                    self.sistema_voz.decir(f"{descripcion} {mensaje_confirmacion}")
                    self.ejecutar_apilado(criterio)
                elif accion == "SECUENCIA":
                    comandos = data.get("comandos", [])
                    if comandos:
                        mensaje_confirmacion = "Se iniciará la secuencia de movimientos solicitada."
                        self.sistema_voz.decir(f"{descripcion} {mensaje_confirmacion}")
                        self.ejecutar_secuencia_de_comandos(comandos)

            elif accion not in ["CONFIRMAR", "CANCELAR"]:
                self.sistema_voz.decir("La instrucción no pudo ser interpretada.")

        except Exception as e:
            logging.error(f"Error al procesar la acción de voz: {e}")
            self.sistema_voz.decir("Ha ocurrido un error al procesar el comando. Por favor, intente nuevamente.")

    def ejecutar_limpieza(self):
        comandos_generados = [{"forma": obj.get("forma"), "color": obj.get("color"), "deposito": 1} for obj in self.ultimos_objetos_detectados]
        self.ejecutar_secuencia_de_comandos(comandos_generados)

    def ejecutar_clasificacion(self, criterio="FORMA"):
        comandos_generados = []
        if criterio == "FORMA":
            for obj in self.ultimos_objetos_detectados:
                destino = 1 if obj.get("forma") == "CUBO" else 2
                comandos_generados.append({"forma": obj.get("forma"), "color": obj.get("color"), "deposito": destino})
        
        elif criterio == "COLOR":
            colores_detectados = set(obj.get('color') for obj in self.ultimos_objetos_detectados)
            num_colores = len(colores_detectados)
            if num_colores > 2:
                mensaje = f"Se han detectado {num_colores} colores distintos y solo hay dos depósitos disponibles. Por favor, retire un color y reintente la operación."
                self.sistema_voz.decir(mensaje)
                return
            colores_lista = list(colores_detectados)
            color_a_deposito = {}
            if num_colores >= 1: color_a_deposito[colores_lista[0]] = 1
            if num_colores == 2: color_a_deposito[colores_lista[1]] = 2
            for obj in self.ultimos_objetos_detectados:
                destino = color_a_deposito.get(obj.get("color"))
                comandos_generados.append({"forma": obj.get("forma"), "color": obj.get("color"), "deposito": destino})

        if comandos_generados:
            self.ejecutar_secuencia_de_comandos(comandos_generados)

    def ejecutar_apilado(self, criterio="FORMA"):
        self.estado_pilas = {}
        self.criterio_apilado_actual = criterio
        objetos_a_apilar = list(self.ultimos_objetos_detectados)
        for obj in objetos_a_apilar:
            self._ejecutar_un_apilado(obj, criterio)
        self.sistema_voz.decir("Tarea de apilado completada.")

    def ejecutar_secuencia_de_comandos(self, lista_comandos):
        objetos_disponibles = list(self.ultimos_objetos_detectados)
        for comando in lista_comandos:
            self._ejecutar_un_movimiento(comando, objetos_disponibles)
        self.sistema_voz.decir("Secuencia finalizada. A la espera de nuevas instrucciones.")
    
    def _ejecutar_un_movimiento(self, comando, objetos_disponibles):
        forma_buscada = comando.get("forma")
        color_buscado = comando.get("color")
        deposito_buscado = comando.get("deposito")
        objeto_encontrado = next((obj for obj in objetos_disponibles if obj.get('forma') == forma_buscada and obj.get('color') == color_buscado), None)
        if objeto_encontrado:
            objetos_disponibles.remove(objeto_encontrado)
            self._realizar_pick_and_place(
                info_objeto=objeto_encontrado, 
                coord_origen=objeto_encontrado['coord_reales'], 
                destino=deposito_buscado, 
                tipo_destino='deposito'
            )
        else:
            forma = self.traductor_natural.get(forma_buscada, forma_buscada)
            color = self.traductor_natural.get(color_buscado, color_buscado)
            self.sistema_voz.decir(f"Advertencia: No se ha encontrado {forma} {color} en el área de trabajo.")

    def _ejecutar_un_apilado(self, objeto, criterio):
        clave_pila, pos_x_pila, pos_y_pila = self._obtener_base_pila(criterio, objeto)
        px_corregido, py_corregido = self._aplicar_offsets_por_cuadrante(pos_x_pila, pos_y_pila)
        pila_actual = self.estado_pilas.get(clave_pila, [])
        altura_colocacion = config.ALTURA_PICKING_Z + (len(pila_actual) * config.ALTURA_PIEZA_MM)
        destino_final = (px_corregido, py_corregido, altura_colocacion)
        self._realizar_pick_and_place(
            info_objeto=objeto, 
            coord_origen=objeto['coord_reales'], 
            destino=destino_final, 
            tipo_destino='apilado'
        )
        pila_actual.append(objeto)
        self.estado_pilas[clave_pila] = pila_actual
        logging.info(f"Pieza añadida a '{clave_pila}'. La pila ahora tiene {len(pila_actual)} piezas.")

    def _desarmar_y_limpiar_pilas_a_deposito(self):
        self.sistema_voz.decir("Despejando el área de trabajo...")
        claves_pilas = list(self.estado_pilas.keys())
        for clave in claves_pilas:
            pila = self.estado_pilas[clave]
            while pila:
                pieza_a_mover = pila.pop()
                altura_recogida_z = config.ALTURA_PICKING_Z + (len(pila) * config.ALTURA_PIEZA_MM)
                _, pos_x_pila, pos_y_pila = self._obtener_base_pila(self.criterio_apilado_actual, clave)
                coord_origen_corregida = self._aplicar_offsets_por_cuadrante(pos_x_pila, pos_y_pila)
                self._realizar_pick_and_place(
                    info_objeto=pieza_a_mover, 
                    coord_origen=coord_origen_corregida, 
                    destino=1, 
                    pz_origen=altura_recogida_z, 
                    tipo_destino='deposito'
                )
        self.estado_pilas = {}
        self.criterio_apilado_actual = None
        self.sistema_voz.decir("Todas las pilas han sido desarmadas.")

    def ejecutar_desarmado_con_retorno(self):
        if not self.estado_pilas:
            self.sistema_voz.decir("No hay ninguna pila para desarmar.")
            return
        self.sistema_voz.decir("Confirmado. Desarmando pilas y devolviendo las piezas a su origen.")
        claves_pilas = list(self.estado_pilas.keys())
        for clave in claves_pilas:
            pila = self.estado_pilas[clave]
            while pila:
                pieza_a_mover = pila.pop()
                altura_recogida_z = config.ALTURA_PICKING_Z + (len(pila) * config.ALTURA_PIEZA_MM)
                _, pos_x_pila, pos_y_pila = self._obtener_base_pila(self.criterio_apilado_actual, pieza_a_mover)
                coord_origen_corregida = self._aplicar_offsets_por_cuadrante(pos_x_pila, pos_y_pila)
                coord_destino_final = pieza_a_mover['coord_reales']
                self._realizar_pick_and_place(
                    info_objeto=pieza_a_mover,
                    coord_origen=coord_origen_corregida,
                    destino=coord_destino_final,
                    pz_origen=altura_recogida_z,
                    tipo_destino='retorno'
                )
        self.estado_pilas = {}
        self.criterio_apilado_actual = None
        self.sistema_voz.decir("He devuelto todas las piezas a su lugar original.")
    
    def _obtener_base_pila(self, criterio, objeto_o_clave):
        clave_pila = ""
        if isinstance(objeto_o_clave, dict):
            clave_pila = objeto_o_clave.get("forma") if criterio == "FORMA" else objeto_o_clave.get("color")
        else:
            clave_pila = objeto_o_clave
        if criterio == "FORMA":
            pos_base = config.POSICION_APILADO_FORMA_CUBO if clave_pila == "CUBO" else config.POSICION_APILADO_FORMA_CILINDRO
            return clave_pila, pos_base[0], pos_base[1]
        else: 
            if clave_pila == "BLACK": pos_base = config.POSICION_APILADO_COLOR_NEGRO
            elif clave_pila == "BLUE": pos_base = config.POSICION_APILADO_COLOR_AZUL
            else: pos_base = config.POSICION_APILADO_COLOR_ROJO
            return clave_pila, pos_base[0], pos_base[1]

    def _realizar_pick_and_place(self, info_objeto, coord_origen, destino, pz_origen=None, tipo_destino='deposito'):
        forma_natural = self.traductor_natural.get(info_objeto.get("forma"), "el objeto")
        color_natural = self.traductor_natural.get(info_objeto.get("color"), "")
        self.sistema_voz.decir(f"Retiraré {forma_natural} {color_natural}.")
        if pz_origen is None:
            px_pick, py_pick = self._aplicar_offsets_por_cuadrante(coord_origen[0], coord_origen[1])
            pz_pick = config.ALTURA_PICKING_Z
        else:
            px_pick, py_pick = coord_origen
            pz_pick = pz_origen
        
        self.controlador.abrir_pinza()
        time.sleep(1)
        self.controlador.mover_a_coordenadas(px_pick, py_pick, pz=config.ALTURA_SEGURA_Z)
        self.controlador.mover_a_coordenadas(px_pick, py_pick, pz=pz_pick)
        time.sleep(2.5)
        self.controlador.cerrar_pinza()
        time.sleep(1)
        
        logging.info("Elevando pieza a altura segura antes de mover.")
        self.controlador.mover_a_coordenadas(px_pick, py_pick, pz=config.ALTURA_SEGURA_Z)
        
        # --- PRIMERA CORRECCIÓN: Pausa para estabilización después del ascenso. ---
        time.sleep(1)

        px_place, py_place, pz_place = self._obtener_coords_destino_final(destino, tipo_destino)
        if px_place is not None:
            self.controlador.mover_a_coordenadas(px_place, py_place, pz=config.ALTURA_SEGURA_Z)
            
            # --- SEGUNDA CORRECCIÓN: Pausa para estabilización antes del descenso. ---
            time.sleep(1.5)

            logging.info("Bajando pieza a la posición de colocación.")
            self.controlador.mover_a_coordenadas(px_place, py_place, pz=pz_place)
            time.sleep(2.0)
            self.controlador.abrir_pinza()
            time.sleep(1)
            self.controlador.mover_a_coordenadas(px_place, py_place, pz=config.ALTURA_SEGURA_Z)
        
        self.controlador.mover_a_posicion_home()

    def _obtener_coords_destino_final(self, destino, tipo):
        if tipo == 'deposito':
            if destino == 1: return config.POSICION_A1
            if destino == 2: return config.POSICION_A2
        elif tipo == 'apilado':
            return destino
        elif tipo == 'retorno':
            px_corregido, py_corregido = self._aplicar_offsets_por_cuadrante(destino[0], destino[1])
            return px_corregido, py_corregido, config.ALTURA_PICKING_Z
        return None, None, None

    def _aplicar_offsets_por_cuadrante(self, px, py):
        offset_x, offset_y = 0, 0
        if px >= 0 and py <= 0:
            if px > 70: 
                offset_x, offset_y = config.OFFSET_Q1_BORDE_X_MM, config.OFFSET_Q1_BORDE_Y_MM
            else:
                offset_x, offset_y = config.OFFSET_Q1_CENTRO_X_MM, config.OFFSET_Q1_CENTRO_Y_MM
        elif px < 0 and py <= 0:
            offset_x, offset_y = config.OFFSET_Q2_X_MM, config.OFFSET_Q2_Y_MM
        elif px < 0 and py > 0:
            offset_x, offset_y = config.OFFSET_Q3_X_MM, config.OFFSET_Q3_Y_MM
        elif px >= 0 and py > 0:
            offset_x, offset_y = config.OFFSET_Q4_X_MM, config.OFFSET_Q4_Y_MM
        return px + offset_x, py + offset_y