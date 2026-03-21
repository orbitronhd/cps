#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "Pixel 10 Pro XL";
const char* password = "alskdjfhg";
const char* mqtt_server = "10.163.125.102"; // Your laptop's hotspot IP

const char* AMBULANCE_ID = "AMB_02";

// Pin definitions matching our earlier hardware plan
#define BTN_PRIORITY_1 4
#define BTN_PRIORITY_2 5

WiFiClient espClient;
PubSubClient client(espClient);

// Debounce state tracking
bool lastStateP1 = HIGH;
bool lastStateP2 = HIGH;
unsigned long lastDebounceTimeP1 = 0;
unsigned long lastDebounceTimeP2 = 0;
const unsigned long debounceDelay = 50; // 50ms threshold

void setup() {
    Serial.begin(115200);
    
    // Internal pullups mean the pin reads HIGH when unpressed, LOW when pressed
    pinMode(BTN_PRIORITY_1, INPUT_PULLUP);
    pinMode(BTN_PRIORITY_2, INPUT_PULLUP);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n[WIFI] Connected.");
    
    client.setServer(mqtt_server, 1883);
}

void reconnect() {
    while (!client.connected()) {
        if (client.connect(AMBULANCE_ID)) {
            Serial.println("[MQTT] Connected to Server.");
        } else {
            delay(5000);
        }
    }
}

void sendPreemptRequest(int priorityLevel) {
    StaticJsonDocument<200> doc;
    doc["ambulance_id"] = AMBULANCE_ID;
    doc["priority"] = priorityLevel;
    doc["action"] = "REQUEST_PREEMPTION";

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    client.publish("ambulance/routing", jsonBuffer);
    Serial.print("[TX] Preemption Request Sent | Priority: ");
    Serial.println(priorityLevel);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    // Handle Priority 1 Button
    bool currentP1 = digitalRead(BTN_PRIORITY_1);
    // If the button was just pressed down...
    if (currentP1 == LOW && lastStateP1 == HIGH) {
        delay(50); // Instantly bypass switch bounce
        if (digitalRead(BTN_PRIORITY_1) == LOW) { // Confirm it's still pressed
            sendPreemptRequest(1);
        }
    }
    lastStateP1 = currentP1;

    // Handle Priority 2 Button
    bool currentP2 = digitalRead(BTN_PRIORITY_2);
    // If the button was just pressed down...
    if (currentP2 == LOW && lastStateP2 == HIGH) {
        delay(50); // Instantly bypass switch bounce
        if (digitalRead(BTN_PRIORITY_2) == LOW) { // Confirm it's still pressed
            sendPreemptRequest(2);
        }
    }
    lastStateP2 = currentP2;
}