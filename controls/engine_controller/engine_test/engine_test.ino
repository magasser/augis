#include <Servo.h>

#define   MIN_THROTTLE   1050
#define   NO_THROTTLE     1450
#define   MAX_THROTTLE    1870

#define   ENGINE_LEFT_PIN   2    // Yellow
#define   ENGINE_RIGHT_PIN  1    // Green
#define   MODE_PIN          0    // Purple

#define   LOOP_DELAY        50

Servo engineLeftServo;
Servo engineRightServo;

int cEngineLeft = NO_THROTTLE;
int cEngineRight = NO_THROTTLE;

unsigned int scale;

void setup() {  
  Serial.begin(9600);
  
  engineLeftServo.attach(ENGINE_LEFT_PIN);
  engineRightServo.attach(ENGINE_RIGHT_PIN);

  scale = (MAX_THROTTLE - MIN_THROTTLE) / 1000;

  pinMode(MODE_PIN, OUTPUT);
  digitalWrite(MODE_PIN, HIGH);

  writeEngines();

  while(!Serial);
}

void loop() {
  
  /*for(int i = 0; i < 400; i++) {
    cEngineLeft = NO_THROTTLE;
    cEngineRight = NO_THROTTLE;
    cEngineLeft -= i*1;
    cEngineRight -= i*1;
    
    Serial.println(cEngineLeft);
    
    writeEngines();

    delay(50);
  }*/
  
  /*if(Serial.available()) {
    String input = Serial.readString();
    unsigned int val = input.toInt();
    Serial.println(val);
    cEngineLeft = val;
    //cEngineRight = val;
  }*/
  
  writeEngines();

  
  /*cEngineLeft = 1870;
  cEngineRight = 1870;
  writeEngines();
  Serial.println("FWD");
  delay(1000);
  cEngineLeft = 1450;
  cEngineRight = 1450;
  writeEngines();
  Serial.println("STOP");
  delay(100);
  cEngineLeft = 1050;
  cEngineRight = 1050;
  writeEngines();
  delay(100);
  cEngineLeft = 1450;
  cEngineRight = 1450;
  writeEngines();
  delay(100);
  cEngineLeft = 1050;
  cEngineRight = 1050;
  writeEngines();
  Serial.println("BWD");
  delay(1000);*/
}

void writeEngines() {
  engineLeftServo.writeMicroseconds(cEngineLeft);
  engineRightServo.writeMicroseconds(cEngineRight);
}
