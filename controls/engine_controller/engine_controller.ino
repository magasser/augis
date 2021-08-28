/**
 * Title: AUGIS Driving controls for Arduino
 * Author: Manuel Gasser
 * Created: 27.02.2021
 * Updated: 11.06.2021
 * Version: 1.5
 *
 * Description:
 * Script to control the steering and throttle of the AUGIS
 * with Arduino.
 */

// Libraries
#include <Servo.h>
#include <Scheduler.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include "Command.h"

#define   DEBUG_MODE        false

// Define constant variables for throttle range of the engines
#define   BWD_THROTTLE_MAX  1180
#define   BWD_DZ            1380
#define   NO_THROTTLE       1500
#define   FWD_DZ            1580
#define   FWD_THROTTLE_MAX  1840


// Define for pins
#define   ENGINE_LEFT_PIN   2    // Yellow
#define   ENGINE_RIGHT_PIN  1    // Green
#define   MODE_PIN          0    // Purple

// Baude rate for serial output
#define   SERIAL_BAUDE      115200

// Loop delay
#define   LOOP_DELAY        10

// Input size of commands
#define   INPUT_SIZE        100

// Command delimiters
#define   DEL_PREFIX        ':'
#define   DEL_SEP           ','

// Time to wait when no commands sent in milliseconds
#define   RASP_WAIT         5000
#define   RASP_INTERVAL     500

// WiFi connection
#define WIFI_SSID           "***"
#define WIFI_PWD            "***"

// Serial timeout in milliseconds
#define SERIAL_TIMEOUT      500

// MQTT connection
#define MQTT_PORT           1883
#define MQTT_USER           "***"
#define MQTT_PWD            "***"
#define MQTT_KEEPALIVE      3

// Time to wait for connections to be established
#define CONN_WAIT      1000

// Clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// MQTT
const char* MQTT_HOST = "augis.ti.bfh.ch";
const char* COMMAND_MODE = "augis/command/mode";
const char* COMMAND_ENGINE = "augis/command/engine";
const char* INFO_MODE = "augis/info/mode";
const char* INFO_CONN = "augis/info/conn";
const char* ERROR_CONN = "augis/error/conn";
const char* LWT = "augis/lwt";
const char* HELLO_REQ = "augis/hello/req";
const char* HELLO_RESP = "augis/hello/resp";
const char* RASP_IP = "augis/raspberry/ip";

// Engine struct
struct Engine {
  unsigned short cValue;
  bool isFWD;
  Servo servo;
};

// Initialize engines
Engine engineLeft = { NO_THROTTLE, true, Servo() };
Engine engineRight = { NO_THROTTLE, true, Servo() };

// Enum for modes
enum Mode {
  AUTONOMOUS,
  RADIO_REMOTE,
  EMERGENCY,
};

// Current mode
Mode mode;

boolean ledState = false;

// Time when last command was sent
unsigned long timeLastConnReceived;
unsigned long timeLastConnSent;

// Time since last reconnect attempt
unsigned long lastReconnectMQTT = 0;
unsigned long lastReconnectWiFi = 0;

/**
 * Setup function sets initial values and pin modes
 */
