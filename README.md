
# Dual Camera Face Recognition and Tracking System

A real-time face recognition system that tracks individuals across two cameras using MQTT for communication and Telegram for notifications.

## Features

- Real-time face recognition using OpenCV and face_recognition library
- Dual camera tracking system
- MQTT-based communication between cameras
- Telegram notifications for:
  - Person detection
  - Safety alerts
  - Status updates
- Automatic alert system for delayed crossings
- Visual status display on camera feeds
- Image capture and storage of detections

## Prerequisites

- Python 3.7 or higher
- OpenCV
- face_recognition library
- paho-mqtt
- requests
- HiveMQ account
- Telegram bot token

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create an `images` folder and add face images:
```
images/
    person1.jpg
    person2.jpg
    ...
```

4. Create a `detections` folder for captured images:
```bash
mkdir detections
```

## Configuration

1. Update Telegram settings in both `camera1.py` and `camera2.py`:
```python
BOT_TOKEN = "your_telegram_bot_token"
CHAT_ID = "your_chat_id"
```

2. Update MQTT settings in both camera files:
```python
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_USERNAME = "your_hivemq_username"
MQTT_PASSWORD = "your_hivemq_password"
```

## Usage

1. Start Camera 1 (Entry Point):
```bash
python camera1.py
```

2. Start Camera 2 (Exit Point):
```bash
python camera2.py
```

3. Press 'q' to quit either camera.

## System Behavior

- Camera 1 (Entry Point):
  - Detects and recognizes faces
  - Sends detection messages to Camera 2
  - Tracks time until person reaches Camera 2
  - Sends alerts if person doesn't reach Camera 2 within 10 seconds

- Camera 2 (Exit Point):
  - Receives detection messages from Camera 1
  - Confirms when person reaches exit point
  - Sends success messages back to Camera 1
  - Updates status display

## MQTT Topics

- `face_detection/camera1`: Messages from Camera 1
- `face_detection/camera2`: Messages from Camera 2
- `face_detection/status`: Status updates and alerts

## Message Formats

1. Detection Message:
```json
{
    "name": "person_name",
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "camera": "camera1/camera2",
    "type": "detection",
    "status": "detected"
}
```

2. Status Message:
```json
{
    "message": "status message text",
    "type": "status",
    "name": "person_name",
    "camera": "camera1/camera2",
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "status": "tracking/detected/alert"
}
```

3. Alert Message:
```json
{
    "message": "alert message text",
    "type": "alert",
    "name": "person_name",
    "camera": "camera1/camera2",
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "status": "alert"
}
```

## Troubleshooting

1. Camera Access Issues:
   - Try different camera indices (0, 1, 2)
   - Check camera permissions
   - Ensure no other application is using the camera

2. MQTT Connection Issues:
   - Verify HiveMQ credentials
   - Check internet connection
   - Ensure port 1883 is not blocked

3. Face Recognition Issues:
   - Ensure clear, well-lit images in the `images` folder
   - Check image format (JPG/PNG)
   - Verify face_recognition library installation

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

