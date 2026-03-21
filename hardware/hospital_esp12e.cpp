/* WIRING:
 * D1 (GPIO5) -> 330 ohm Resistor -> Status LED -> GND
 */
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";
const char *mqtt_server = "192.168.x.x";

const char *HOSP_ID = "H1"; // Change for H2, H3
#define STATUS_LED D1

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char *topic, byte *payload, unsigned int length) {
  // Flash LED 3 times to indicate incoming ambulance route confirmed
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(200);
    digitalWrite(STATUS_LED, LOW);
    delay(200);
  }
}

void setup() {
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
    delay(500);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    if (client.connect(HOSP_ID)) {
      String topic = String("hospital/status/") + HOSP_ID;
      client.subscribe(topic.c_str());
    } else
      delay(5000);
  }
  client.loop();
}