void setup() {
  // Attach servos to their respective pins
  engineLeft.servo.attach(ENGINE_LEFT_PIN, BWD_THROTTLE_MAX, FWD_THROTTLE_MAX);
  engineRight.servo.attach(ENGINE_RIGHT_PIN, BWD_THROTTLE_MAX, FWD_THROTTLE_MAX);

  // Setup serial output for USB communication
  SerialUSB.begin(SERIAL_BAUDE);
  SerialUSB.setTimeout(SERIAL_TIMEOUT);
  unsigned long startConnect = millis();

  while(!SerialUSB && millis() - startConnect <= CONN_WAIT) delay(100);

  // Set default mode
  mode = RADIO_REMOTE;

  // Set mode pin to output
  pinMode(MODE_PIN, OUTPUT);
  // Set led pin as output pin
  pinMode(LED_BUILTIN, OUTPUT);

  // Connect to WiFi
  debugPrint("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PWD);
  startConnect = millis();

  while(WiFi.status() != WL_CONNECTED && millis() - startConnect <= CONN_WAIT) {
    delay(100);
  }

  if(WiFi.status() == WL_CONNECTED) {
    debugPrint("Connected to WiFi");
  } else {
    debugPrint("Failed to connect to WiFi");
  }

  // Set last command to current time
  timeLastConnReceived = millis();

  // Setup MQTT
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttOnMessage);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE);

  // Connect to MQTT
  debugPrint("Connecting to MQTT...");
  startConnect = millis();
  while(!mqttClient.connected() && millis() - startConnect <= CONN_WAIT) {
    if(mqttClient.connect("arduino_mkr_1010_wifi", MQTT_USER, MQTT_PWD)) {

      mqttSubscribeToTopics();
    }
    delay(50);
  }

  if(mqttClient.connected()) {
      debugPrint("Connected to MQTT");
  } else {
    debugPrint("Failed to connect to MQTT ");
  }

  // Start reconnection loop for WiFi and MQTT
  Scheduler.startLoop(reconnectLoop);
}

/**
 * Main execution loop
 */
void loop() {
  // Execute code from current mode
  switch(mode) {
    case AUTONOMOUS:
      autonomousMode();
      break;
    case RADIO_REMOTE:
      radioRemoteMode();
      break;
    case EMERGENCY:
      emergencyMode();
      break;
    default:
      radioRemoteMode();
      break;
  }

  raspberryConnCheck();

  mqttClient.loop();


  // Delay to not repeat the loop to often
  delay(LOOP_DELAY);
}

/**
 * In the autonomous mode the arduino adjust the throttle and
 * steering of the AUGIS according to the received commands.
 */
void autonomousMode() {
  // Set low to have switch board in autonomous mode
  digitalWrite(MODE_PIN, HIGH);

  checkForCommands();

  // Write new throttle values for each engine
  writeEngines();
}

/**
 * In the radio remote mode the mode pin is set to low
 * for the AUGIS to be controled with the remote control.
 */
  // Set low to have switch board in remote control mode
void radioRemoteMode() {
  digitalWrite(MODE_PIN, LOW);

  checkForCommands();
}

/**
 *
 */
void emergencyMode() {
  // Set high to have switch board in autonomous mode
  digitalWrite(MODE_PIN, HIGH);

  writeEngines();

  // Change to radio remote mode when no mqtt is not available
  if(WiFi.status() != WL_CONNECTED || !mqttClient.connected()) {
    //mode = RADIO_REMOTE;
    engineLeft.cValue = NO_THROTTLE;
    engineRight.cValue = NO_THROTTLE;
  }
}

/**
 * Check for commands on the serial USB connection and
 * execute them.
 */
void checkForCommands() {
  // Check if new command was sent
  if(SerialUSB.available() > 0) {

    // Read the command
    Command cmd = readCommand();
    executeCommand(cmd);
  }
}

/**
 * Write current throttle values to both engines and handle direction
 * change from forward to backward.
 */
void writeEngines() {
  handleEngine(&engineLeft);
  handleEngine(&engineRight);
}

void handleEngine(Engine *engine) {
  if(engine->isFWD) {
    if(engine->cValue <= BWD_DZ) {
      engine->isFWD = false;
      engine->servo.writeMicroseconds(BWD_THROTTLE_MAX);
      delay(100);
      engine->servo.writeMicroseconds(NO_THROTTLE);
      delay(100);
      engine->servo.writeMicroseconds(engine->cValue);
    } else {
      engine->servo.writeMicroseconds(engine->cValue);
    }
  } else {
    engine->servo.writeMicroseconds(engine->cValue);
    engine->isFWD = engine->cValue >= NO_THROTTLE;
  }
}

/**
 * Executes given command.
 *
 * @param cmd command to be executed
 */
