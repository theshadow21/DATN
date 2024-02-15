from flask import Flask, render_template, Response, request, send_from_directory, jsonify, session, redirect,url_for, current_app, send_file
from camera import VideoCamera
from imutils import paths
import face_recognition
import pickle 
import cv2
import os
import json
import re
import threading
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import shutil
from datetime import timedelta

pi_camera = VideoCamera(flip=False) # flip pi camera if upside down.

# App Globals (do not edit)
app = Flask(__name__)
app.secret_key = '8d43ce30-9052-42a7-9e9d-847c53be299e'
app.permanent_session_lifetime = timedelta(minutes=5)

#============================= Global Variables =======================#
configuration_path = os.path.join('./configuration.json')
video_path = os.path.join('./video')
image_path = os.path.join('./picture')

email =""
start_time = ""
end_time = ""
current_name = ""
admin_name = ""
admin_pass = ""
MAX_ATTEMPTS = 3
is_train_model = False
is_NoStreaming = True
is_updateConfig = False

#============================= App routes =============================#
@app.route('/')
def index():
    attempts = session.get('failed_attempts', 0)
    if attempts >= MAX_ATTEMPTS:
        return render_template('index.html', error='Too many failed login attempts, please try after 5m',disable='true')
    elif attempts > 0 :
        return render_template('index.html', error=f'Invalid username or password, login fail {attempts}')
    else:
        return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    global is_NoStreaming
    is_NoStreaming = False
    return Response(gen(pi_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Call stop_streaming to make sure that streaming stop
@app.route('/stopStreaming')
def stop_streaming():
    global is_NoStreaming
    is_NoStreaming = True
    return jsonify({'status':'OK'}),200

# Take a photo when pressing camera button
@app.route('/takePicture')
def take_picture():
    owner_pic_path = './dataset/'+current_name+ '/'
    pi_camera.take_picture(owner_pic_path)
    return jsonify({'status':'OK'}),200

@app.route('/streaming')
def streaming():
    global is_streaming
    is_streaming = True
    print('[INFO] App streaming')
    if session.get('logged_in'):
        return render_template('streaming.html')
    else:
        return render_template('index.html')

@app.route('/recording')
def recording():
    print('[INFO] App recording')
    if session.get('logged_in'):
        return render_template('recording.html')
    else:
        return render_template('index.html')

@app.route('/setting')
def setting():
    print('[INFO] App setting')
    if session.get('logged_in'):
        return render_template('setting.html')
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Kiểm tra thông tin đăng nhập
        if username == admin_name and password == admin_pass:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            session['failed_attempts'] = 0
            return redirect(url_for('streaming'))
        else:
            attempts = session.get('failed_attempts', 0) + 1
            session['failed_attempts'] = attempts
            if attempts >= MAX_ATTEMPTS:
                return render_template('index.html', error='Too many failed login attempts, please try after 5m',disable='true')
            else:
                return render_template('index.html', error=f'Invalid username or password, login fail {attempts}')

    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/listVideo')
def listVideo():
    print('[INFO] App get listVideo')
    _list_video = getListVideo()
    return jsonify({'data': _list_video})

@app.route('/trainModel')
def trainModel():
    print('[INFO] App train model')
    trainModel()
    return jsonify({'status':'OK'}),200

@app.route('/settingTimes', methods=['GET'])
def settingTimes():
    print('[INFO] setting time')
    global is_updateConfig
    start_time = request.args.get('startTime')
    stop_time  = request.args.get('stopTime')
    update_config_time(start_time,stop_time)
    is_updateConfig = True
    return 'OK',200

@app.route('/settingOwner', methods=['GET'])
def settingOwner():
    global is_updateConfig
    print('[INFO] App Setting owner')
    _user_name = request.args.get('name')
    _email = request.args.get('email')
    if(update_config_owner(_user_name,_email)):
        is_updateConfig = True
        return 'OK',200
    else:
        return 'Owner exists',404

@app.route('/display_video', methods=['GET'])
def display_video():
    _video_name = request.args.get('video_name')
    _video = video_path + '/' + _video_name
    print('[INFO] display_video' , _video )
    return Response(generate_frames(_video), mimetype='multipart/x-mixed-replace; boundary=frame')
#========================================================================================#
@app.route("/stream_video_1", methods=["GET"])
def video():
    _video_name = request.args.get('video_name')
    headers = request.headers
    if not "range" in headers:
        return current_app.response_class(status=400)

    _video_dir = os.path.abspath(os.path.join("./video", _video_name))
    size = os.stat(_video_dir)
    size = size.st_size

    chunk_size = (10 ** 6) * 3 #1000kb makes 1mb * 3 = 3mb (this is based on your choice)
    start = int(re.sub("\D", "", headers["range"]))
    end = min(start + chunk_size, size - 1)

    content_length = end - start + 1

    def get_chunk(video_dir, start, chunk_size):
        with open(video_dir, "rb") as f:
            f.seek(start)
            chunk = f.read(chunk_size)
        return chunk

    content_range = "bytes " + str(start) + "-" + str(end) + "/" + str(size)
    headers = {
        "Content-Range": content_range,
        "Accept-Ranges": "bytes",
        "Content-Length": content_length,
        "Content-Type": "video/x-msvideo",
    }

    return current_app.response_class(get_chunk(_video_dir, start,chunk_size), 206, headers)

@app.route('/deleteVideo', methods=['GET'])
def delete_video():
    _video_name = request.args.get('video_name')
    if (deleteVideo(_video_name)):
        return jsonify({'status':'OK'}),200
    else:
        return jsonify({'status':'Error'}),400

@app.route('/getFreeDisk', methods=['GET'])
def get_free_disk():
    _free_disk = get_free_space()
    return jsonify({'data': _free_disk})

@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response

@app.route('/stream_video', methods=['GET'])
def get_file():
    _video_name = request.args.get('video_name')
    _video_dir = os.path.abspath(os.path.join("./video", _video_name))
    range_header = request.headers.get('Range', None)
    byte1, byte2 = 0, None
    if range_header:
        match = re.search(r'(\d+)-(\d*)', range_header)
        groups = match.groups()

        if groups[0]:
            byte1 = int(groups[0])
        if groups[1]:
            byte2 = int(groups[1])
       
    chunk, start, length, file_size = get_chunk(byte1, byte2, _video_dir)
    resp = Response(chunk, 206, mimetype='video/mp4',
                      content_type='video/mp4', direct_passthrough=True)
    resp.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, start + length - 1, file_size))
    return resp

