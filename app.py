from re import DEBUG, sub
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for, flash, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from flask_googlemaps import GoogleMaps, Map, icons
from dotenv import load_dotenv
from GPSPhoto import gpsphoto
import shutil
import random
import string
import os, sys
import logging
import torch
# import darknet
import colorsys
import subprocess
from glob import glob
import datetime, time
import cv2
# import imutils
import numpy as np
from threading import Thread
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

app = Flask(__name__)
load_dotenv()

UPLOAD_FOLDER = 'static/uploads/'
DOWNLOAD_FOLDER = 'static/downloads/'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'MP4'}

app.secret_key = "maderahano"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['GOOGLEMAPS_KEY'] = os.getenv("GOOGLE_MAP_KEY_API")

global imagenames
imagenames = []
upload_images = os.path.join(UPLOAD_FOLDER, 'images')
upload_videos = os.path.join(UPLOAD_FOLDER, 'videos')
download_images = os.path.join(DOWNLOAD_FOLDER, 'images')
download_videos = os.path.join(DOWNLOAD_FOLDER, 'videos')

model = torch.hub.load('yolo', 'custom', path='yolo/runs/train/exp6/weights/best.pt', source='local')  # local repo
# model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
GoogleMaps(app)

global link_RTMP
def generate_stream_keys(): # define the function and pass the length as argument  
    global link_RTMP
    length = 6
    result = ''.join((random.choice(string.ascii_lowercase) for x in range(length)))
    link_RTMP = 'rtmp://0.tcp.ap.ngrok.io:19336/live/' + result

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@app.route("/")
def main():
    return render_template('upload.html')

@app.route("/live")
def live():
    return render_template('live.html')

@app.route("/map")
def map():
    map = Map(
        identifier="view-map",
        lat=37.4419,
        lng=-122.1419,
        markers=[
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
             'lat': 37.4419,
             'lng': -122.1419,
             'infobox': "<b>Hello World</b>"
          },
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
             'lat': 37.4300,
             'lng': -122.1400,
             'infobox': "<b>Hello World from other place</b>"
          }
        ]
    )
    return render_template('map.html', map=map)

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route("/webcam")
def webcam():
    return render_template('webcam.html')

@app.route("/drone")
def drone():
    generate_stream_keys()
    return render_template('drone.html', linkRTMP=link_RTMP)

# IMAGE DETECTION

