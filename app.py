from re import DEBUG, sub
from flask import Flask, render_template, request, redirect, send_file, url_for, flash, jsonify, Response
from werkzeug.utils import secure_filename, send_from_directory
import random
import os, sys
import darknet
import colorsys
import subprocess
import datetime, time
import cv2
import imutils
import numpy as np
from threading import Thread

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'MP4'}

app.secret_key = "maderahano"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

upload_images = os.path.join(UPLOAD_FOLDER, 'images')
upload_videos = os.path.join(UPLOAD_FOLDER, 'videos')

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@app.route("/")
def main():
    return render_template('index.html')

# IMAGE DETECTION

@app.route("/detect-image", methods=['POST'])
def detect_image():
    if not request.method == "POST":
        return
    
    if 'file' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    
    files = request.files.getlist('file')
    fileNames = []
    errors = {}
    success = False

    for file in files: 
        if file and allowed_image_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_images, filename))
            fileNames.append(filename)
            success = True
            subprocess.run(['./darknet', 'detector', 'test', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/images/", filename), '-thresh 0.3', '-dont_show'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', '../static/downloads/images/'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', filename], cwd='static/downloads/images')
            subprocess.run(['rm', 'predictions.jpg'], cwd='static/downloads/images')
        else:
            errors[file.filename] = 'file type is not allowed'
    
    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 206
        return resp
    if success:
        resp = jsonify({'message' : "Files successfully uploaded"})
        resp.status_code = 201
        return render_template('index.html', imagenames=fileNames) 
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp
    
# @app.route("/detect-image/<filename>")
# def display_images(filename):
#     print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='uploads/images/' + filename), code=301)

# VIDEO DETECTION

@app.route("/detect-video", methods=['POST'])
def detect_video():
    if not request.method == "POST":
        return
    
    if 'file' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    
    files = request.files.getlist('file')
    fileNames = []
    errors = {}
    success = False

    for file in files: 
        if file and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_videos, filename))
            fileNames.append(filename)
            success = True
            subprocess.run(['./darknet', 'detector', 'demo', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/videos/", filename), '-i', '0', '-out_filename', os.path.join("../static/downloads/videos/", filename), '-dont_show'], cwd='yolov4')
        else:
            errors[file.filename] = 'file type is not allowerd'
    
    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 206
        return resp
    if success:
        resp = jsonify({'message' : "Files successfully uploaded"})
        resp.status_code = 201
        return render_template('index.html', videonames=fileNames) 
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp
    
# WEBCAM DETECTION

global capture, rec_frame, grey, switch, neg, rec, out, trash
trash = 0
capture = 0
grey = 0
neg = 0
switch = 0
rec = 0

# yolo variable

global metaMain, netMain, altNames
netMain = None
metaMain = None
altNames = None

# Make Shots Directory to Save Pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

camera = cv2.VideoCapture(0)

def record(out):
    global rec_frame
    while(rec):
        time.sleep(0.05)
        out.write(rec_frame)

def detect_webcam_trash(frame):
    global start_x, start_y, box_width, box_height, label
    start_x = 0
    start_y = 0
    box_width = 0
    box_height = 0
    label = 0

    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    
    frame_blob = cv2.dnn.blobFromImage(frame, 1 / 255, (416, 416), swapRB=True, crop=False)

    with open("yolov4/data/obj.names","r", encoding="utf-8") as f:
        labels = f.read().strip().split("\n")

    colors = ["0,255,255", "0,0,255", "255,0,0", "255,255,0", "0,255,0"]
    colors = [np.array(color.split(",")).astype("int") for color in colors]
    colors = np.array(colors)
    colors = np.tile(colors, (18, 1))

    yolo_config_path = "yolov4/cfg/trash.cfg"
    yolo_weights_path = "yolov4/backup/trash/training/trash_best.weights"

    net = cv2.dnn.readNetFromDarknet(yolo_config_path, yolo_weights_path)
    layers = net.getLayerNames()

    output_layer = [layers[i - 1] for i in net.getUnconnectedOutLayers()]
    net.setInput(frame_blob)
    detection_layers = net.forward(output_layer)

    ids_list = []
    boxes_list = []
    confidences_list = []

    for detection_layer in detection_layers:
        for object_detection in detection_layer:

            scores = object_detection[5:]
            predicted_id = np.argmax(scores)
            confidence = scores[predicted_id]

            if confidence > 0.35:
                
                label = labels[predicted_id]
                bounding_box = object_detection[0:4] * np.array([frame_width, frame_height, frame_width, frame_height])
                (box_center_x, box_center_y, box_width, box_height) = bounding_box.astype("int")

                start_x = int(box_center_x - (box_width / 2))
                start_y = int(box_center_y - (box_height / 2))

                ids_list.append(predicted_id)
                confidences_list.append(float(confidence))
                boxes_list.append([start_x, start_y, int(box_width), int(box_height)])
            max_ids = cv2.dnn.NMSBoxes(boxes_list, confidences_list, 0.5, 0.4)

    for max_id in max_ids:
        max_class_id = max_id[0]
        box = boxes_list[max_class_id]

        start_x = box[0]
        start_y = box[1]
        box_width = box[2]
        box_height = box[3]

        predicted_id = ids_list[max_class_id]
        label = labels[predicted_id]
        confidence = confidences_list[max_class_id]

    end_x = start_x + box_width
    end_y = start_y + box_height

    box_color = colors[predicted_id]
    box_color = [int(each) for each in box_color]
    label = "{}: {:.2f}%".format(label, confidence * 100)
    print("predicted object {}".format(label))

    cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), box_color, 2)
    cv2.putText(frame, label, (start_x, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

    return frame

def gen_webcam_frames():
    global out, capture, rec_frame
    while True:
        success, frame = camera.read()
        if success:
            if(trash):
                frame = detect_webcam_trash(frame)
            if(grey):
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if(neg):
                frame = cv2.bitwise_not(frame)
            if(capture):
                capture = 0
                now = datetime.datetime.now()
                p = os.path.sep.join(['static', "shot_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
            if(rec):
                rec_frame = frame
                frame = cv2.putText(cv2.flip(frame,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 4)
                frame = cv2.flip(frame,1)

            try:                
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
        else:
            pass
    
@app.route('/live-webcam')
def live_webcam():
    return Response(gen_webcam_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests', methods=['POST', 'GET'])
def tasks():
    global switch, camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture = 1
        elif request.form.get('trash') == 'Trash':
            global trash
            trash = not trash
            if (trash):
                time.sleep(4)
        elif request.form.get('grey') == 'Grey':
            global grey
            grey = not grey
        elif request.form.get('neg') == 'Negative':
            global neg
            neg = not neg
        elif request.form.get('stop') == 'Stop/Start':
            if (switch == 1):
                switch = 0
                camera.release()
                cv2.destroyAllWindows()
            else:
                camera = cv2.VideoCapture(0)
                switch = 1
        elif request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec = not rec
            if (rec):
                now = datetime.datetime.now()
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter('vid_{}.avi'.format(str(now).replace(":",'')), fourcc, 20.0, (640, 480))
                # Start New Thread for Recording the Video
                thread = Thread(target = record, args=[out,])
                thread.start()
            elif (rec == False):
                out.release()
    elif request.method == 'GET':
        return render_template('index.html')
    return render_template('index.html')

camera.release()
cv2.destroyAllWindows()

# @app.route('/detect-video/<filename>')
# def display_videos(filename):
#     print('display_video filename: ' + filename)
#     return redirect(url_for('static', filename='uploads/videos/' + filename), code=301)

# @app.route("/opencam", methods=['GET'])
# def opencam():
#     print("here")
#     subprocess.run(['python3', 'detect.py', '--source', '0'])
#     return "done"
    
# @app.route('/return-files', methods=['GET'])
# def return_file():
#     obj = request.args.get('obj')
#     loc = os.path.join("runs/detect", obj)
#     print(loc)
#     try:
#         return send_file(os.path.join("runs/detect", obj), attachment_filename=obj)
#         # return send_from_directory(loc, obj)
#     except Exception as e:
#         return str(e)