void executeCommand(Command cmd) {
  String prefix = cmd.getPrefix();
  String data = cmd.getData();
  prefix.toUpperCase();

  // Reset time since last command
  if(prefix.equals("CONN") && data.equals("raspberry-pi")) {
    timeLastConnReceived = millis();
    mqttClient.publish(INFO_CONN, "rasp-ard");
  }
  mqttClient.publish("debug/arduino", data.c_str());
  debugPrint(prefix + ": " + data);
  if(prefix.equals("ENGINE")) {
    int i = data.indexOf(",");
    int valueLeft = data.substring(0, i).toInt();
    int valueRight = data.substring(i+1).toInt();
    if(valueLeft > 0) {
      engineLeft.cValue = map(valueLeft, 0, 100, FWD_DZ, FWD_THROTTLE_MAX);
    } else if(valueLeft == 0) {
      engineLeft.cValue = NO_THROTTLE;
    } else {
      engineLeft.cValue = map(valueLeft, -100, 0, BWD_THROTTLE_MAX, BWD_DZ);
    }
    if(valueRight > 0) {
      engineRight.cValue = map(valueRight, 0, 100, FWD_DZ, FWD_THROTTLE_MAX);
    } else if(valueRight == 0) {
      engineRight.cValue = NO_THROTTLE;
    } else {
      engineRight.cValue = map(valueRight, -100, 0, BWD_THROTTLE_MAX, BWD_DZ);
    }
  } else if(prefix.equals("MODE")) {
    data.toLowerCase();
    if(data.equals("auto")) {
      mode = AUTONOMOUS;
      mqttClient.publish(INFO_MODE, "auto");
    } else if(data.equals("radio-remote")) {
      mode = RADIO_REMOTE;
      mqttClient.publish(INFO_MODE, "radio-remote");
    }
  }
}

/**
 * Send command on the serial USB connection.
 *
 * @param cmd command to be sent
 */
void sendCommand(Command cmd) {
  String prefix = cmd.getPrefix();
  String data = cmd.getData();
  String message = String(prefix + ": " + data + "\n");
  SerialUSB.write(message.c_str());
}

/**
 * Returns command read from SerialUSB USB connection
 *
 * @return command that was read
 */
Command readCommand() {
  String input = SerialUSB.readStringUntil('\n');

  return Command(input.c_str(), DEL_PREFIX);
}

/**
 * Callback when for MQTT message
 *
 * @param topic from the message
 * @param payload of the message
 * @param length of the payload
 */
void mqttOnMessage(char *topic, byte *p, unsigned int length) {
  byte* payload = (byte*)malloc(length);
  memcpy(payload,p,length);
  String msg = convertByteArrayToString(payload, length);

  if(strcmp(topic, HELLO_REQ) == 0) {
    mqttClient.publish(HELLO_RESP, "arduino");
  } else if(strcmp(topic, COMMAND_MODE) == 0) {
    if(msg.equals("emergency")) {
      mode = EMERGENCY;
      engineLeft.cValue = NO_THROTTLE;
      engineRight.cValue = NO_THROTTLE;
      mqttClient.publish(INFO_MODE, "emergency");
    } else if(msg.equals("auto")) {
      mode = AUTONOMOUS;
      engineLeft.cValue = NO_THROTTLE;
      engineRight.cValue = NO_THROTTLE;
      mqttClient.publish(INFO_MODE, "auto");
    } else if(msg.equals("radio-remote")) {
      mode = RADIO_REMOTE;
      engineLeft.cValue = NO_THROTTLE;
      engineRight.cValue = NO_THROTTLE;
      mqttClient.publish(INFO_MODE, "radio-remote");
    }
  } else if(mode == EMERGENCY) {
    if(strcmp(topic, COMMAND_ENGINE) == 0) {
      executeCommand(Command("engine", msg.c_str()));
    }
  }
  free(payload);
}

/**
 * Convert byte array to string.
 *
 * @param bytes byte array pointer
 * @param length of the byte array
 * @return string
 */
