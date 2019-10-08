#system
import os
import json
import sys
#datetime
from datetime import datetime as dt
import time
#math
import math
import numpy as np
from sklearn.cluster import DBSCAN
#video processing
#imagezmq
import cv2
sys.path.insert(0, './imagezmq')
import imagezmq
#custom lib
from base_camera import BaseCamera
from thumbnails import create_thumbnails

class Camera(BaseCamera):
    #class attributes
    #flag for recording
    enable_motion = False

    # params for ShiTomasi corner detection
    feature_params = dict(maxCorners=200,
                          qualityLevel=0.025,
                          minDistance=3,
                          blockSize=5)

    # Parameters for lucas kanade optical flow
    lk_params = dict(winSize =(15,15),
                     maxLevel=6,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
    #Parameters for background subtraction
    subtractor_params = dict(backgroundRatio=0.6, 
                             history=500)
    region_params = dict(x_min=0,y_min=0,x_max=0,y_max=0)

    def __init__(self):
        super().__init__()

    #helper functions
    #setter
    def set_feature_params(maxCorners, qualityLevel, minDistance, blockSize):
        Camera.feature_params['maxCorners'] = int(maxCorners)
        Camera.feature_params['qualityLevel'] = qualityLevel
        Camera.feature_params['minDistance'] = int(minDistance)
        Camera.feature_params['blockSize'] = int(blockSize)
    def set_subtractor_params(backgroundRatio, history):
        Camera.subtractor_params['backgroundRatio'] = backgroundRatio
        Camera.subtractor_params['history'] = int(history)
    def set_region_params(x_min, y_min, x_max, y_max):
        Camera.region_params['x_min'] = int(x_min)
        Camera.region_params['y_min'] = int(y_min)
        Camera.region_params['x_max'] = int(x_max)
        Camera.region_params['y_max'] = int(y_max)
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
    #create DBSCAN clusters 
    def cluster(input_set,eps):
        cluster = DBSCAN(eps=eps,min_samples=4).fit(input_set)
        labels = cluster.labels_
        return labels
    #receive frames from Pi
    def receiver():
        image_hub = imagezmq.ImageHub()
        while True:
            _, img = image_hub.recv_image()
            image_hub.send_reply(b'OK')
            yield img
    next_frame = receiver()
    #create json file for saved vids
    def create_data(file_name):
        data={}
        data['name'] = os.path.basename(file_name)
        data['frame_count'] = 0
        data['fps'] = 24
        data['objects'] = dict((item, 0) for item in ["bicycle", "bus", "car", "dog", "motorbike", "person"])
        return data
    #main method for analyzing and saving frames
    def frames():
        #parameters for tracking and sampling
        tracks = []
        track_len = 5
        detect_interval = 2
        frame_idx = 0
        
        #background subtraction
        fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=500,backgroundRatio=0.6)
        time.sleep(2.0)
        
        #flags for recording
        already_recording = False
        no_motion = time.time()
        
        #parameters for recording
        vid_path = './videos/'
        org_path = './original/'
        json_path = './json/'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        
        while True:
            #flags for recording
            start_recording = False
            end_recording = False
            
            next_frame = next(Camera.next_frame)
            next_copy = cv2.GaussianBlur(next_frame,(7, 7), 0)
            next_gray = cv2.cvtColor(next_copy, cv2.COLOR_BGR2GRAY)
            vis = next_frame.copy()
            mask = fgbg.apply(next_copy)
            mask[Camera.region_params['y_min']:Camera.region_params['y_max'],
            Camera.region_params['x_min']:Camera.region_params['x_max']] = 0

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
                for (x, y), (x0, y0) in zip(p1.reshape(-1, 2),p0.reshape(-1, 2)):
                      velocity.append(math.hypot((x-x0), (y-y0))*10)
                velocity = np.array(velocity).reshape(-1, 1)
                features_set = np.concatenate((p1.reshape(-1, 2), velocity), axis=1)
                
                #create dbscan clusters base on the tracking points
                clustering = Camera.cluster(features_set,50)
                d = abs(p0 - p0r).reshape(-1, 2).max(-1)
                good = d < 1
                labels_flag = np.array(clustering) > -1
                new_tracks = []
                cluster_list = [[] for _ in range(len(set(clustering)))]
                velocity_list = [[] for _ in range(len(set(clustering)))]
                #loop through the tracked points
                for tr, (x, y), v, label_flag, label, good_flag in zip(tracks, p1.reshape(-1, 2), velocity, labels_flag,                         clustering, good):
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
                    hull = cv2.convexHull(np.float32(cluster_list[i]).reshape(-1, 2))
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

            #record video if enable motion detection and flags
            if start_recording and Camera.enable_motion:
                vid_name = str(dt.now())[:-7].replace(' ','_')
                out_org = cv2.VideoWriter(org_path+vid_name+'.avi', fourcc, 24, (640,480))
                out = cv2.VideoWriter(vid_path+vid_name+'.avi', fourcc, 24, (640,480))
                data = Camera.create_data(vid_path+vid_name+'.avi')
                with open(json_path+vid_name+'.avi' +'.json', 'w') as outfile:
                    json.dump(data, outfile, indent=4)
                already_recording = True
                print("[DEBUG] Start recording: {}...".format(start_recording))
                print("[DEBUG] Already recording: {}...".format(already_recording))
                print("[DEBUG] End recording: {}...".format(end_recording))

            if (not end_recording) and already_recording and Camera.enable_motion:
                out_org.write(next_frame)
                out.write(vis)
            if end_recording or (already_recording and (not Camera.enable_motion)):
                already_recording = False
                out.release()
                out_org.release()
                create_thumbnails()
                print("[DEBUG] Start recording: {}...".format(start_recording))
                print("[DEBUG] Already recording: {}...".format(already_recording))
                print("[DEBUG] End recording: {}...".format(end_recording))
            #detect for new tracking points after 1 interval
            if frame_idx % detect_interval == 0:
                for x, y in [np.int32(tr[-1]) for tr in tracks]:
                        cv2.circle(mask, (x, y), 3, 0, -1)
                p = cv2.goodFeaturesToTrack(next_gray, mask=mask, **Camera.feature_params)
                if p is not None:
                        for x, y in np.float32(p).reshape(-1, 2):
                                tracks.append([(x, y)])

            #resampling all tracking points after 100 intervals
            if frame_idx %(100*detect_interval) == 0:
                tracks = []
                p = cv2.goodFeaturesToTrack(next_gray, mask=mask, **Camera.feature_params)
                if p is not None:
                        for x, y in np.float32(p).reshape(-1, 2):
                                tracks.append([(x, y)])

            frame_idx += 1
            #stop = time.time()
            prev_gray = next_gray
            yield (cv2.imencode('.jpg', vis)[1].tobytes(),
                      cv2.imencode('.jpg', next_frame)[1].tobytes(),
                      cv2.imencode('.jpg', mask)[1].tobytes())

