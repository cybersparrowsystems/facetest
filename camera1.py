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
MQTT_TOPIC = "face_detection/camera1"
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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ successfully!")
        # Subscribe to both camera2 and status topics
        client.subscribe([("face_detection/camera2", 0), ("face_detection/status", 0)])
        print("Subscribed to MQTT topics")
    else:
        print(f"Failed to connect to HiveMQ, return code: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from HiveMQ with code: {rc}")

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        print(f"Camera 1 received MQTT message: {data}")  # Debug print
        
        # Handle different message types
        if "type" in data:
            if data["type"] == "detection":
                if data["camera"] == "camera2":
                    name = data["name"]
                    if name in detected_people:
                        time_diff = datetime.now() - detected_people[name]["time"]
                        status_msg = f"✅ {name} has reached safely at {datetime.now().strftime('%H:%M:%S')}"
                        print(status_msg)
                        send_telegram_message(status_msg)
                        
                        # Publish success message
                        success_message = {
                            "message": status_msg,
                            "type": "success",
                            "name": name,
                            "camera": "camera1",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "reached"
                        }
                        try:
                            client.publish("face_detection/status", json.dumps(success_message))
                            print(f"Published success to MQTT: {success_message}")
                        except Exception as e:
                            print(f"Error publishing success to MQTT: {e}")
                        
                        del detected_people[name]
            elif data["type"] == "alert":
                print(f"Received alert: {data['message']}")
        else:
            # Handle legacy format
            if "camera" in data and data["camera"] == "camera2":
                name = data["name"]
                if name in detected_people:
                    time_diff = datetime.now() - detected_people[name]["time"]
                    status_msg = f"✅ {name} has reached safely at {datetime.now().strftime('%H:%M:%S')}"
                    print(status_msg)
                    send_telegram_message(status_msg)
                    del detected_people[name]
    except Exception as e:
        print(f"Error processing message in Camera 1: {e}")
        print(f"Raw message: {message.payload.decode()}")

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

# Start camera 1
print("Initializing camera...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Failed to open camera")
    client.loop_stop()
    exit(1)

print("Camera initialized successfully")
detected_faces = set()

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
                    "camera": "camera1",
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

# Replace the existing timer start with this
print("Starting status check timer...")
start_status_check_timer()

# Update the message publishing format to be consistent
def publish_detection(name, timestamp, status="detected"):
    message = {
        "name": name,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "camera": "camera1",
        "status": status,
        "type": "detection"
    }
    try:
        client.publish(MQTT_TOPIC, json.dumps(message))
        print(f"Published to MQTT: {message}")
    except Exception as e:
        print(f"Error publishing to MQTT: {e}")

# Update the status message publishing
def publish_status(message, name, status_type="detection"):
    status_message = {
        "message": message,
        "type": status_type,
        "name": name,
        "camera": "camera1",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"  # Add status field
    }
    try:
        client.publish("face_detection/status", json.dumps(status_message))
        print(f"Published status to MQTT: {status_message}")
    except Exception as e:
        print(f"Error publishing status to MQTT: {e}")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from camera 1.")
        break

    face_locations, face_names = sfr.detect_known_faces(frame)
    
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        if name != "Unknown":
            # Draw box and name with more visible colors and thickness
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 4)  # Even thicker green box
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            
            # Add status text
            status = "Detected"
            if name in detected_people:
                time_diff = datetime.now() - detected_people[name]["time"]
                status = f"Detected {time_diff.total_seconds():.1f}s ago"
            
            cv2.putText(frame, status, (left, bottom + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if name not in detected_faces:
                detected_faces.add(name)
                timestamp = datetime.now()
                image_path = os.path.join("detections", f"{name}_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
                cv2.imwrite(image_path, frame)
                
                # Track person
                detected_people[name] = {"time": timestamp}
                status_msg = f"Person detected at Camera 1: {name} at {timestamp.strftime('%H:%M:%S')}"
                print(status_msg)
                
                publish_detection(name, timestamp)
                publish_status(status_msg, name)
                
                send_telegram_message(f"Person detected at Camera 1: {name}\nTime: {timestamp.strftime('%H:%M:%S')}", image_path)

    # Add system status text
    cv2.putText(frame, "Camera 1 - Entry Point", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Camera 1", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop() 
