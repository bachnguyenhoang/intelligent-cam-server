import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	SECRET_KEY=os.environ.get('SECRET_KEY') or 'intelligent-surveillance-camera'
	DATABASE=os.path.join(basedir+'/instance','cam_server.sqlite')
