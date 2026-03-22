#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "Pixel 10 Pro XL";
const char* password = "alskdjfhg";
const char* mqtt_server = "10.163.125.102";

const char* INTERSECTION_ID = "INT_01";

#define NS_GREEN D1
#define NS_RED D2
#define EW_GREEN D5
#define EW_RED D6

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastTrafficChange = 0;
const unsigned long trafficInterval = 5000; // 5 seconds per light cycle
bool isNortheastGreen = true;
bool isPreempted = false;

void setLights(bool nsGreen, bool nsRed, bool ewGreen, bool ewRed) {
    digitalWrite(NS_GREEN, nsGreen);
    digitalWrite(NS_RED, nsRed);
    digitalWrite(EW_GREEN, ewGreen);
    digitalWrite(EW_RED, ewRed);
}

void callback(char* topic, byte* payload, unsigned int length) {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    if (error) return;

    String action = doc["action"];
    
    if (action == "PREEMPT_ROUTE") {
        String direction = doc["direction"];
        isPreempted = true;
        Serial.print("[ALARM] Preemption Active for Lane: ");
        Serial.println(direction);

        if (direction == "NS") {
            setLights(HIGH, LOW, LOW, HIGH); // NS Green, EW Red
        } else if (direction == "EW") {
            setLights(LOW, HIGH, HIGH, LOW); // NS Red, EW Green
        }
    } 
    else if (action == "CLEAR") {
        Serial.println("[RESUME] Preemption Cleared. Resuming standard loop.");
        isPreempted = false;
        lastTrafficChange = millis(); // Reset timer to avoid instant flip
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("[MQTT] Connecting...");
        if (client.connect(INTERSECTION_ID)) {
            Serial.println("SUCCESS");
            String topic = String("traffic/lights/") + INTERSECTION_ID;
            client.subscribe(topic.c_str());
        } else {
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
    
    // Initial State: NS Green, EW Red
    setLights(HIGH, LOW, LOW, HIGH);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
}

void loop() {
    if (!client.connected()) reconnect();
    client.loop();

    // Standard traffic light cycle (only runs if no ambulance is present)
    if (!isPreempted) {
        unsigned long currentMillis = millis();
        if (currentMillis - lastTrafficChange >= trafficInterval) {
            lastTrafficChange = currentMillis;
            isNortheastGreen = !isNortheastGreen;
            
            if (isNortheastGreen) {
                setLights(HIGH, LOW, LOW, HIGH);
            } else {
                setLights(LOW, HIGH, HIGH, LOW);
            }
        }
    }
}