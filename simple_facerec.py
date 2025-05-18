# import cv2
# import numpy as np
# import face_recognition
# import os

# class SimpleFacerec:
#     def _init_(self):
#         self.known_face_encodings = []
#         self.known_face_names = []

#     def load_encoding_images(self, images_path):
#         """
#         Load encoding images from path
#         :param images_path:
#         :return:
#         """
#         # Load Images
#         images_path = os.listdir(images_path)
#         print("{} encoding images found.".format(len(images_path)))

#         # Store image encoding and names
#         for img_path in images_path:
#             if img_path.endswith('.jpg') or img_path.endswith('.png'):
#                 face_img = face_recognition.load_image_file(f"face-recognition/images/{img_path}")
#                 face_encoding = face_recognition.face_encodings(face_img)[0]

#                 self.known_face_encodings.append(face_encoding)
#                 self.known_face_names.append(img_path.split('.')[0])

#         print("Encoding images loaded")

#     def detect_known_faces(self, frame):
#         """
#         Detect faces in frame
#         :param frame:
#         :return:
#         """
#         small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
#         rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

#         # Find all the faces and face encodings in the current frame of video
#         face_locations = face_recognition.face_locations(rgb_small_frame)
#         face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

#         face_names = []
#         for face_encoding in face_encodings:
#             # See if the face is a match for the known face(s)
#             matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
#             name = "Unknown"

#             # Use the known face with the smallest distance to the new face
#             face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
#             best_match_index = np.argmin(face_distances)
#             if matches[best_match_index]:
#                 name = self.known_face_names[best_match_index]

#             face_names.append(name)

#         # Convert back to original size
#         face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in face_locations]

#         return face_locations, face_names
import cv2
import numpy as np
import face_recognition
import os

class SimpleFacerec:
    def __init__(self):  # Fixed typo: _init_ to __init__
        self.known_face_encodings = []
        self.known_face_names = []

    def load_encoding_images(self, images_path):
        """
        Load encoding images from path
        :param images_path:
        :return:
        """
        # Load Images
        images_list = os.listdir(images_path)
        print("{} encoding images found.".format(len(images_list)))

        # Store image encoding and names
        for img_path in images_list:
            if img_path.endswith('.jpg') or img_path.endswith('.png'):
                # Construct the full path using the provided images_path
                full_img_path = os.path.join(images_path, img_path)
                face_img = face_recognition.load_image_file(full_img_path)
                face_encoding = face_recognition.face_encodings(face_img)[0]

                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(img_path.split('.')[0])

        print("Encoding images loaded")

    def detect_known_faces(self, frame):
        """
        Detect faces in frame
        :param frame:
        :return:
        """
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]

            face_names.append(name)

        # Convert back to original size
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in face_locations]

        return face_locations, face_names