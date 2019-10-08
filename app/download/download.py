from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory, send_file, Response
)
from werkzeug.exceptions import abort
from opencv_server import Camera
from tracker_utils import create_json
from app.db import get_db

import os
import zipfile
import json
from threading import Thread

bp = Blueprint('download', __name__)
detection_thread = Thread(target=create_json)
_start_flag = False

@bp.route('/download', methods=('GET', 'POST'))
def download():
	file_path = './videos/'
	org_path = './original/'
	json_path = './json/'
	thumbnails_path = './thumbnails/'
	file_names = sorted(os.listdir(file_path))

	if request.method == 'POST':
		if request.form['download_buttons'] == 'Select':
			return 'nothing', 204
		if request.form['download_buttons'] == 'Back':
			return redirect(url_for('home.index'))
		if request.form['download_buttons'] == 'Info':
		    return redirect(url_for('download.info'))
		if request.form['download_buttons'] == 'Download':
			print('proceed to download ' + str(request.form.getlist('selected'))+ '...')
			return file_zip(file_path,request.form.getlist('selected'))
		if request.form['download_buttons'] == 'Download all':
			return file_zip(file_path,file_names)
		if request.form['download_buttons'] == 'Delete':
			print('proceed to delete ' + str(request.form.getlist('selected')) + '...')
			for item in request.form.getlist('selected'):
				os.remove(file_path + item)
				os.remove(org_path + item)
				os.remove(json_path + item + '.json')
				os.remove(thumbnails_path + item[:-4] + '.jpg')
				file_names = os.listdir(file_path)
			print('remain files: ' + str(file_names))
			return render_template('download/download.html', file_path=file_path, file_names=file_names)
		if request.form['download_buttons'] == 'Delete all':
			for item in file_names:
				os.remove(file_path + item)
				os.remove(org_path + item)
				os.remove(thumbnails_path + item[:-4] + '.jpg')
				os.remove(json_path + item + '.json')
			file_names = os.listdir(file_path)
			return render_template('download/download.html', file_names=file_names)
	return render_template('download/download.html', file_names=file_names)

@bp.route('/thumbs/<file_name>')
def thumbnail(file_name):
	thumbnails_path = './thumbnails/'
	with open(thumbnails_path + file_name, "rb") as frame:
		f = frame.read()
		b = bytearray(f)
		return Response((b'--frame\r\n'
	       			b'Content-Type: image/jpeg\r\n\r\n' + b + b'\r\n'),
				mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/download/info', methods=('GET', 'POST'))
def info():
	global detection_thread
	global _start_flag
	if not detection_thread.is_alive() and (_start_flag is False):
		if request.method=="POST":
			if request.form['back_buttons'] == 'Back':
				return redirect(url_for('download.download'))
			if request.form['back_buttons'] == 'JSON':
				detection_thread.start()
				_start_flag = True
				return redirect(url_for('download.download'))
		data_list = []
		for file_name in sorted(os.listdir('./json/')):
			with open('./json/'+file_name,'r') as f:
				data_list.append(json.load(f))
		return render_template('download/info.html',data_list=data_list)
	elif detection_thread.is_alive() and (_start_flag is True):
		return render_template('download/wait.html')
	elif not detection_thread.is_alive() and (_start_flag is True):
		detection_thread = Thread(target=create_json)
		_start_flag = False
		data_list = []
		for file_name in sorted(os.listdir('./json/')):
			with open('./json/'+file_name,'r') as f:
				data_list.append(json.load(f))
		return render_template('download/info.html',data_list=data_list)

@bp.route('/download/original/<org_name>')
def download_original(org_name):
	return send_from_directory(os.path.abspath('./original'),org_name,as_attachment=True)
@bp.route('/download/videos/<vid_name>')
def download_vid(vid_name):
	return send_from_directory(os.path.abspath('./videos'),vid_name,as_attachment=True)
@bp.route('/download/detection/<vid_name>')
def download_detection(vid_name):
	return send_from_directory(os.path.abspath('./detection'),vid_name,as_attachment=True)
@bp.route('/download/json/<json_name>')
def download_json(json_name):
	return send_from_directory(os.path.abspath('./json'),json_name,as_attachment=True)

def file_zip(file_path, file_names):
	file_path = os.path.abspath(os.path.dirname(file_path)) + '/'
	if len(file_names) == 0:
		return '',204
	elif len(file_names) == 1:
		return send_from_directory(file_path,file_names[0],as_attachment=True)
	else:
		zipf = zipfile.ZipFile(file_path[:-7] + 'zip/'+'vids.zip','w', zipfile.ZIP_DEFLATED)
		for file_name in file_names:
			zipf.write(file_path+file_name,file_name)
		zipf.close()
		return send_file(file_path[:-7] + 'zip/'+'vids.zip', mimetype='zip', attachment_filename='vids.zip', as_attachment=True)