@app.route("/upload-images", methods=['POST'])
def upload_detection_images():
    if not request.method == "POST":
        return redirect(request.url)

    if 'uploadImageFiles' not in request.files:
        return redirect(request.url)
    
    global imagenames
    imagenames = []
    locations = []
    files = request.files.getlist('uploadImageFiles')   
    for file in files:
        if file and allowed_image_file(file.filename):
            filename = secure_filename(file.filename)
            imagenames.append(filename)
            file.save(os.path.join(upload_images, filename))
            locations.append(gpsphoto.getGPSData(os.path.join(upload_images, filename)))

            # YOLOv5 Using Pytorch Command
            img = ''
            img = upload_images + '/' + filename

            results = model(img)
            results.save()

            locationImage = 'runs/detect/exp/' + filename
            print(locationImage)
            detectionImage = cv2.imread(locationImage)
            font = cv2.FONT_HERSHEY_SIMPLEX
            org = (10, -50)
            fontScale = 4
            color = [(255,0,0), (255,128,0), (255,255,0), (0,255,0), (0,0,255), (128,0,255), (255,0,255)]
            print(type(color))
            thickness = 8
            idxColor = 0
            for idx, name in enumerate(results.pandas().xyxy[0].value_counts('name').index.tolist()):
                listOrg = list(org)
                listOrg[1] += 150
                org = tuple(listOrg)
                finalResult = cv2.putText(detectionImage, name + ' : ' + str(results.pandas().xyxy[0].value_counts('name')[idx]), org, font, fontScale, color[idxColor], thickness, cv2.LINE_AA)
                idxColor += 1

            cv2.imwrite(locationImage, finalResult)

            timestamp = os.listdir('runs/detect/')[0]
            shutil.move(os.path.join('runs/detect', timestamp), download_images)
            subprocess.run(['mv', os.path.join('exp', filename), '.'], cwd='static/downloads/images')
            subprocess.run(['rmdir', 'exp'], cwd='static/downloads/images')
            subprocess.run(['rm', '-rf', 'runs'])

            print("<==========Log Object Detection==========>")
            print(results.pandas().xyxy[0])
            print("\n")
            print("<==========Conclusion Object Detection==========>")
            print(results.pandas().xyxy[0].value_counts('name'))
            print("\n")

            # for idx, name in enumerate(results.pandas().xyxy[0].value_counts('name').index.tolist()):
            #     print('Key :', name)
            #     print('Values :', results.pandas().xyxy[0].value_counts('name')[idx])
            # results.pandas().xyxy[0]
            # results.pandas().xyxy[0].value_counts['name']

            # YOLOv5 Using Python Command
            # subprocess.run(['python', 'detect.py', '--weights', 'yolo/runs/train/exp6/weights/best.pt', '--source', os.path.join("../static/uploads/images/", filename),'--project', '../static/downloads', '--name', 'images'], cwd='yolo')
            # YOLOv4 Darknet Configuration
            # subprocess.run(['./darknet', 'detector', 'test', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/images/", filename), '-thresh 0.3', '-dont_show'], cwd='yolov4')
            # subprocess.run(['cp', 'predictions.jpg', '../static/downloads/images/'], cwd='yolov4')
            # subprocess.run(['cp', 'predictions.jpg', filename], cwd='static/downloads/images')
            # subprocess.run(['rm', 'predictions.jpg'], cwd='static/downloads/images')
            
            msg = 'Files successfully uploaded!'
        else:
            msg = 'Invalid Upload!'

    if len(locations[0]) > 0:
        map = Map(
            identifier="view-map",
            maptype='SATELLITE',
            style="height:600px;width:900px",
            lat=locations[0]['Latitude'],
            lng=locations[0]['Longitude'],
            markers=[(loc['Latitude'], loc['Longitude']) for loc in locations],
            fit_markers_to_bounds = True 
        )
    else:
        map = 0
    
    return render_template('upload.html', msg=msg, imagenames=imagenames, map=map)

@app.route("/download-images", methods=['GET'])
def download_detection_images():
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zf:
        for filename in imagenames:
            file = os.path.join(download_images, filename)
            zf.write(file, os.path.basename(file))
            
    memory_file.seek(0)

    return send_file(memory_file, download_name='all_images.zip', as_attachment=True)

@app.route("/download-image/<path:filename>", methods=['GET'])
def download_detection_image(filename):
    return send_from_directory(download_images, filename, as_attachment=True)

# VIDEO DETECTION

global fileVideoName

# @app.route("/upload-videos", methods=['POST'])
# def upload_detection_videos():
#     # global video, resultDetection
#     if not request.method == "POST":
#         return redirect(request.url)

#     if 'uploadVideoFiles' not in request.files:
#         return redirect(request.url)
    
#     files = request.files.getlist('uploadVideoFiles')   
#     video_names = []

#     for file in files:
#         if file and allowed_video_file(file.filename):
#             filename = secure_filename(file.filename)
#             video_names.append(filename)
#             file.save(os.path.join(upload_videos, filename))

#             # YOLOv5 Using Pytorch Command
#             locVid = ''
#             locVid = upload_videos + '/' +filename
#             video = cv2.VideoCapture(locVid)

#             if (video.isOpened()== False): 
#                 print("Error opening video stream or file")

#             saveVideo = os.path.sep.join(['static/downloads/videos/', filename])
#             fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
#             frame_width = int(video.get(3))
#             frame_height = int(video.get(4))
#             # Find OpenCV version
#             (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        
#             if int(major_ver)  < 3 :
#                 fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
#                 # print ("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
#             else :
#                 fps = video.get(cv2.CAP_PROP_FPS)
#                 # print ("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

#             resultDetection = cv2.VideoWriter(saveVideo, fourcc, fps, (frame_width, frame_height))
            
#             while(video.isOpened()):
#                 success, frame = video.read()
#                 if success:
#                     results = model(frame)
#                     detection = np.squeeze(results.render())

#                     print(results.pandas().xyxy[0])
#                     print(results.pandas().xyxy[0].value_counts('name'))

#                     time.sleep(0.05)
#                     resultDetection.write(detection)
#                 else:
#                     break
            
