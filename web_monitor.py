from flask import Flask, render_template, Response
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from queue import Queue
import threading

app = Flask(__name__)

# Message queue for storing recent messages
message_queue = Queue(maxsize=100)

# MQTT setup
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_USERNAME = "hivemq.webclient.1747421508183"
MQTT_PASSWORD = "6uP8c#GY*voAV&x75.dX"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Web Monitor connected to HiveMQ!")
        client.subscribe([("face_detection/camera1", 0), 
                         ("face_detection/camera2", 0),
                         ("face_detection/status", 0)])
    else:
        print(f"Failed to connect to HiveMQ, return code: {rc}")

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_queue.put({
            "timestamp": timestamp,
            "topic": message.topic,
            "data": data
        })
    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_messages')
def get_messages():
    messages = []
    while not message_queue.empty():
        messages.append(message_queue.get())
    return json.dumps(messages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 