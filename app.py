from re import DEBUG, sub
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for, flash, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from flask_googlemaps import GoogleMaps, Map, icons
from dotenv import load_dotenv
from GPSPhoto import gpsphoto
import ffmpeg_streaming
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

image_names = []
video_names = []
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

@app.route("/upload")
def upload():
    return render_template('upload.html')

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

@app.route("/try-upload")
def try_upload():
    return render_template('tryUpload.html')

@app.route("/drone")
def drone():
    # subprocess.run(['sh', 'stream1.sh'], cwd='live')
    # video = ffmpeg_streaming.input('rtmp://127.0.0.1/live/str')

    return render_template('drone.html')

@app.route("/stream-drone")
def stream_drone():
    def generate():
        startTime = time.time()
        buffer = []
        sentBurst = False

        ffmpeg_command = ["sh", "stream1.sh"]
        process = subprocess.Popen(ffmpeg_command, cwd='live', stdout = subprocess.PIPE, stderr = subprocess.STDOUT, bufsize = -1)

        while True:
            # Get some data from ffmpeg
            line = process.stdout.read(1024)

            # We buffer everything before outputting it
            buffer.append(line)

            # Minimum buffer time, 3 seconds
            if sentBurst is False and time.time() > startTime + 3 and len(buffer) > 0:
                sentBurst = True

                for i in range(0, len(buffer) - 2):
                    print("Send initial burst #", i)
                    yield buffer.pop(0)

            elif time.time() > startTime + 3 and len(buffer) > 0:
                yield buffer.pop(0)

            process.poll()
            if isinstance(process.returncode, int):
                if process.returncode > 0:
                    print('FFmpeg Error')
                break

    return Response(stream_with_context(generate()), mimetype = "audio/mpeg")    

