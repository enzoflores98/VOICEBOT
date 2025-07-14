#include <Servo.h>

// Definición de los servos
Servo eje1;
Servo eje2;
Servo eje3;
Servo eje4;
Servo eje5;
Servo eje6;

// Definición de los pines de los servos en un Arduino Uno
//const int eje5pin = 9; 
//const int eje4pin = 10;  
//const int eje6pin = 11;
//const int eje1pin = 3; 
//const int eje2pin = 5; 
//const int eje3pin = 6; 

const int eje5pin = 5;
const int eje4pin = 6;
const int eje6pin = 3;
const int eje1pin = 11;
const int eje2pin = 9;
const int eje3pin = 10;


void setup() {
  // Inicializa los servos y los asigna a sus respectivos pines
  eje1.attach(eje1pin);
  eje2.attach(eje2pin);
  eje3.attach(eje3pin);
  eje4.attach(eje4pin);
  eje5.attach(eje5pin);
  eje6.attach(eje6pin);

  // Mueve los servos a la posición inicial
  //moveServos(50,90,125,90,5,180);
  moveServos(0,85,90,125,90,50);
  // Inicia la comunicación serial
  Serial.begin(9600);
}

void loop() {
  // Si hay datos disponibles en el puerto serial
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); // Lee hasta el carácter de nueva línea
    int angles[6];
    int index = 0;

    // Divide los datos en los valores de los ángulos
    char* token = strtok(data.c_str(), ",");
    while (token != NULL && index < 6) {
      angles[index++] = atoi(token);
      token = strtok(NULL, ",");
    }

    // Mueve los servos con los ángulos recibidos
    if (index == 6) {
      moveServos(angles[0], angles[1], angles[2], angles[3], angles[4], angles[5]);
    }
    
  }
}

// Función para mover todos los servos a los ángulos especificados
void moveServos(int eje1Angle, int eje2Angle, int eje3Angle, int eje4Angle, int eje5Angle, int eje6Angle) {
  eje1.write(eje1Angle);
  
  eje2.write(eje2Angle);
  
  eje3.write(eje3Angle);
  
  eje4.write(eje4Angle);
  
  eje5.write(eje5Angle);
  
  eje6.write(eje6Angle);
  
}
