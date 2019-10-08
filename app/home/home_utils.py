from opencv_server import Camera

#helper function
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def gen(camera):
	"""Video streaming generator function."""
	while True:
		frame = camera.get_frame()[0]
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def gen_original(camera):
	"""Video streaming generator function."""
	while True:
		frame = camera.get_frame()[1]
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def gen_mask(camera):
	"""Video streaming generator function."""
	while True:
		frame = camera.get_frame()[2]
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