@app.route("/upload-images", methods=['POST'])
def upload_detection_images():
    if not request.method == "POST":
        return redirect(request.url)

    if 'uploadImageFiles' not in request.files:
        return redirect(request.url)
    
    image_names = []
    locations = []
    
    files = request.files.getlist('uploadImageFiles')   
    for file in files:
        if file and allowed_image_file(file.filename):
            filename = secure_filename(file.filename)
            image_names.append(filename)
            file.save(os.path.join(upload_images, filename))
            locations.append(gpsphoto.getGPSData(os.path.join(upload_images, filename)))

            subprocess.run(['./darknet', 'detector', 'test', 'data/obj.data', 'cfg/trash.cfg', 'backup/trash/training/trash_best.weights', os.path.join("../static/uploads/images/", filename), '-thresh 0.3', '-dont_show'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', '../static/downloads/images/'], cwd='yolov4')
            subprocess.run(['cp', 'predictions.jpg', filename], cwd='static/downloads/images')
            subprocess.run(['rm', 'predictions.jpg'], cwd='static/downloads/images')
            
            msg = 'Files successfully uploaded!'
        else:
            msg = 'Invalid Upload!'

    map = Map(
        identifier="view-map",
        maptype='SATELLITE',
        style="height:600px;width:900px",
        lat=locations[0]['Latitude'],
        lng=locations[0]['Longitude'],
        markers=[(loc['Latitude'], loc['Longitude']) for loc in locations],
        fit_markers_to_bounds = True 
    )
    
    return render_template('tryUpload.html', msg=msg, imagenames=image_names, map=map)

@app.route("/download-images", methods=['GET'])
def download_detection_images():
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zf:
        for filename in image_names:
            file = os.path.join(download_images, filename)
            zf.write(file, os.path.basename(file))
            # data = ZipInfo(file['fileName'])
            # data.date_time = time.localtime(time.time())[:6]
            # data.compress_type = ZIP_DEFLATED
            # zf.writestr(data, file['fileData'])
            
    memory_file.seek(0)

    return send_file(memory_file, download_name='all_images.zip', as_attachment=True)

@app.route("/download-image/<path:filename>", methods=['GET'])
def download_detection_image(filename):
    return send_from_directory(download_images, filename, as_attachment=True)


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
    
    return render_template('tryUpload.html', msg=msg, videonames=video_names)

@app.route("/download-videos", methods=['GET'])
def download_detection_videos():
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zf:
        for filename in video_names:
            file = os.path.join(download_videos, filename)
            zf.write(file, os.path.basename(file))
            
    memory_file.seek(0)

    return send_file(memory_file, download_name='all_videos.zip', as_attachment=True)

@app.route("/download-video/<path:filename>", methods=['GET'])
def download_detection_video(filename):
    return send_from_directory(download_videos, filename, as_attachment=True)

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
    
    return render_template('upload.html', imagenames=fileNames)
    
    # if success and errors:
    #     errors['message'] = 'File(s) successfully uploaded'
    #     resp = jsonify(errors)
    #     resp.status_code = 206
    #     msg = 'File(s) successfully uploaded!'
    #     return jsonify({'htmlresponse': render_template('response.html', msg=msg)})
    # if success:
    #     resp = jsonify({'message' : "Files successfully uploaded"})
    #     resp.status_code = 201
    #     print(fileNames)
    #     msg = 'Files successfully uploaded!'
    #     return jsonify({'htmlresponse': render_template('response.html', msg=msg, imagenames=fileNames)})
    # else:
    #     resp = jsonify(errors)
    #     resp.status_code = 400
    #     msg = 'Invalid upload only png, jpg, jpeg'
    #     return jsonify({'htmlresponse': render_template('response.html', msg=msg)})
    
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

# global capture, rec_frame, grey, switch, neg, rec, out, trash
# trash = 0
# capture = 0
# grey = 0
# neg = 0
# switch = 0
# rec = 0

# # yolo variable

# global metaMain, netMain, altNames
# netMain = None
# metaMain = None
# altNames = None

# # Make Shots Directory to Save Pics
# try:
#     os.mkdir('./shots')
# except OSError as error:
#     pass

# camera = cv2.VideoCapture(0)

# def record(out):
#     global rec_frame
#     while(rec):
#         time.sleep(0.05)
#         out.write(rec_frame)

# def detect_webcam_trash(frame):
#     global start_x, start_y, box_width, box_height, label
#     start_x = 0
#     start_y = 0
#     box_width = 0
#     box_height = 0
#     label = 0

#     frame_width = frame.shape[1]
#     frame_height = frame.shape[0]
    
#     frame_blob = cv2.dnn.blobFromImage(frame, 1 / 255, (416, 416), swapRB=True, crop=False)

#     with open("yolov4/data/obj.names","r", encoding="utf-8") as f:
#         labels = f.read().strip().split("\n")

#     colors = ["0,255,255", "0,0,255", "255,0,0", "255,255,0", "0,255,0"]
#     colors = [np.array(color.split(",")).astype("int") for color in colors]
#     colors = np.array(colors)
#     colors = np.tile(colors, (18, 1))

#     yolo_config_path = "yolov4/cfg/trash.cfg"
#     yolo_weights_path = "yolov4/backup/trash/training/trash_best.weights"

#     net = cv2.dnn.readNetFromDarknet(yolo_config_path, yolo_weights_path)
#     layers = net.getLayerNames()

#     output_layer = [layers[i - 1] for i in net.getUnconnectedOutLayers()]
#     net.setInput(frame_blob)
#     detection_layers = net.forward(output_layer)

#     ids_list = []
#     boxes_list = []
#     confidences_list = []

#     for detection_layer in detection_layers:
#         for object_detection in detection_layer:

#             scores = object_detection[5:]
#             predicted_id = np.argmax(scores)
#             confidence = scores[predicted_id]

#             if confidence > 0.35:
                
#                 label = labels[predicted_id]
#                 bounding_box = object_detection[0:4] * np.array([frame_width, frame_height, frame_width, frame_height])
#                 (box_center_x, box_center_y, box_width, box_height) = bounding_box.astype("int")

#                 start_x = int(box_center_x - (box_width / 2))
#                 start_y = int(box_center_y - (box_height / 2))

#                 ids_list.append(predicted_id)
#                 confidences_list.append(float(confidence))
#                 boxes_list.append([start_x, start_y, int(box_width), int(box_height)])
#             max_ids = cv2.dnn.NMSBoxes(boxes_list, confidences_list, 0.5, 0.4)

#     for max_id in max_ids:
#         max_class_id = max_id[0]
#         box = boxes_list[max_class_id]

#         start_x = box[0]
#         start_y = box[1]
#         box_width = box[2]
#         box_height = box[3]

#         predicted_id = ids_list[max_class_id]
#         label = labels[predicted_id]
#         confidence = confidences_list[max_class_id]

#     end_x = start_x + box_width
#     end_y = start_y + box_height

#     box_color = colors[predicted_id]
#     box_color = [int(each) for each in box_color]
#     label = "{}: {:.2f}%".format(label, confidence * 100)
#     print("predicted object {}".format(label))

#     cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), box_color, 2)
#     cv2.putText(frame, label, (start_x, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

#     return frame

# def gen_webcam_frames():
#     global out, capture, rec_frame
#     while True:
#         success, frame = camera.read()
#         if success:
#             if(trash):
#                 frame = detect_webcam_trash(frame)
#             if(grey):
#                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             if(neg):
#                 frame = cv2.bitwise_not(frame)
#             if(capture):
#                 capture = 0
#                 now = datetime.datetime.now()
#                 p = os.path.sep.join(['static', "shot_{}.png".format(str(now).replace(":",''))])
#                 cv2.imwrite(p, frame)
#             if(rec):
#                 rec_frame = frame
#                 frame = cv2.putText(cv2.flip(frame,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 4)
#                 frame = cv2.flip(frame,1)

#             try:                
#                 ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
#                 frame = buffer.tobytes()
#                 yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             except Exception as e:
#                 pass
#         else:
#             pass
    
# @app.route('/live-webcam')
# def live_webcam():
#     return Response(gen_webcam_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/requests', methods=['POST', 'GET'])
# def tasks():
#     global switch, camera
#     if request.method == 'POST':
#         if request.form.get('click') == 'Capture':
#             global capture
#             capture = 1
#         elif request.form.get('trash') == 'Trash':
#             global trash
#             trash = not trash
#             if (trash):
#                 time.sleep(4)
#         elif request.form.get('grey') == 'Grey':
#             global grey
#             grey = not grey
#         elif request.form.get('neg') == 'Negative':
#             global neg
#             neg = not neg
#         elif request.form.get('stop') == 'Stop/Start':
#             if (switch == 1):
#                 switch = 0
#                 camera.release()
#                 cv2.destroyAllWindows()
#             else:
#                 camera = cv2.VideoCapture(0)
#                 switch = 1
#         elif request.form.get('rec') == 'Start/Stop Recording':
#             global rec, out
#             rec = not rec
#             if (rec):
#                 now = datetime.datetime.now()
#                 fourcc = cv2.VideoWriter_fourcc(*'XVID')
#                 out = cv2.VideoWriter('vid_{}.avi'.format(str(now).replace(":",'')), fourcc, 20.0, (640, 480))
#                 # Start New Thread for Recording the Video
#                 thread = Thread(target = record, args=[out,])
#                 thread.start()
#             elif (rec == False):
#                 out.release()
#     elif request.method == 'GET':
#         return render_template('index.html')
#     return render_template('index.html')

# camera.release()


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