#             video.release()
#             resultDetection.release()

#             # YOLOv5 Using Python Command
#             # subprocess.run(['python', 'detect.py', '--weights', 'yolo/runs/train/exp6/weights/best.pt', '--source', os.path.join("../static/uploads/videos/", filename),'--project', '../static/downloads', '--name', 'videos'], cwd='yolo')
#             # YOLOv4 Darknet Configuration
#             # subprocess.run(['./darknet', 'detector', 'demo', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/videos/", filename), '-i', '0', '-out_filename', os.path.join("../static/downloads/videos/", filename), '-dont_show'], cwd='yolov4')
            
#             msg = 'Files successfully uploaded!'
#             print(msg)
#         else:
#             msg = 'Invalid Upload!'
    
#     return render_template('upload.html', msg=msg, videonames=video_names)

@app.route("/upload-videos", methods=['POST'])
def upload_detection_videos():
    global fileVideoName
    if not request.method == "POST":
        return redirect(request.url)

    if 'uploadVideoFiles' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('uploadVideoFiles')   
    video_names = []

    for file in files:
        if file and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            video_names.append(filename)
            fileVideoName = filename
            file.save(os.path.join(upload_videos, filename))
            
            msg = 'Files successfully uploaded!'
            print(msg)
        else:
            msg = 'Invalid Upload!'
    
    return render_template('upload.html', msg=msg, videonames=video_names)

def gen_video_frames():
    global fileVideoName

    # YOLOv5 Using Pytorch Command
    locVid = ''
    locVid = upload_videos + '/' + fileVideoName
    video = cv2.VideoCapture(locVid)

    if (video.isOpened()== False): 
        print("Error opening video stream or file")

    saveVideo = os.path.sep.join(['static/downloads/videos/', fileVideoName])
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    frame_width = int(video.get(3))
    frame_height = int(video.get(4))
    # Find OpenCV version
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

    if int(major_ver)  < 3 :
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
        # print ("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else :
        fps = video.get(cv2.CAP_PROP_FPS)
        # print ("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    resultDetection = cv2.VideoWriter(saveVideo, fourcc, fps, (frame_width, frame_height))
    
    while(video.isOpened()):
        success, frame = video.read()
        if success:
            results = model(frame)
            detection = np.squeeze(results.render())

            print(results.pandas().xyxy[0])
            print(results.pandas().xyxy[0].value_counts('name'))

            time.sleep(0.05)
            resultDetection.write(detection)
            try:                
                ret, buffer = cv2.imencode('.jpg', detection)
                detection = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + detection + b'\r\n')
            except Exception as e:
                pass
        else:
            break

    video.release()
    resultDetection.release()

