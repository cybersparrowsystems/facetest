import cv2
import time
from simple_facerec import SimpleFacerec
import requests
from datetime import datetime
import paho.mqtt.client as mqtt
import json
import os
from threading import Timer
import threading

# Initialize face recognizer
sfr = SimpleFacerec()
sfr.load_encoding_images("images/")

# Telegram bot setup
BOT_TOKEN = "8155482207:AAEreatrbw-Oh-7dk0fwTyg5nvWiSN2DRVU"
CHAT_ID = "6207462707"

# MQTT setup
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "face_detection/camera2"
MQTT_USERNAME = "hivemq.webclient.1747421508183"
MQTT_PASSWORD = "6uP8c#GY*voAV&x75.dX"

# Track detected people
detected_people = {}

def send_telegram_message(message, image_path=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)
    
    if image_path:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {"photo": open(image_path, "rb")}
        data = {"chat_id": CHAT_ID}
        requests.post(url, data=data, files=files)

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        print(f"Camera 2 received MQTT message: {data}")  # Debug print
        
        # Handle different message types
        if "type" in data:
            if data["type"] == "detection":
                if data["camera"] == "camera1":
                    name = data["name"]
                    if name not in detected_people:
                        detected_people[name] = {"time": datetime.now()}
                        status_msg = f"Person {name} detected at entry point"
                        print(status_msg)
                        
                        # Publish status update with consistent format
                        status_message = {
                            "message": status_msg,
                            "type": "status",
                            "name": name,
                            "camera": "camera2",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "tracking"
                        }
                        client.publish("face_detection/status", json.dumps(status_message))
                        print(f"Published tracking status: {status_message}")
            elif data["type"] == "alert":
                print(f"Received alert: {data['message']}")
    except Exception as e:
        print(f"Error processing message in Camera 2: {e}")
        print(f"Raw message: {message.payload.decode()}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ successfully!")
        # Subscribe to both camera1 and status topics
        client.subscribe([("face_detection/camera1", 0), ("face_detection/status", 0)])
        print("Subscribed to MQTT topics")
    else:
        print(f"Failed to connect to HiveMQ, return code: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from HiveMQ with code: {rc}")

def check_person_status():
    current_time = datetime.now()
    for name, data in list(detected_people.items()):
        time_diff = current_time - data["time"]
        if time_diff.total_seconds() > 10:  # If more than 10 seconds have passed
            # Only send alert if we haven't sent one for this person
            if "alert_sent" not in data:
                alert_msg = f"⚠️ ALERT: {name} has not reached Camera 2 after {time_diff.total_seconds():.1f} seconds!"
                print(alert_msg)
                send_telegram_message(alert_msg)
                
                # Publish alert to MQTT
                alert_message = {
                    "message": alert_msg,
                    "type": "alert",
                    "name": name,
                    "camera": "camera2",
                    "time_elapsed": time_diff.total_seconds(),
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "alert"
                }
                try:
                    client.publish("face_detection/status", json.dumps(alert_message))
                    print(f"Published alert to MQTT: {alert_message}")
                except Exception as e:
                    print(f"Error publishing alert to MQTT: {e}")
                
                # Mark alert as sent
                detected_people[name]["alert_sent"] = True

def start_status_check_timer():
    check_person_status()
    # Schedule the next check
    threading.Timer(5.0, start_status_check_timer).start()

# MQTT client setup
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Connect to MQTT with retry
max_retries = 3
retry_count = 0
connected = False

print("Starting MQTT connection process...")
while retry_count < max_retries and not connected:
    try:
        print(f"Attempting to connect to HiveMQ (attempt {retry_count + 1}/{max_retries})...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        connected = True
        print("MQTT loop started")
        
        # Wait for connection to establish
        print("Waiting for connection to establish...")
        time.sleep(2)
        
        # Verify connection
        if client.is_connected():
            print("MQTT connection verified!")
        else:
            print("MQTT connection failed verification")
            connected = False
            retry_count += 1
            continue
            
    except Exception as e:
        print(f"Error connecting to HiveMQ: {e}")
        retry_count += 1
        if retry_count < max_retries:
            print("Retrying in 5 seconds...")
            time.sleep(5)

if not connected:
    print("Failed to connect to HiveMQ after multiple attempts")
    exit(1)

print("MQTT connection established successfully. Proceeding with camera initialization...")

# Create detections folder if it doesn't exist
if not os.path.exists("detections"):
    os.makedirs("detections")

# Start camera 2
print("Initializing camera...")
cap = cv2.VideoCapture(0)  # Try camera index 0 first
if not cap.isOpened():
    print("Failed to open camera 0, trying camera 1...")
    cap = cv2.VideoCapture(1)  # Try camera index 1
    if not cap.isOpened():
        print("Failed to open camera 1, trying camera 2...")
        cap = cv2.VideoCapture(2)  # Try camera index 2
        if not cap.isOpened():
            print("Failed to open any camera")
            client.loop_stop()
            exit(1)

print("Camera initialized successfully")
detected_faces = set()

# Start the status check timer
print("Starting status check timer...")
start_status_check_timer()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from camera 2.")
        break

    face_locations, face_names = sfr.detect_known_faces(frame)
    
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        if name != "Unknown":
            # Draw box and name with more visible colors and thickness
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 4)  # Even thicker green box
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            
            # Add status text
            status = "Reached Safely"
            if name in detected_people:
                time_diff = datetime.now() - detected_people[name]["time"]
                if time_diff.total_seconds() > 10:
                    status = "⚠️ Alert: Delayed"
                else:
                    status = f"Reached in {time_diff.total_seconds():.1f}s"
            
            cv2.putText(frame, status, (left, bottom + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if name not in detected_faces:
                detected_faces.add(name)
                timestamp = datetime.now()
                image_path = os.path.join("detections", f"{name}_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
                cv2.imwrite(image_path, frame)
                
                # Publish detection message
                detection_message = {
                    "name": name,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "camera": "camera2",
                    "type": "detection",
                    "status": "detected"
                }
                client.publish(MQTT_TOPIC, json.dumps(detection_message))
                print(f"Published detection: {detection_message}")
                
                # Publish status message
                status_msg = f"Person detected at Camera 2: {name} at {timestamp.strftime('%H:%M:%S')}"
                status_message = {
                    "message": status_msg,
                    "type": "status",
                    "name": name,
                    "camera": "camera2",
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "detected"
                }
                client.publish("face_detection/status", json.dumps(status_message))
                print(f"Published status: {status_message}")
                
                send_telegram_message(f"Person detected at Camera 2: {name}\nTime: {timestamp.strftime('%H:%M:%S')}", image_path)

    # Add system status text
    cv2.putText(frame, "Camera 2 - Exit Point", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Camera 2", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()