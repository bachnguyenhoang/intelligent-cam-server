from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory, send_file, Response
)
from werkzeug.exceptions import abort
from opencv_server import Camera
from app.db import get_db
import os
import zipfile

bp = Blueprint('download', __name__)

@bp.route('/download', methods=('GET', 'POST'))
def download():
	file_path = '/home/quynhtram/flask/cam-server-revised/videos/'
	thumbnails_path = '/home/quynhtram/flask/cam-server-revised/thumbnails/'
	file_names = os.listdir(file_path)

	if request.method == 'POST':
		if request.form['download_buttons'] == 'Select':
			return 'nothing', 204
		if request.form['download_buttons'] == 'Back':
			return redirect(url_for('home.index'))
		if request.form['download_buttons'] == 'Download':
			print('proceed to download ' + str(request.form.getlist('selected'))+ '...')
			return file_zip(file_path,request.form.getlist('selected'))
		if request.form['download_buttons'] == 'Download all':
			return file_zip(file_path,file_names)
		if request.form['download_buttons'] == 'Delete':
			print('proceed to delete ' + str(request.form.getlist('selected')) + '...')
			for item in request.form.getlist('selected'):
				os.remove(file_path + item)
				os.remove(thumbnails_path + item[:-4] + '.jpg')
				file_names = os.listdir(file_path)				
			print('remain files: ' + str(file_names))
			return render_template('download/download.html', file_path=file_path, file_names=file_names)
		if request.form['download_buttons'] == 'Delete all':
			for item in file_names:
				os.remove(file_path + item)
				os.remove(thumbnails_path + item[:-4] + '.jpg')
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
	

def file_zip(file_path, file_names):
	if len(file_names) == 0:
		return '',204
	elif len(file_names) == 1:
		return send_from_directory(file_path,file_names[0],as_attachment=True)
	else:
		zipf = zipfile.ZipFile('/home/quynhtram/flask/cam-server-revised/zip/'+'vids.zip','w', zipfile.ZIP_DEFLATED)
		for file_name in file_names:
			zipf.write(file_path+file_name,file_name)
		zipf.close()
		return send_file('/home/quynhtram/flask/cam-server-revised/zip/'+'vids.zip', mimetype='zip', attachment_filename='vids.zip', as_attachment=True)
