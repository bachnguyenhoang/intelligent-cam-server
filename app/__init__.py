#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response
from config import Config

# import camera driver
#if os.environ.get('CAMERA'):
#    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
#else:
#    from camera import Camera
from opencv_server import Camera
# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

def create_app(test_config=None):
	print('creating app...')
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_object(Config)
	try:
		os.makedirs('./videos')
	except OSError:
		pass
	try:
		os.makedirs('./zip')
	except OSError:
		pass
	try:
		os.makedirs('./thumbnails')
	except OSError:
		pass
	from . import db
	db.init_app(app)
	from app.home import bp as home_bp
	app.register_blueprint(home_bp)
	app.add_url_rule('/', endpoint='index')
	from app.download import download
	app.register_blueprint(download.bp)
	return app
