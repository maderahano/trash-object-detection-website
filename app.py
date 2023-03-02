from re import DEBUG, sub
from flask import Flask, render_template, request, redirect, send_file, url_for, flash, jsonify
from werkzeug.utils import secure_filename, send_from_directory
import os
import subprocess

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
            errors[file.filename] = 'file type is not allowerd'
    
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
    
@app.route("/detect-image/<filename>")
def display_images(filename):
    print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/images/' + filename), code=301)

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
    
@app.route('/detect-video/<filename>')
def display_videos(filename):
    print('display_video filename: ' + filename)
    return redirect(url_for('static', filename='uploads/videos/' + filename), code=301)

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