@app.route('/display-video')
def display_video():
    return Response(gen_video_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/download-video/<path:filename>", methods=['GET'])
def download_detection_video(filename):
    return send_from_directory(download_videos, filename, as_attachment=True)
    
# WEBCAM DETECTION

global camera, capture_webcam, rec_frame_webcam, grey_webcam, switch_webcam, neg_webcam, rec_webcam, out_webcam
capture_webcam = 0
grey_webcam = 0
neg_webcam = 0
switch_webcam = 0
rec_webcam = 0

# Make Shots Directory to Save Pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

def record_webcam(out_webcam):
    global rec_frame_webcam
    while(rec_webcam):
        time.sleep(0.05)
        out_webcam.write(rec_frame_webcam)

def gen_webcam_frames():
    global out_webcam, capture_webcam, rec_frame_webcam
    while True:
        success, frame = camera.read()
        if success:
            results = model(frame)
            detection = np.squeeze(results.render())

            if(grey_webcam):
                detection = cv2.cvtColor(detection, cv2.COLOR_BGR2GRAY)
            if(neg_webcam):
                detection = cv2.bitwise_not(detection)
            if(capture_webcam):
                capture_webcam = 0
                now = datetime.datetime.now()
                p = os.path.sep.join(['static/webcam/images/', "shot_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, detection)
            if(rec_webcam):
                rec_frame_webcam = detection
                detection = cv2.putText(cv2.flip(detection,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 4)
                detection = cv2.flip(detection,1)

            try:                
                ret, buffer = cv2.imencode('.jpg', detection)
                detection = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + detection + b'\r\n')
            except Exception as e:
                pass
        else:
            pass
    
@app.route('/live-webcam')
def live_webcam():
    return Response(gen_webcam_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests-webcam', methods=['POST', 'GET'])
def tasks_webcam():
    global switch_webcam, camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture_webcam
            capture_webcam = 1
        elif request.form.get('grey') == 'Grey':
            global grey_webcam
            grey_webcam = not grey_webcam
        elif request.form.get('neg') == 'Negative':
            global neg_webcam
            neg_webcam = not neg_webcam
        elif request.form.get('stop') == 'Stop/Start':
            global camera
            if (switch_webcam == 1):
                switch_webcam = 0
                camera.release()
            else:
                camera = cv2.VideoCapture(0)
                switch_webcam = 1
        elif request.form.get('rec') == 'Start/Stop Recording':
            global rec_webcam, out_webcam
            rec_webcam = not rec_webcam
            if (rec_webcam):
                now = datetime.datetime.now()
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                p = os.path.sep.join(['static/webcam/videos/', "vid_{}.avi".format(str(now).replace(":",''))])
                out_webcam = cv2.VideoWriter(p, fourcc, 20.0, (640, 480))
                # Start New Thread for Recording the Video
                thread = Thread(target = record_webcam, args=[out_webcam,])
                thread.start()
            elif (rec_webcam == False):
                out_webcam.release()
    elif request.method == 'GET':
        return render_template('webcam.html')
    return render_template('webcam.html')

# DRONE DETECTION

global camera_drone, capture_drone, rec_frame_drone, grey_drone, switch_drone, neg_drone, rec_drone, out_drone
capture_drone = 0
grey_drone = 0
neg_drone = 0
switch_drone = 0
rec_drone = 0

# Make Shots Directory to Save Pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

def record_drone(out_drone):
    global rec_frame_drone
    while(rec_drone):
        time.sleep(0.05)
        out_drone.write(rec_frame_drone)

def gen_drone_frames():
    global out_drone, capture_drone, rec_frame_drone
    while True:
        success, frame = camera_drone.read()
        if success:
            results = model(frame)
            detection = np.squeeze(results.render())

            if(grey_drone):
                detection = cv2.cvtColor(detection, cv2.COLOR_BGR2GRAY)
            if(neg_drone):
                detection = cv2.bitwise_not(detection)
            if(capture_drone):
                capture_drone = 0
                now = datetime.datetime.now()
                p = os.path.sep.join(['static/drone/images/', "shot_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, detection)
            if(rec_drone):
                rec_frame_drone = detection
                detection = cv2.putText(cv2.flip(detection,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 4)
                detection = cv2.flip(detection,1)

            try:                
                ret, buffer = cv2.imencode('.jpg', detection)
                detection = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + detection + b'\r\n')
            except Exception as e:
                pass
        else:
            pass
    
@app.route('/live-drone')
def live_drone():
    return Response(gen_drone_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests-drone', methods=['POST', 'GET'])
def tasks_drone():
    global switch_drone, camera_drone
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture_drone
            capture_drone = 1
        elif request.form.get('grey') == 'Grey':
            global grey_drone
            grey_drone = not grey_drone
        elif request.form.get('neg') == 'Negative':
            global neg_drone
            neg_drone = not neg_drone
        elif request.form.get('stop') == 'Stop/Start':
            global camera_drone
            if (switch_drone == 1):
                switch_drone = 0
                camera_drone.release()
            else:
                camera_drone = cv2.VideoCapture(link_RTMP)
                switch_drone = 1
        elif request.form.get('rec') == 'Start/Stop Recording':
            global rec_drone, out_drone
            rec_drone = not rec_drone
            if (rec_drone):
                now = datetime.datetime.now()
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                p = os.path.sep.join(['static/drone/videos/', "vid_{}.avi".format(str(now).replace(":",''))])
                out_drone = cv2.VideoWriter(p, fourcc, 20.0, (640, 480))
                # Start New Thread for Recording the Video
                thread = Thread(target = record_drone, args=[out_drone,])
                thread.start()
            elif (rec_drone == False):
                out_drone.release()
    elif request.method == 'GET':
        return render_template('drone.html', linkRTMP=link_RTMP)
    return render_template('drone.html', linkRTMP=link_RTMP)