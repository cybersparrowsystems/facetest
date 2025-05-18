# import cv2
# from simple_facerec import SimpleFacerec

# # Initialize face recognizer and load known faces
# sfr = SimpleFacerec()
# sfr.load_encoding_images("C:\Users\Subhash\Downloads\NMIT_1\facetest\images")  # Make sure this folder contains images named as <name>.jpg

# # Start camera (0 is usually the default laptop webcam)
# # cap = cv2.VideoCapture(0)
# cap=cv2.VideoCapture(0)
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame from camera.")
#         break

#     # Detect faces
#     face_locations, face_names = sfr.detect_known_faces(frame)
#     # Draw boxes and names
#     for (top, right, bottom, left), name in zip(face_locations, face_names):
#         cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#         cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

#     cv2.imshow("Camera Face Recognition Test", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         print("Exiting...")
#         break

# cap.release()
# cv2.destroyAllWindows()
import cv2
from simple_facerec import SimpleFacerec

# Initialize face recognizer and load known faces
sfr = SimpleFacerec()
sfr.load_encoding_images("images/")  # Relative path to the images folder

# Start camera (0 is usually the default laptop webcam)
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from camera.")
        break

    # Detect faces
    face_locations, face_names = sfr.detect_known_faces(frame)
    # Draw boxes and names
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Camera Face Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting...")
        break

cap.release()
cv2.destroyAllWindows()