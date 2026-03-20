#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// --- CONFIGURATION ---
const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";
const char *mqtt_server = "192.168.x.x"; // IP of your CachyOS Laptop
const int mqtt_port = 1883;

// Unique ID for this specific intersection
const char *NODE_ID = "N2";
String control_topic = String("traffic/control/") + NODE_ID;

// --- PIN DEFINITIONS ---
#define NS_GREEN D1
#define NS_RED D2
#define EW_GREEN D5
#define EW_RED D6

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

// Function to set default "safe" state (N/S Green, E/W Red)
void setNormalState() {
  digitalWrite(NS_GREEN, HIGH);
  digitalWrite(NS_RED, LOW);
  digitalWrite(EW_GREEN, LOW);
  digitalWrite(EW_RED, HIGH);
  Serial.println("[STATE] Normal Flow (N/S Green)");
}

// Function to clear the path for the ambulance
void setPreemptState(const char *target_amb) {
  // In our logic, if the ambulance is approaching N2, we force N/S Green.
  // You would adjust this logic based on which way the ambulance is actually
  // facing.
  digitalWrite(NS_GREEN, HIGH);
  digitalWrite(NS_RED, LOW);
  digitalWrite(EW_GREEN, LOW);
  digitalWrite(EW_RED, HIGH);

  Serial.print("[STATE] PREEMPT GREEN activated for ");
  Serial.println(target_amb);
}

void callback(char *topic, byte *payload, unsigned int length) {
  // Convert payload to String
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // Parse JSON
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("JSON Parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  const char *state = doc["state"];
  const char *target_amb = doc["target_amb"];

  if (String(state) == "PREEMPT_GREEN") {
    setPreemptState(target_amb);
  } else if (String(state) == "NORMAL") {
    setNormalState();
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(NODE_ID)) {
      Serial.println("connected");
      client.subscribe(control_topic.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(NS_GREEN, OUTPUT);
  pinMode(NS_RED, OUTPUT);
  pinMode(EW_GREEN, OUTPUT);
  pinMode(EW_RED, OUTPUT);

  setNormalState(); // Boot up into a safe state

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}