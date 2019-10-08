#standard
import os
import json
import time

from imutils.video import VideoStream
import numpy as np
import cv2
from tracker.centroidtracker import CentroidTracker
from tracker.trackableobject import TrackableObject

import dlib

def tracker(inp, out=None, yolo="yolo-tiny", confidence_thres=0.2, thres=0.5):
    # load the COCO class labels our YOLO model was trained on
    labelsPath = os.path.sep.join([yolo, "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    # initialize centroid tracker, object counter, and trackers
    ct = dict((item, CentroidTracker(maxDisappeared=15, maxDistance=50)) for item in LABELS)
    total = dict((item, 0) for item in LABELS)
    trackableObjects = dict((item, {}) for item in LABELS)
    trackers = dict((item, []) for item in LABELS)
    # initialize the frame size and video writer
    H, W = None, None
    writer = None
    frame_count = 0

    # initialize data dict for json file
    data = {}
    if inp is not None:
        data['name'] = os.path.basename(inp)
        cap = cv2.VideoCapture(inp)
        data['frame_count'] = int(cv2.VideoCapture.get(cap, cv2.CAP_PROP_FRAME_COUNT))
        data['fps'] = int(cap.get(cv2.CAP_PROP_FPS))
        data['objects'] = total
    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                               dtype="uint8")

    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo, "yolov3.weights"])
    configPath = os.path.sep.join([yolo, "yolov3.cfg"])

    # load our serialized model from disk
    #print("[INFO] loading model...")
    #net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # initialize the video stream and allow the camera sensor to warmup
    if inp is None:
        print("[INFO] starting video stream...")
        vs = VideoStream(src=0).start()
        time.sleep(2.0)
    else:
        vs = cv2.VideoCapture(inp)
    # loop over the frames from the video stream
    while True:
        rects = dict((item, []) for item in LABELS)
        if frame_count >= data['frame_count']:
            print("[INFO] video ended")
            break
        # read the next frame from the video stream and resize it
        _, frame = vs.read()

        # if the frame dimensions are None, grab them
        if W is None or H is None:
            (H, W) = frame.shape[:2]

        # if we are supposed to be writing a video to disk, initialize
        # the writer
        if out is not None and writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(out, fourcc, 30,
                                     (W, H), True)
        if frame_count % 15 == 0:
            trackers = dict((item, []) for item in LABELS)
            #PREPROCESSING
            # construct a blob from the frame, pass it through the network,
            # obtain our output predictions, and initialize the list of
            # bounding box rectangles
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
                                         swapRB=True, crop=False)
            net.setInput(blob)
            layerOutputs = net.forward(ln)
            boxes = []
            confidences = []
            classIDs = []

            #OBJECT DETECTION
            for output in layerOutputs:
                # loop over each of the detections
                for detection in output:
                    # extract the class ID and confidence (i.e., probability)
                    # of the current object detection
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]

                    # filter out weak predictions by ensuring the detected
                    # probability is greater than the minimum probability
                    if confidence > confidence_thres:
                        # scale the bounding box coordinates back relative to
                        # the size of the image, keeping in mind that YOLO
                        # actually returns the center (x, y)-coordinates of
                        # the bounding box followed by the boxes' width and
                        # height
                        box = detection[0:4] * np.array([W, H, W, H])
                        (centerX, centerY, width, height) = box.astype("int")

                        # use the center (x, y)-coordinates to derive the top
                        # and and left corner of the bounding box
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))

                        # update our list of bounding box coordinates,
                        # confidences, and class IDs
                        boxes.append([x, y, int(width), int(height)])
                        confidences.append(float(confidence))
                        classIDs.append(classID)

            # apply non-maxima suppression to suppress weak, overlapping
            # bounding boxes
            idxs = cv2.dnn.NMSBoxes(boxes, confidences,
                                    confidence_thres, thres)
            if len(idxs) > 0:
                # loop over the indexes we are keeping
                for i in idxs.flatten():
                    # extract the bounding box coordinates
                    (x, y) = (boxes[i][0], boxes[i][1])
                    (w, h) = (boxes[i][2], boxes[i][3])
                    #rects[LABELS[classIDs[i]]].append((x,y,x+w,y+h))
                    color = [int(c) for c in COLORS[classIDs[i]]]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    text = "{}".format(LABELS[classIDs[i]])
                    cv2.putText(frame, text, (int(x+w/2 - 10), int(y+h/2 - 30)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    # construct a dlib rectangle object from the bounding
                    # box coordinates and then start the dlib correlation
                    # tracker
                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(x, y, x+w, y+h)
                    tracker.start_track(frame, rect)

                    # add the tracker to our list of trackers so we can
                    # utilize it during skip frames
                    trackers[LABELS[classIDs[i]]].append(tracker)

        else:
            for (key, tracks) in trackers.items():
                for tracker in tracks:
                    # set the status of our system to be 'tracking' rather
                    # than 'waiting' or 'detecting'

                    # update the tracker and grab the updated position
                    tracker.update(frame)
                    pos = tracker.get_position()

                    # unpack the position object
                    startX = int(pos.left())
                    startY = int(pos.top())
                    endX = int(pos.right())
                    endY = int(pos.bottom())

                    # add the bounding box coordinates to the rectangles list
                    rects[key].append((startX, startY, endX, endY))
                    color = [int(c) for c in COLORS[LABELS.index(key)]]
                    cv2.rectangle(frame, (startX, startY), (endX, endY),
                                  color, 2)
                    text = "{}".format(key)
                    cv2.putText(frame, text, (int(startX+(endX-startX)/2 - 10),
                                              int(startY+(endY-startY)/2 - 30)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            #OBJECT TRACKING
            # update our centroid tracker using the computed set of bounding
            # box rectangles
            for (num, item) in enumerate(LABELS):
                objects = ct[item].update(rects[item])

                # loop over the tracked objects
                for (objectID, centroid) in objects.items():
                    color = [int(c) for c in COLORS[num]]
                    # draw both the ID of the object and the centroid of the
                    # object on the output frame
                    text = "ID {}".format(objectID)
                    cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.circle(frame, (centroid[0], centroid[1]), 4, color, -1)

                    # check to see if a trackable object exists for the current
                    # object ID
                    to = trackableObjects.get(item).get(objectID, None)

                    # if there is no existing trackable object, create one
                    if to is None:
                        to = TrackableObject(objectID, centroid)

                    # otherwise, there is a trackable object so we can utilize it
                    # to determine direction
                    else:
                        # the difference between the y-coordinate of the *current*
                        # centroid and the mean of *previous* centroids will tell
                        # us in which direction the object is moving (negative for
                        # 'left' and positive for 'right')
                        x = [c[0] for c in to.centroids]
                        direction = centroid[0] - np.mean(x)
                        to.centroids.append(centroid)
                        # check to see if the object has been counted or not
                        if not to.counted:
                            # if the object move past the center line
                            # and path larger than threshold, count
                            if direction < 0 and abs(direction) > 10 and centroid[0] < W // 2:
                                total[item] += 1
                                to.counted = True

                            elif direction > 0 and abs(direction) > 10 and centroid[0] > W // 2:
                                total[item] += 1
                                to.counted = True

                    # store the trackable object in our dictionary
                    trackableObjects[item][objectID] = to

        info = [(item, total[item]) for item in LABELS]

        # loop over the info tuples and draw them on our frame
        for (i, (k, v)) in enumerate(info):
            text = "{}: {}".format(k, v)
            cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        if out is not None and writer is not None:
            writer.write(frame)
        frame_count += 1
    if inp is not None:
        with open('./json/' + data['name'] +'.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)
    if out is not None:
        writer.release()

def create_json():
    vids = os.listdir('./original/')
    list_file = open('check_list.json', 'r')
    read_list = json.load(list_file)
    not_read = list(set(vids).difference(set(read_list)))
    list_file.close()
    for vid in not_read:
        tracker(inp='./original/'+vid,
                out='./detection/'+vid,
                yolo="yolo-custom", confidence_thres=0.2, thres=0.5)
        read_list.append(vid)
    list_file = open('check_list.json', 'w')
    json.dump(sorted(read_list), list_file, indent=4)
    list_file.close()
