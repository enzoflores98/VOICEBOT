<h1 align="center">VOICEBOT PROJECT</h1>
<p align="center">
  <img src="https://github.com/user-attachments/assets/d4ab1a18-9311-4dee-971c-c33eea6f4b84" alt="Logo de VoiceBot en Oro" width="300">
</p>

## Equipo 👥

[Enzo Flores](https://github.com/enzoflores98)  
[Nicolas Barcia](https://github.com/NicoBar91)

## Institución 🎓

[Univseridad Nacional de Lomas de Zamora](https://www.unlz.edu.ar/)  
[Facultad de Ingenieria](https://ingenieria.unlz.edu.ar/)


<h2 align="center">Introduccion 🤖</h2>

VoiceBot es un brazo robótico de cuatro grados de libertad (4GL) el cual, utilizando visión artificial y reconocimiento de voz, es capaz tomar piezas distinguidas por forma y color para colocarlas en los depósitos ordenados. Su nombre es debido a que su principal funcionalidad es manejar las funciones de pick and place a través de comandos de voz.

## Objetivos 🎯

- Creacion de un robot manipulador que sea controlable a través de comandos de voz
- Integrar visión artificial para el reconocimiento de objetos
  
## Modo de uso 🚀

### Preparación
1.	Colocar las piezas en el área de detección.
2.	Verificar que los depósitos se encuentren en posición.
3.	Verificar conexión a fuentes de energía, Webcam, Arduino/USB y micrófono activo.

### Funcionamiento
1. Ejecutar script main.py.
2. Presionar la barra espaciadora y dar una orden en voz alta la cual contenga: forma, color de la pieza y deposito al cual se va a llevar el objeto.
No es requisito que esta instruccion sea en ese orden. Ademas, el algoritmo será capaz de reconocer su intención aun cuando la instruccion no sea concisa
3. Aguardar proceso de Pick & Place.
4. Realizar nueva orden.

## Caracteristicas generales 📝

### Esquema del robot

<p align="center">
  <img src="https://github.com/user-attachments/assets/1dc38a6f-7934-4419-8af1-cd8d0cc62e7d" width="600">
</p>

- Longitud total del brazo extendido en horizontal: 381.21mm
- Longitud total del brazo extendido en vertical: 433.16mm

### Componentes

Los eslabones del brazo robótico fueron impresos en 3D con el material PLA. Las piezas, depósitos y apoyos también fueron fabricados con de la misma forma y con el mismo material. 
Para completar la maqueta/prototipo; se encuentra un soporte metálico encargado de sostener la luz LED, necesaria para eliminar problemáticas relacionadas con la detección de imagen, y la Webcam encargada de tomar la imagen desde arriba. Todo esto se encuentra apoyado sobre una plataforma de madera de tipo melamina.








