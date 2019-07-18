import sys
sys.path.insert(0,'./imagezmq')
import socket
import time
import cv2
import argparse
from imutils.video import VideoStream
import imagezmq

ap = argparse.ArgumentParser()
ap.add_argument('-ip','--IPAddress', required=True, help='ip address of the server')
args = vars(ap.parse_args())

sender = imagezmq.ImageSender(connect_to=('tcp://{}:5555'.format(args["IPAddress"])))
rpi_name = socket.gethostname()
picam = VideoStream(src=0,usePiCamera=True,resolution=(640,480),framerate=25).start()
time.sleep(2.0)
while True:
	image = picam.read()
	sender.send_image(rpi_name,image)

picam.stop()
#cv2.destroyAllWindows()