@app.route('/get_video_file', methods=['GET'])
def get_video_file():
    _video_name = request.args.get('video_name')
    _video_dir = os.path.abspath(os.path.join("./video", _video_name))
    mime_type = 'video/mp4'
    return send_file(_video_dir, mimetype=mime_type)

#============================= functions =============================#
def gen(camera):
    #get camera frame
    print("[INFO] Start streaming camera")
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    #End while
    print("[INFO] Stop streaming camera")

def generate_frames(video_path):
    print("[INFO] Streaming video")
    video_capture = cv2.VideoCapture(video_path)
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def get_chunk(byte1=None, byte2=None, video_dir=None):
    file_size = os.stat(video_dir).st_size
    start = 0
    
    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start

    with open(video_dir, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk, start, length, file_size


def read_config():
    print('[Info] reading config file')
    global current_name
    global email
    global start_time
    global end_time
    global admin_name
    global admin_pass
    with open(configuration_path, 'r') as file:
        config = json.load(file)
    
    #Get global variables
    current_name = config["name"]
    email        = config["email"]
    start_time   = config["time"]["start_time"]
    end_time     = config["time"]["end_time"]
    admin_name     = config["account"]["administrator"]["email"]
    admin_pass     = config["account"]["administrator"]["password"]
    print('[Info] config file: ',current_name," ",email," ",start_time," ",end_time)

def update_config_owner(owner, email):
    print('[Info] updating config owner')
    ret_val = False
    with open(configuration_path, 'r') as file:
        config = json.load(file)
    
    config['email'] = email
    if(not_exists_name(owner)):
        config['name'] = owner
        ret_val = True

    with open(configuration_path, 'w') as file:
        json.dump(config,file,indent=2)
    
    return ret_val
    

def not_exists_name(new_name):
    new_path = "./dataset/"+new_name
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        return True
    else:
        return False


def update_config_time(start_time, end_time):
    print('[Info] updating config time')
    with open(configuration_path, 'r') as file:
        config = json.load(file)

    config['time']['start_time'] = start_time
    config['time']['end_time'] = end_time

    with open(configuration_path,'w') as file:
        json.dump(config,file,indent=2)

# Get free disk
def get_free_space(path="/"):
    # Get disk usage statistics
    usage = shutil.disk_usage(path)

    total_space = usage.total  # Total disk space in bytes
    free_space = usage.free    # Free disk space in bytes
    used_space = usage.used    # Used disk space in bytes

    # Convert bytes to human-readable sizes (optional)
    total_space_gb = total_space / (2**30)  # Convert bytes to gigabytes
    free_space_gb = free_space / (2**30)
    used_space_gb = used_space / (2**30)

    return {
        "total_space": total_space,
        "free_space": free_space,
        "used_space": used_space,
        "total_space_gb": total_space_gb,
        "free_space_gb": free_space_gb,
        "used_space_gb": used_space_gb
    }

def save_video():
    print('[Info] Saving video')

def getListVideo():
    print('[Info] get list video')
    _list_video_path = os.listdir(video_path)
    # print('List', _list_video_path)
    return _list_video_path

def trainModel():
    global is_NoStreaming
    # our images are located in the dataset folder
    print("[INFO] ============> Starting train model <================")
    imagePaths = list(paths.list_images("dataset"))

    # initialize the list of known encodings and known names
    knownEncodings = []
    knownNames = []
    
    is_NoStreaming = False
    # loop over the image paths
    for (i, imagePath) in enumerate(imagePaths):
        # extract the person name from the image path
        print("[INFO] processing image {}/{}".format(i + 1,len(imagePaths)))
        name = imagePath.split(os.path.sep)[-2]

        # load the input image and convert it from RGB (OpenCV ordering)
        # to dlib ordering (RGB)
        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input image
        boxes = face_recognition.face_locations(rgb,
            model="hog")

        # compute the facial embedding for the face
        encodings = face_recognition.face_encodings(rgb, boxes)

        # loop over the encodings
        for encoding in encodings:
            # add each encoding + name to our set of known names and
            # encodings
            knownEncodings.append(encoding)
            knownNames.append(name)

    # dump the facial encodings + names to disk
    print("[INFO] serializing encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    f = open("encodings.pickle", "wb")
    f.write(pickle.dumps(data))
    f.close()
    print("[INFO] ============> Finish train model <================")
    is_NoStreaming = True

def sendMail(): 
    # Set the sender email and password and recipient email
    strange_images = image_path+"/stranger_people.jpg" 
    print("[INFO] ============> Send email <================")
    from_email_addr = "sendersmarthome@gmail.com"
    from_email_password = "xxke ueoq onjo uthl"
    # to_email_addr="xuantuanncth1@gmail.com"
    email_subject = "[WARNING!] Có người lạ mặt!"
    email_body = "Cảnh báo có người lạ mặt trong sân nhà bạn!"
    if email != "":
        to_email_addr = email
    else:
        to_email_addr = "hieutran21042k@gmail.com"
    # create a multipart message
    msg = MIMEMultipart()
    
    # set the email body
    msg.attach(MIMEText(email_body, 'plain'))
    
    # set sender and recipient
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr
    
    # set your email subject
    msg['Subject'] = email_subject
    
    # attach the image
    with open(strange_images, 'rb') as image_file:
        image_data = image_file.read()
        image = MIMEImage(image_data, name="stranger_people.jpg")
        msg.attach(image)
    
    # connect to server and send email
    # edit this line with your provider's SMTP server details
    server = smtplib.SMTP('smtp.gmail.com', 587)
    
    # comment out this line if your provider doesn't use TLS
    server.starttls()
    
    server.login(from_email_addr, from_email_password)
    server.send_message(msg)
    server.quit()
    
    print('Email sent')
# face_detect(is_NoStreaming,is_updateConfig,start_time,end_time)
def face_detect():
    print("Start face_detect")
    global is_updateConfig
    while True:
        if is_NoStreaming:
            pi_camera.face_detect(start_time, end_time)

        if pi_camera.check_sendMail() :
            sendMail()
            pi_camera.clear_flag_mail()
        if is_updateConfig:
            print("[INFO] Face_detet(): is_updateConfig = True")
            read_config()
            is_updateConfig = False

def deleteVideo(video_name):
    _video_path = video_path+"/"+video_name
    if os.path.exists(_video_path):
        os.remove(_video_path)
        return True
    else:
        return False

def statApplications():
    app.run(host='0.0.0.0', port =5000, debug=False, threaded=True)

def startFaceDetection():
    face_detect(start_time,end_time)

if __name__ == '__main__':
    read_config()
    # face_detect(start_time,end_time)
    appThread = threading.Thread(target=statApplications)
    faceThread = threading.Thread(target=face_detect)

    appThread.start()
    faceThread.start()

    appThread.join()
    faceThread.join()

