from re import DEBUG, sub
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for, flash, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from flask_googlemaps import GoogleMaps, Map, icons
from dotenv import load_dotenv
from GPSPhoto import gpsphoto
import random
import os, sys
import logging
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

GoogleMaps(app)

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@app.route("/")
def main():
    return render_template('index.html')

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
    return render_template('drone.html')

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

            subprocess.run(['./darknet', 'detector', 'test', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/images/", filename), '-thresh 0.3', '-dont_show'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', '../static/downloads/images/'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', filename], cwd='static/downloads/images')
            subprocess.run(['rm', 'predictions.jpg'], cwd='static/downloads/images')
            
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

@app.route("/upload-videos", methods=['POST'])
def upload_detection_videos():
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
            file.save(os.path.join(upload_videos, filename))

            subprocess.run(['./darknet', 'detector', 'demo', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/videos/", filename), '-i', '0', '-out_filename', os.path.join("../static/downloads/videos/", filename), '-dont_show'], cwd='yolov4')
            
            msg = 'Files successfully uploaded!'
        else:
            msg = 'Invalid Upload!'
    
    return render_template('upload.html', msg=msg, videonames=video_names)

@app.route("/download-video/<path:filename>", methods=['GET'])
def download_detection_video(filename):
    return send_from_directory(download_videos, filename, as_attachment=True)
    
# WEBCAM DETECTION

global camera, capture, rec_frame, grey, switch, neg, rec, out
capture = 0
grey = 0
neg = 0
switch = 0
rec = 0

# Make Shots Directory to Save Pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

def record(out):
    global rec_frame
    while(rec):
        time.sleep(0.05)
        out.write(rec_frame)

def gen_webcam_frames():
    global out, capture, rec_frame
    while True:
        success, frame = camera.read()
        if success:
            if(grey):
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if(neg):
                frame = cv2.bitwise_not(frame)
            if(capture):
                capture = 0
                now = datetime.datetime.now()
                p = os.path.sep.join(['static/webcam/images/', "shot_{}.png".format(str(now).replace(":",''))])
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

@app.route('/requests-webcam', methods=['POST', 'GET'])
def tasks_webcam():
    global switch, camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture = 1
        elif request.form.get('grey') == 'Grey':
            global grey
            grey = not grey
        elif request.form.get('neg') == 'Negative':
            global neg
            neg = not neg
        elif request.form.get('stop') == 'Stop/Start':
            global camera
            if (switch == 1):
                switch = 0
                camera.release()
            else:
                camera = cv2.VideoCapture(0)
                switch = 1
        elif request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec = not rec
            if (rec):
                now = datetime.datetime.now()
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                p = os.path.sep.join(['static/webcam/videos/', "vid_{}.avi".format(str(now).replace(":",''))])
                out = cv2.VideoWriter(p, fourcc, 20.0, (640, 480))
                # Start New Thread for Recording the Video
                thread = Thread(target = record, args=[out,])
                thread.start()
            elif (rec == False):
                out.release()
    elif request.method == 'GET':
        return render_template('webcam.html')
    return render_template('webcam.html')


# DRONE DETECTION

drone = cv2.VideoCapture(0)

def drone_gen_frames():
    drone = cv2.VideoCapture('rtmp://192.168.119.87/live/str')
    # global out, capture, rec_frame
    while True:
        success, frame = drone.read()
        if success:
            try:                
                ret, buffer = cv2.imencode('.jpg', frame) # Change "frame" to cv2.flip(frame,1) if you want to flip horizontal
                frame = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
        else:
            pass

@app.route('/live-drone')
def live_drone():
    return Response(drone_gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/requests', methods=['POST', 'GET'])
# def tasks():
#     global switch, drone
#     link_rtmp = request.form.get('linkrtmp')

#     if not link_rtmp:
#         return jsonify({'error' : 'Nothing Found!'})

#     print("The value of link RTMP is ", link_rtmp)
#     print("The type data value of link RTMP is ", type(link_rtmp))
#     drone = cv2.VideoCapture(int(link_rtmp))

#     return render_template('live.html')
            
drone.release()
cv2.destroyAllWindows()