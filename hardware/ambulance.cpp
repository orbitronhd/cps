#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <Wire.h>

// --- CONFIGURATION ---
const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";
const char *mqtt_server = "192.168.x.x"; // IP of your CachyOS Laptop
const int mqtt_port = 1883;

const char *AMBULANCE_ID = "AMB_01";
const char *DEFAULT_DESTINATION = "H1";

// --- PIN DEFINITIONS ---
#define BTN_HIGH_PRIO 4
#define BTN_LOW_PRIO 5

// --- OLED SETUP ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Debounce variables
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay =
    300; // 300ms delay to prevent double-presses

void updateDisplay(const char *header, const char *message) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println(header);

  display.setTextSize(2);
  display.setCursor(0, 20);
  display.println(message);
  display.display();
}

void setup_wifi() {
  updateDisplay("WiFi", "Connecting...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  updateDisplay("WiFi", "Connected!");
  delay(1000);
}

void sendDistressSignal(int priority) {
  StaticJsonDocument<200> doc;
  doc["id"] = AMBULANCE_ID;
  doc["priority"] = priority;
  doc["dest"] = DEFAULT_DESTINATION;

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);

  mqttClient.publish("ambulance/requests", jsonBuffer);

  String prioText = (priority == 1) ? "PRIO 1" : "PRIO 2";
  updateDisplay("Request Sent", prioText.c_str());
  Serial.println("Distress signal sent: " + String(jsonBuffer));
}

void callback(char *topic, byte *payload, unsigned int length) {
  // This receives updates from the central server
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  updateDisplay("Server Update", msg.c_str());
}

void reconnect() {
  while (!mqttClient.connected()) {
    updateDisplay("MQTT", "Connecting...");
    if (mqttClient.connect(AMBULANCE_ID)) {
      String subTopic = String("ambulance/") + AMBULANCE_ID + "/status";
      mqttClient.subscribe(subTopic.c_str());
      updateDisplay("System Ready", "Awaiting input");
    } else {
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;)
      ; // Halt
  }

  // Initialize Buttons
  pinMode(BTN_HIGH_PRIO, INPUT_PULLUP);
  pinMode(BTN_LOW_PRIO, INPUT_PULLUP);

  setup_wifi();
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // Button Reading Logic
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (digitalRead(BTN_HIGH_PRIO) == LOW) {
      sendDistressSignal(1);
      lastDebounceTime = millis();
    } else if (digitalRead(BTN_LOW_PRIO) == LOW) {
      sendDistressSignal(2);
      lastDebounceTime = millis();
    }
  }
}