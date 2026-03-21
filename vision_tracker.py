import cv2
import cv2.aruco as aruco
import paho.mqtt.client as mqtt
import json
import system_config
import time

# Node Bounding Boxes (X_min, Y_min, X_max, Y_max) - Calibrate these to your physical board
ZONES = {
    "N1": (100, 100, 300, 300),
    "N2": (400, 100, 600, 300),
    "N3": (700, 100, 900, 300),
}
# Map ArUco IDs to Ambulance IDs
AMB_MARKERS = { 0: "AMB_01", 1: "AMB_02" }

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "VisionTracker")
mqtt_client.connect(system_config.MQTT_BROKER, system_config.MQTT_PORT, 60)
mqtt_client.loop_start()

# If using scrcpy via OBS Virtual Camera, this is usually 0 or 1.
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

last_known_nodes = {}

print("[VISION] Tracking Active. Press 'q' to quit.")
while True:
    ret, frame = cap.read()
    if not ret: continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:
        for i in range(len(ids)):
            marker_id = ids[i][0]
            if marker_id in AMB_MARKERS:
                amb_id = AMB_MARKERS[marker_id]
                
                # Calculate center of marker
                c = corners[i][0]
                cx, cy = int(c[:, 0].mean()), int(c[:, 1].mean())
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

                # Check which zone the center point is in
                for node, (x1, y1, x2, y2) in ZONES.items():
                    if x1 < cx < x2 and y1 < cy < y2:
                        if last_known_nodes.get(amb_id) != node:
                            payload = json.dumps({"id": amb_id, "node": node})
                            mqtt_client.publish(system_config.TOPIC_AMB_LOCATION, payload)
                            last_known_nodes[amb_id] = node
                            print(f"[TRACKING] {amb_id} entered {node}")

    cv2.imshow('Cyber-Physical Map Tracker', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()