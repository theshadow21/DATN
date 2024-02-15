PICamera = False

import cv2 as cv
if PICamera:
    from imutils.video.pivideostream import PiVideoStream
else:
    from imutils.video.videostream import VideoStream
import imutils
from imutils import paths
import face_recognition
import pickle 
import time
from datetime import datetime
import numpy as np

#Determine faces from encodings.pickle file model created from train_model.py 
encodingsP = "encodings.pickle" 
# load the known faces and embeddings along with OpenCV's Haar # cascade for face detection 
print("[INFO] loading encodings + face detector...") 
data_model = pickle.loads(open(encodingsP, "rb").read()) 


class VideoCamera(object):
    def __init__(self, flip = False, file_type  = ".jpg", photo_string= "stream_photo", video_type=".avi"):
        if PICamera:
            self.vs = PiVideoStream().start()
        else:
            self.vs = VideoStream().start()
        self.flip = flip # Flip frame vertically
        self.file_type = file_type # image type i.e. .jpg
        self.video_type = video_type
        self.photo_string = photo_string # Name to save the photo
        self.mail_counter = 0
        self.isSendEmail = False
        self.out = None
        self.is_firstSendMail = 0 #Define check if is first send mail
        time.sleep(2.0)

    def __del__(self):
        self.vs.stop()

    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(frame, 0)
        return frame

    def get_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        ret, jpeg = cv.imencode(self.file_type, frame)
        self.previous_frame = jpeg
        return jpeg.tobytes()

    # Take a photo, called by camera button
    def take_picture(self, path):
        print("[INFO] Take a picture")
        frame = self.flip_if_needed(self.vs.read())
        ret, image = cv.imencode(self.file_type, frame)
        today_date = datetime.now().strftime("%m%d%Y-%H%M%S") # get current time
        if path != "":
            file_path = path + f"{self.photo_string}_{today_date}{self.file_type}"
            print("File path: " + file_path)
        else:
            file_path = f"./picture/stranger_people{self.file_type}"
        cv.imwrite(file_path,frame)

    def check_time(self, start, end):
        _start_time = datetime.strptime(start, '%H:%M').time()
        _end_time = datetime.strptime(end, '%H:%M').time()
        current_time = datetime.now().time()
        if (_start_time < current_time) and ( current_time < _end_time ):
            return True
        else:
            return False

    def start_recording(self):
        print("[INFO] Starting recording")
        today_date = datetime.now().strftime("%H_%M_%d%m%Y") # get current time
        video_path = f"./video/{today_date}{self.video_type}"
        print("[INFO] Video path: ", video_path)
        fourcc = cv.VideoWriter_fourcc(*'XVID')  # You can change the codec as needed
        if PICamera:
            resolution = self.vs.resolution
        else:
            resolution=(320, 240)
        self.out = cv.VideoWriter(video_path, fourcc, 20.0, resolution)  # Adjust parameters accordingly
    
    def stop_recording(self):
        if self.out:
            print("[INFO] Stop recording")
            self.out.release()
            self.out = None

    def check_sendMail(self):
        if self.is_firstSendMail == 1:
            self.is_firstSendMail = 2
            return True
        if self.mail_counter > 5:
            print("[INFO] Check send mail: Send")
            return True
        else:
            return False
    
    def clear_flag_mail(self):
        self.mail_counter = 0
    # Detect faces
    def face_detect(self, start_time, end_time):
        frame = self.flip_if_needed(self.vs.read())
        if (self.check_time(start_time,end_time)):
            # Record video while face is detected
            if not self.out:
                self.start_recording()

            # Write the frame to the video file
            self.out.write(frame)
        else:
            self.stop_recording()
            
        # Detect the fce boxes 
        boxes = face_recognition.face_locations(frame)
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(frame, boxes)
        names = []
        print("Beginning face detection")
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data_model["encodings"],encoding)
            name = "Unknown" #if face is not recognized, then print Unknown
            if True in matches:
                print("Co nguoi quen")
                self.is_firstSendMail = 0
            else:
                self.take_picture("")
                print("Nguoi la xuat hien")
                if self.is_firstSendMail == 0:
                    self.is_firstSendMail = 1
                else:
                    self.mail_counter += 1

