import sys
sys.path.insert(0, './imagezmq')
import imagezmq

import numpy as np
import math
from statistics import mean
import random as rng

from sklearn.cluster import DBSCAN
import cv2
from imutils.video import VideoStream
from imutils.video import FileVideoStream
import imutils
#import argparse

from datetime import datetime as dt
import time

from base_camera import BaseCamera

class Camera(BaseCamera):

	enable_motion = False

	def __init__(self):
		super().__init__()
		self.motion = False
		
		
	def recorder(self):
		#create file
		file_path = '/home/quynhtram/flask/cam-server-revised/videos/'
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		vid_name = str(dt.now())[:-7].replace(' ','_')
		out = cv2.VideoWriter(file_path+vid_name+'.avi',fourcc, 24, (640,480))
		start = time.time()
		while time.time() - start <= 10:
			out.write(cv2.imdecode(np.fromstring(self.get_frame()[0],np.uint8), cv2.IMREAD_COLOR))
		#end record

	#helper functions
	#find centroid of a contour
	def centroid(contour):
		try:
		        M = cv2.moments(contour)
		        cX = int(M["m10"] / M["m00"])
		        cY = int(M["m01"] / M["m00"])
		        return (cX,cY)
		except:
		        return (0,0)

	#create bounding rectangle for an object
	def bounding_rec(img,cnt,color):
		rect = cv2.minAreaRect(cnt)
		box = cv2.boxPoints(rect)
		box = np.int0(box)
		cv2.drawContours(img,[box],0,color,2)
		return Camera.centroid(cnt)
		
	def cluster(input_set,eps):
		cluster = DBSCAN(eps=eps,min_samples=4).fit(input_set)
		labels = cluster.labels_
		return labels

	#class attribute
	# params for ShiTomasi corner detection
	feature_params = dict( maxCorners = 200,
		               qualityLevel = 0.025,
		               minDistance = 3,
		               blockSize = 5 )

	# Parameters for lucas kanade optical flow
	lk_params = dict( winSize  = (15,15),
		          maxLevel = 6,
		          criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

	def receiver():
		image_hub = imagezmq.ImageHub()
		while True:
			_, img = image_hub.recv_image()
			image_hub.send_reply(b'OK')
			yield img
	next_frame = receiver()

	def frames():
		file_path = '/home/quynhtram/flask/cam-server-revised/videos/'
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		tracks = []
		track_len = 5
		detect_interval = 2
		frame_idx = 0

		fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=500,backgroundRatio=0.6)
		time.sleep(2.0)

		already_recording = False
		no_motion = time.time()

		while True:
			start_recording = False
			end_recording = False
			next_frame = next(Camera.next_frame)
			
			next_copy = cv2.GaussianBlur(next_frame,(7,7),0)
			next_gray = cv2.cvtColor(next_copy, cv2.COLOR_BGR2GRAY)             
			vis = next_frame.copy()

			mask = fgbg.apply(next_copy)
		
			if len(tracks) > 0:
				img0, img1 = prev_gray, next_gray
				#calculate flow											
				p0 = np.float32([tr[-1] for tr in tracks]).reshape(-1, 1, 2)
				p1, _st, _err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **Camera.lk_params)

				#reverse flow for evaluation
				p0r, _st, _err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **Camera.lk_params)

				#create feature vectors array
				#position+displacement(distance between 2 points)
				velocity = []
				for (x,y), (x0,y0) in zip(p1.reshape(-1,2),p0.reshape(-1,2)):
				      velocity.append(math.hypot((x-x0),(y-y0))*10)
				velocity = np.array(velocity).reshape(-1,1)
				features_set = np.concatenate((p1.reshape(-1,2),velocity),axis=1)
				
				#create dbscan clusters base on the tracking points
				clustering = Camera.cluster(features_set,50)                          
				d = abs(p0-p0r).reshape(-1, 2).max(-1)
				good = d < 1
				labels_flag = np.array(clustering) > -1
				new_tracks = []
				cluster_list = [[] for _ in range(len(set(clustering)))]
				velocity_list = [[] for _ in range(len(set(clustering)))]

				#loop through the tracked points
				for tr, (x, y), v, label_flag, label, good_flag in zip(tracks, p1.reshape(-1, 2), velocity, labels_flag, 						clustering, good):
					#remove noise                        
					if not (good_flag and label_flag and v > 4):
				                continue
					#add points to corresponding lists
					tr.append((x, y))
					cluster_list[label].append((x,y))
					velocity_list[label].append(v)
					if len(tr) > track_len:
					        del tr[0]
					new_tracks.append(tr)
					cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
				tracks = new_tracks
			       	
				#draw lines showing optical flow trail		
				cv2.polylines(vis, [np.int32(tr) for tr in tracks], False, (0, 255, 0))
				#draw bounding rectangles for every clusters found
				for i in range(len(cluster_list)):
					hull = cv2.convexHull(np.float32(cluster_list[i]).reshape(-1,2))
					color = (3, 1, 1)
					if hull is not None:
						v_mean = np.mean(velocity_list[i])/10
						centr = Camera.bounding_rec(vis,hull,color)
						cv2.circle(vis,centr,2,(255,0,255),-1)
						cv2.putText(vis, str(round(v_mean,1)), (centr[0] - 20, centr[1] - 20),
									cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),2)
				#condition checking for creating motion video
				if sum(len(cluster_list[i]) for i in range(len(cluster_list))) > 0 and (not already_recording) and Camera.enable_motion:
					start_recording = True
					print('start recording...')
					already_recording = True
				if sum(len(cluster_list[i]) for i in range(len(cluster_list))) > 0 and already_recording and Camera.enable_motion:
					no_motion = time.time()

				if (time.time() - no_motion > 5) and already_recording and Camera.enable_motion:
					end_recording = True
					start_recording = False
					already_recording = False
					print('recording stopped')
			#record video if enable motion detection
			if start_recording and Camera.enable_motion:
				print("creating a video...")
				vid_name = str(dt.now())[:-7].replace(' ','_')
				out = cv2.VideoWriter(file_path+vid_name+'.avi',fourcc, 24, (640,480))
				already_recording = True

			if (not end_recording) and already_recording and Camera.enable_motion:
				out.write(vis)
				
			#detect for new tracking points after 1 interval
			if frame_idx % detect_interval == 0:
				for x, y in [np.int32(tr[-1]) for tr in tracks]:
				        cv2.circle(mask, (x, y), 3, 0, -1)
				p = cv2.goodFeaturesToTrack(next_gray, mask = mask, **Camera.feature_params)
				if p is not None:
				        for x, y in np.float32(p).reshape(-1, 2):
				                tracks.append([(x, y)])
	
			#resampling all tracking points after 100 intervals
			if frame_idx %(100*detect_interval) == 0:
				tracks = []
				p = cv2.goodFeaturesToTrack(next_gray, mask = mask, **Camera.feature_params)
				if p is not None:
				        for x,y in np.float32(p).reshape(-1,2):
				                tracks.append([(x,y)])

			frame_idx += 1
			#stop = time.time()
			prev_gray = next_gray
			ch = cv2.waitKey(1)
			yield (cv2.imencode('.jpg', vis)[1].tobytes(),
				cv2.imencode('.jpg', next_frame)[1].tobytes(),
				cv2.imencode('.jpg', mask)[1].tobytes())


	
