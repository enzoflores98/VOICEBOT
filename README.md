<h1 align="center"> 🗣️ VoiceBot Project 🤖</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/d4ab1a18-9311-4dee-971c-c33eea6f4b84" alt="Logo de VoiceBot en Oro" width="300">
</p>

## Equipo 👥

[Enzo Flores](https://github.com/enzoflores98)  
[Nicolas Barcia](https://github.com/NicoBar91)

## Institución 🎓

[Universidad Nacional de Lomas de Zamora](https://www.unlz.edu.ar/)  
[Facultad de Ingenieria](https://ingenieria.unlz.edu.ar/)


<h2 align="center">Introducción 🧭</h2>

VoiceBot es un brazo robótico de cuatro grados de libertad (4GL) el cual, utilizando visión artificial y reconocimiento de voz, es capaz tomar piezas distinguidas por forma y color para colocarlas en los depósitos ordenados. Su nombre es debido a que su principal funcionalidad es manejar las funciones de pick and place a través de comandos de voz.

<h2 align="center">Objetivos 🎯</h2>

- Creacion de un robot manipulador que sea controlable a través de comandos de voz.
- Integrar visión artificial para el reconocimiento de objetos.
  
<h2 align="center">Modo de uso 🚀</h2>

### Preparación
1.	Colocar las piezas en el área de detección.
2.	Verificar que los depósitos se encuentren en posición.
3.	Verificar conexión a fuentes de energía, Webcam, Arduino/USB y micrófono activo.

### Funcionamiento
1. Ejecutar script main.py.
2. Dar las ordenes en lenguaje natural. Pueden darse varias ordenes de una vez y el robot sera capaz de reconocerlas y ejecutarlas.
El algoritmo será capaz de reconocer su intención aun cuando la instruccion no sea concisa.
3. Aguardar proceso de Pick & Place.
4. Realizar nueva orden.

<p align="center">
  <img src="voicebot.gif" width="600"/>
</p>

📽️ [Ver demo en video](demo.mp4)


<h2 align="center">Caracteristicas generales 📝</h2>


### Esquema del robot

<p align="center">
  <img src="https://github.com/user-attachments/assets/1dc38a6f-7934-4419-8af1-cd8d0cc62e7d" width="600">
</p>

- Longitud total del brazo extendido en horizontal: 381.21mm
- Longitud total del brazo extendido en vertical: 433.16mm

### Componentes

Los eslabones del brazo robótico fueron impresos en 3D con el material PLA. Las piezas, depósitos y apoyos también fueron fabricados con de la misma forma y con el mismo material. 

Para completar la maqueta/prototipo; se encuentra un soporte metálico encargado de sostener la luz LED, necesaria para eliminar problemáticas relacionadas con la detección de imagen, y la Webcam encargada de tomar la imagen desde arriba. Todo esto se encuentra apoyado sobre una plataforma de madera de tipo melamina.


<h2 align="center">Cinemática ⚙️</h2>

El código para esta resolucion fue realizado en Python y se encuentra en el archivo cinematica.py adjunto en este repositorio.
El problema cinematico fue descompuesto en las siguientes partes:

1. Obtención de las coordenadas XY de cada objeto dentro de la zona de detección.
2. Traducción de estos valores a las coordenadas XYZ donde dirigir el efector del robot, tomando la base del mismo como referencia.
3. Obtención de las coordenadas articulares Q1, Q2, Q3 y Q4 para los motores.
4. Envío de estos valores a los servomotores mediante la conexion python-arduino.

Uno de los parámetros que recibe este código como entrada, es el centro del objeto que debe ir a tomar. El código realiza la conversión de ese centro, que esta referenciado a un vértice de la zona de detección, para transformarlo a una posición referenciada al origen del robot. 
Esto se puede interpretar en el siguiente esquema donde el eje coordenado UV es el correspondiente a los objetos y el XY al robot, además de cómo se relacionan matemáticamente entre sí.

<p align="center">
  <img src="https://github.com/user-attachments/assets/6f52e379-fac0-4e89-943a-43ba4f0e97f4" width="700">
</p>

### Cinematica Directa

Para la obtencion de las ecuaciones correspondientes a la cinematica directa de este brazo róbotico, se utilizo el algoritmo de Denavit & Hartemberg. El mismo consiste en obtener la matriz de transformacion homogenea que relaciona la posicion y orientacion del efector del robot con el origen del sistema mediante un metodo sistematico que establece cuatro transformaciones basicas.

Aplicando este algoritmo, el esquema y la tabla de parametros DH resulta:
<p align="center">
  <img src="https://github.com/user-attachments/assets/8c25439c-7188-4f6c-984a-3722218e7ad9" width="700">
</p>

Las ecuaciones que relacion cada sistema de con el del eje anterior, resultan:

$$
A_{01} = R_z(Q_1) \cdot T_z(l_{1z}) \cdot T_x(l_{1x}) \cdot R_x(\alpha)
$$

$$
A_{12} = R_z(Q_2 + \alpha) \cdot T_x(l_2)
$$

$$
A_{23} = R_z(Q_3) \cdot T_x(l_3)
$$

$$
A_{34} = R_z(Q_4) \cdot T_x(l_4)
$$

Finalmente, la MTH:

$$
MTH = A_{01} \cdot A_{12} \cdot A_{23} \cdot A_{34}
$$

Finalmente, esta matriz contiene en su ultima columna, en las tres primeras filas la posicion Px, Py y Pz del efector:


$$
\begin{cases}
P_x = \dfrac{ \left( -12000 \cdot \sin(Q_2) - 12286 \cdot \sin(Q_2 + Q_3) - 13000 \cdot \sin(Q_2 + Q_3 + Q_4) + 835 \right) \cdot \cos(Q_1) }{100} \\\\
P_y = \dfrac{ \left( -12000 \cdot \sin(Q_2) - 12286 \cdot \sin(Q_2 + Q_3) - 13000 \cdot \sin(Q_2 + Q_3 + Q_4) + 835 \right) \cdot \sin(Q_1) }{100} \\\\
P_z = 120 \cdot \cos(Q_2) + \dfrac{6143}{50} \cdot \cos(Q_2 + Q_3) + 130 \cdot \cos(Q_2 + Q_3 + Q_4) + \dfrac{603}{10}
\end{cases}
$$

### Cinamatica Inversa

Las tres ecuaciones que nos brinda el modelo de cinematica directa, obtenidas de la ultima columna de la Mth, nos plantean un escenario con 3 ecuaciones y 4 incognitas. Es por esto que establecemos una cuarta ecuacion vinculada con la orientacion del efector y que depende de un parametro predefinido que es el angulo de la muñeca con respecto al plano horizontal.

Esta ecuacion es:

$$
\alpha = Q_4 - Q_2 + Q_3
$$

El angulo alfa lo definimos segun diseño, 30° se utilizan para el caso.

Con cuatro ecuaciones para cuatro incognitas, utilizamos Python para resolverla mediante metodos numerico con la libreria fsolve. 
Si bien la resolucion de este sistema nos puede brindar varias soluciones que matematicamente satisfacen nuestro sistema de ecuaciones, se requieren una serie de restricciones para que los valores sean coherentes con el esquema fisico del robot.
Asimismo, es necesario una traduccion de los angulos matematicos a los angulos de giro de los servomotores, que dependen de su inicial real. Por este motivo, el codigo cuenta con una funcion especial para traducir este offset.



<h2 align="center">Software 💻</h2>


Con excepción del control de los motores servos, que se realiza con un código de Arduino, el código del proyecto se encuentra realizado íntegramente con Python.

El lineamiento principal fue resolver las diferentes partes en módulos según funcionalidad para luego integrarlas en un archivo principal que consulte a cada fuente por separado según necesidad. El diagrama de flujo utilizado para poder incorporar la interacción de las diferentes funciones del código es el siguiente:

<p align="center">
  <img src="https://github.com/user-attachments/assets/d3656247-c3b4-49b3-86f7-290a1840dea6" width="700">
</p>

### Reconocimiento de voz

El script que controla este codigo es audio.py. Este modulo se consulta desde main.py, su funcion es realizar el procesamiento de la orden dictada por el usuario y devolver al flujo principal una cada de texto de tres palabras: FORMA COLOR DEPOSITO. 

Se utiliza la librería Pyaudio, para el control del flujo de datos de audio y OpenAI para la transcripción y procesamiento de la orden. Un paso fundamental en este paso es el "entendimiento" de la orden dictada por el usuario. La misma se recibe en forma de texto plano y a través de un prompt que utiliza el modelo "gpt-3.5-turbo" se obtiene la salida en forma cadena de texto.

Ejemplo de prompt:

```txt
Debes responder con exactamente tres cadenas de texto. La primera será una forma, la segunda será un color y la tercera es un número.
El usuario mencionará o insinuará una forma y un color explícita o implícitamente, además de un número de depósito. Tu tarea será interpretar y responder.
Tu respuesta tendrá el formato 'FORMA' 'COLOR' 'NUMERO' (el número deberá responderse con un carácter numérico).
Las formas como respuesta deben ser: 'CILINDRO', 'CUBO', 'ETC'.
Los colores como respuesta deben ser: 'ROJO', 'NEGRO', 'ETC'.
Tu respuesta irá directo a los datos de entrada para mover un robot el cual tomará la forma, color y número como instrucción. Por este motivo es importante que solo respondas con el formato indicado.
Como único caso excepcional en donde responderás algo que sea diferente, es cuando las instrucciones no tengan sentido o no brinden la información suficiente. En ese caso deberás responder 'Instrucción no reconocida'.
No agregues ningún texto ni carácter adicional.
Ten en cuenta que la entrada puede no ser del todo explícita y en ese caso deberás entender qué es lo que el usuario quiere hacer.
```

Los pasos que realiza este script, entonces, son:

1.	Recibe una orden por voz utilizando el micrófono. Esto será un audio en donde se encuentre la frase dictada por el usuario
2.	La frase recibida será transcripta a texto haciendo uso del modelo “whisper-1” de OpenAI
3.	El texto será procesado por un prompt predefinido que utilizará el modelo "gpt-3.5-turbo" y devuelve una orden concisa como cadena de caracteres con tres palabras: FORMA COLOR DEPOSITO. Por ejemplo: texto de entrada < ”Quiero mover la pieza de color rojo y con forma cilíndrica al segundo deposito” > devolverá la instrucción < ”CILINDRO ROJO 2” >



### Visión Artificial

El script que se utiliza para el reconocimiento de los objetos es deteccion.py. 

Para este código se utilizó la librería CV2 desarrollada por OpenCV. La delimitación del área de detección se realizó con marcadores aruco:

<p align="center">
  <img src="https://github.com/user-attachments/assets/3ec0a26a-6d17-4fc2-bc7d-325de4ee0113" width="600">
</p>

Su documentación se puede encontrar en el siguiente [link](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)

Estos marcadores son muy utilizados en el campo de la visión artificial dado que se pueden identificar fácilmente con su sistema de codificación y establecer los bordes para brindar un marco de referencia absoluto a la cámara.

Durante el desarrollo de este proyecto nos encontramos algunos desafíos respecto a la vision artificial. Uno de ellos es respecto a las sombras:

<p align="center">
  <img src="https://github.com/user-attachments/assets/d26b2941-0db1-4917-be2e-0c8edddc4d47" width="400">
</p>

Como se aprecia en la imagen; la sombra puede añadir, no solo distorsión a las medidas reales del objeto en cuanto a su centro, sino también lineas que puedan interpretarse como lados del objeto y por lo tanto provocar un error de identificacion de la forma. 
Para no depender de la iluminacion del ambiente, la resolucion adoptada fue colocar una fuente de LED que proporcione luz continua. 



En este modulo del software se realiza la identificación de cada una de las piezas situadas en el área de detección. Esta identificación se constituye en:
- **Forma**: el algoritmo utilizado identifica la forma del objeto según la cantidad de aristas observadas. Se brinda al código una serie de condicionales para las formas conocidas y se hace una verificación de cuál es la que se cumple.
- **Color**: esta basada en el modelo HSV que define un color según su matiz, saturación y brillo (valor). El código establece una serie mascaras para determinar un rango predefinido para cada color identificable por nuestro software.
- **Coordenadas del centro de cada objeto**: dada la naturaleza regular de los objetos con los que se trabaja en el alcance de este proyecto, este se calcula de forma simple considerándolo inscripto en un rectángulo del cual se calcula su centro con base/2 para X y altura/2 para Y.

A este script se ingresa desde main.py con una frame capturado por la camara y se espera que devuelva un vector de vectores denominado centros_objetos. Cada vector contenido dentro de centros_objetos tendra la forma (shape, color, cx, cy), que refiera a forma, color, coordenada X y coordenada Y del centro del objeto.

### Script Principal

Este codigo es el encargado de manipular el flujo del programa orquestando las diferentes entradas y salidas de parametros para cada fuente. 
Además, en este código se realiza el matcheo entre los objetos detectados por la vision artificial y la orden dictada por el usuario. Una vez encontrada la coincidencia entre ambos, se envia la orden al script de cinematica para terminar con el proceso de pick and place.

El diagrama de flujo del programa queda de la siguiente forma:
1.	Módulo deteccion.py recibe como parámetro la imagen a analizar y devuelve un vector que contiene la información de cada objeto detectado.
2.	Módulo audio.py, se activa desde main.py y devuelve una cadena de tres palabras: FORMA COLOR DEPOSITO.
3.	El código main.py realiza una búsqueda para cruzar la información de la orden con el vector de objetos detectados y devuelve una posición XY que es el centro del objeto que se debe tomar.
4.	El modulo cinemática.py recibe esta coordenada XY y el número de depósito. Realiza las ecuaciones para el calculo de las variables Q1, Q2, Q3 y Q4 que llevan el efector a destino para tomar el objeto y depositarlo en el recipiente correcto. 
5.	Reinicio del bucle.

<h2 align="center">Componentes electrónicos ⚡</h2>

-	Arduino UNO R3
-	4 servomotores MG995R
-	1 servomotores SG95
-	Fuente de alimentación 5V 10A
-	Capacitor electrolítico 3300 µF 16V





