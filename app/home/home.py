from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
from app.home import bp
from opencv_server import Camera
from app.home.helper import *

#directories
@bp.route('/', methods=('GET', 'POST'))
def index():
	camera = Camera()
	if request.method == 'POST':
		if request.form['home_buttons'] == 'Object detections':
			#enable camera with object detection
			return ('', 204)
		if request.form['home_buttons'] == 'Stop camera':
			#disable camera		
			return ('', 204)
		if request.form['home_buttons'] == 'Original':
			#enable camera - no object detection
			return ('', 204)
		if request.form['home_buttons'] == 'Motion mask':
			#motion detection
			return ('', 204)
		if request.form['home_buttons'] == 'Download':
			#redirect to download page
			return redirect(url_for('download.download'))
		if request.form['home_buttons'] == 'Motion detection':
			#turn on motion detection:
			#enable video recording when motion in frame
			camera.recorder()
			return ('', 204)
	return render_template('home/home.html')

#initiate a single camera instance for the page
print('init camera')
#camera = Camera()
@bp.route('/video_feed')
def video_feed():
	"""Video streaming route. Put this in the src attribute of an img tag."""
	return Response(gen(Camera()),
	            mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/feed_original')
def feed_original():
	"""Streaming route for original feed"""
	return Response(gen_original(Camera()),
	            mimetype='multipart/x-mixed-replace; boundary=frame')
		
@bp.route('/feed_motionmask')
def feed_motionmask():
	"""Streaming route for motion feed"""
	return Response(gen_mask(Camera()),
	            mimetype='multipart/x-mixed-replace; boundary=frame')
		
@bp.route('/hello')
def hello():
	with open("img/a.jpg", "rb") as frame:
		f = frame.read()
		b = bytearray(f)
		return Response((b'--frame\r\n'
	       			b'Content-Type: image/jpeg\r\n\r\n' + b + b'\r\n'),
				mimetype='multipart/x-mixed-replace; boundary=frame')
	#return 'Hello, World!'
	
@bp.route('/goodbye')
def goodbye():
	return 'Goodbye, World!'

