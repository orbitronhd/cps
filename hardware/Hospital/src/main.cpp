#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "Pixel 10 Pro XL";
const char* password = "alskdjfhg";
const char* mqtt_server = "10.163.125.102"; 

const char* HOSPITAL_ID = "HOSP_01";
#define STATUS_LED D1 

WiFiClient espClient;
PubSubClient client(espClient);

int hospitalState = 0; 
unsigned long lastBlinkTime = 0;
bool ledState = LOW;

void callback(char* topic, byte* payload, unsigned int length) {
    Serial.println("\n[RECEIVER] Payload Arrived!");
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (error) {
        Serial.println("[ERROR] Failed to parse JSON");
        return;
    }

    String action = doc["action"];
    if (action == "INCOMING_PATIENT") {
        int priority = doc["priority"];
        Serial.print("[STATE] ALERT TRIGGERED | Priority: ");
        Serial.println(priority);
        
        if (priority == 1) {
            hospitalState = 1; // Start blinking
        } else if (priority == 2) {
            hospitalState = 2; // Solid On
            digitalWrite(STATUS_LED, HIGH); 
        }
    } else if (action == "CLEAR") {
        Serial.println("[STATE] Alert Cleared. Idling.");
        hospitalState = 0;
        digitalWrite(STATUS_LED, LOW); 
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("[MQTT] Connecting to Broker...");
        if (client.connect(HOSPITAL_ID)) {
            Serial.println("SUCCESS!");
            String topic = String("hospital/alerts/") + HOSPITAL_ID;
            client.subscribe(topic.c_str());
            Serial.print("[MQTT] Subscribed to: ");
            Serial.println(topic);
        } else {
            Serial.print("FAILED, rc=");
            Serial.print(client.state());
            Serial.println(" -> Retrying in 5 seconds");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(100); // Give the serial monitor a moment to catch up
    
    Serial.println("\n\n--- HOSPITAL NODE BOOT SEQUENCE ---");
    
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
    
    Serial.print("[WIFI] Connecting to ");
    Serial.print(ssid);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\n[WIFI] Connected Successfully!");
    Serial.print("[WIFI] IP Address: ");
    Serial.println(WiFi.localIP());
    
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    if (hospitalState == 1) {
        unsigned long currentMillis = millis();
        if (currentMillis - lastBlinkTime >= 150) { 
            lastBlinkTime = currentMillis;
            ledState = !ledState;
            digitalWrite(STATUS_LED, ledState);
        }
    }
}