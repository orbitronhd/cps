/* WIRING:
 * D1 (GPIO5)  -> Both N/S Green LEDs
 * D2 (GPIO4)  -> Both N/S Red LEDs
 * D5 (GPIO14) -> Both E/W Green LEDs
 * D6 (GPIO12) -> Both E/W Red LEDs
 */
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";
const char *mqtt_server = "192.168.x.x";

const char *NODE_ID = "N2"; // CHANGE THIS FOR EACH INTERSECTION

#define NS_GREEN D1
#define NS_RED D2
#define EW_GREEN D5
#define EW_RED D6

WiFiClient espClient;
PubSubClient client(espClient);

void setNormalState() {
  digitalWrite(NS_GREEN, HIGH);
  digitalWrite(NS_RED, LOW);
  digitalWrite(EW_GREEN, LOW);
  digitalWrite(EW_RED, HIGH);
}

void setPreemptState() {
  digitalWrite(NS_GREEN, HIGH);
  digitalWrite(NS_RED, LOW);
  digitalWrite(EW_GREEN, LOW);
  digitalWrite(EW_RED, HIGH);
}

void callback(char *topic, byte *payload, unsigned int length) {
  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload, length);
  String state = doc["state"];
  if (state == "PREEMPT_GREEN")
    setPreemptState();
  else if (state == "NORMAL")
    setNormalState();
}

void setup() {
  pinMode(NS_GREEN, OUTPUT);
  pinMode(NS_RED, OUTPUT);
  pinMode(EW_GREEN, OUTPUT);
  pinMode(EW_RED, OUTPUT);
  setNormalState();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
    delay(500);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    if (client.connect(NODE_ID)) {
      String topic = String("traffic/control/") + NODE_ID;
      client.subscribe(topic.c_str());
    } else
      delay(5000);
  }
  client.loop();
}