String convertByteArrayToString(byte *bytes, unsigned int length) {
  String ret;
  for(int i = 0; i < length; i++) {
    ret += (char)bytes[i];
  }

  return ret;
}

/**
 * Function to check if connection to raspberry is working.
 */
void raspberryConnCheck() {
  unsigned long now = millis();

  if(now - timeLastConnSent > RASP_INTERVAL) {
    sendCommand(Command("conn", "arduino"));
    timeLastConnSent = now;
  }

  // Check if no commands has been sent for to long
  if(now - timeLastConnReceived > RASP_WAIT) {
    // Failsafe A
    mode = RADIO_REMOTE;
    engineLeft.cValue = NO_THROTTLE;
    engineRight.cValue = NO_THROTTLE;

    if(mqttClient.connected()) {
      mqttClient.publish(ERROR_CONN, "Arduino lost connection to Raspberry Pi.");
      mqttClient.publish(INFO_MODE, "radio-remote");
      mqttClient.publish(ERROR_CONN, "rasp-ard");
    }
  }

}

/**
 * Loop for reconnecting to WiFi and MQTT if connection was lost.
 */
void reconnectLoop() {
  // Reconnect to WiFi if connection was lost
  if(WiFi.status() != WL_CONNECTED) {
    unsigned long now = millis();
    if(now - lastReconnectWiFi > CONN_WAIT) {
      lastReconnectWiFi = now;
      if(reconnectToWiFi()) {
        debugPrint("Reconnected to WiFi");

        lastReconnectWiFi = 0;
      }
    }
  }

  // Reconnect to MQTT if connection was lost
  if(WiFi.status() == WL_CONNECTED && !mqttClient.connected()) {
    unsigned long now = millis();
    mode = RADIO_REMOTE;
    if(now - lastReconnectMQTT > CONN_WAIT) {
      lastReconnectMQTT = now;
      if(reconnectToMQTT()) {
        debugPrint("Reconnected to MQTT");

        lastReconnectMQTT = 0;
      }
    }
  }

  if(mqttClient.connected()) {
    digitalWrite(LED_BUILTIN, HIGH);
    ledState = true;
  } else if(WiFi.status() == WL_CONNECTED) {
    mode = RADIO_REMOTE;
    if(ledState) {
      digitalWrite(LED_BUILTIN, LOW);
      ledState = false;
    } else {
      digitalWrite(LED_BUILTIN, HIGH);
      ledState = true;
    }
  } else {
    mode = RADIO_REMOTE;
    digitalWrite(LED_BUILTIN, LOW);
    ledState = false;
  }

  delay(LOOP_DELAY * 2);
}

/**
 * Reconnect to WiFi
 *
 * @return true if reconnect was successful
 */
boolean reconnectToWiFi() {
  debugPrint("Reconnecting to WiFi...");

  WiFi.begin(WIFI_SSID, WIFI_PWD);

  return WiFi.status() == WL_CONNECTED;
}

/**
 * Subscribe to topics on MQTT
 */
void mqttSubscribeToTopics() {
  mqttClient.subscribe(COMMAND_MODE);
  mqttClient.subscribe(COMMAND_ENGINE);
  mqttClient.subscribe(HELLO_REQ);
  mqttClient.subscribe(HELLO_RESP);
  mqttClient.subscribe(RASP_IP);

  mqttClient.publish(HELLO_REQ, "arduino");
}

 /**
  * Reconnect to MQTT
  *
  * @return true if reconnect was successful
  */
boolean reconnectToMQTT() {
  debugPrint("Reconnecting to MQTT...");
  debugPrint(MQTT_HOST);

  if(mqttClient.connect("arduino_mkr_1010_wifi", MQTT_USER, MQTT_PWD, LWT, 0, false, "arduino")) {
    mqttSubscribeToTopics();
  }

  return mqttClient.connected();
}

void debugPrint(String str) {
  if(DEBUG_MODE) {
    Serial.println(str);
  }
}
