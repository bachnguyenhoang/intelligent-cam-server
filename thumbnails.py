import os
import cv2

def create_thumbnails():
    vids = os.listdir('/home/quynhtram/flask/cam-server-revised/videos/')
    vids = [vids[i][:-4] for i in range(len(vids))]
    thumbs = os.listdir('/home/quynhtram/flask/cam-server-revised/thumbnails/')
    thumbs = [thumbs[i][:-4] for i in range(len(thumbs))]
    no_thumbs = list(set(vids).difference(set(thumbs)))
    print(no_thumbs)    
    for vid in no_thumbs:
        vid_path = '/home/quynhtram/flask/cam-server-revised/videos/' + vid+'.avi'
        print(vid_path)
        frame = video_to_frame(vid_path)
        thumb = image_to_thumbs(frame[0])
        cv2.imwrite('/home/quynhtram/flask/cam-server-revised/thumbnails/%s.jpg' % vid, thumb)

def video_to_frame(video_filename):
    """Extract frames from video"""
    cap = cv2.VideoCapture(video_filename)
    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    frames = []
    if cap.isOpened() and video_length > 0:
        frame_ids = [0]
        count = 0
        success, image = cap.read()
        while success and (count < 1):
            if count in frame_ids:
                frames.append(image)
            success, image = cap.read()
            count += 1
    print(len(frames))
    return frames

def image_to_thumbs(img):
    """Create thumbs from image"""
    height, width, channels = img.shape
    thumbs = {"original": img}
    size = 160
    if (width >= size):
        r = (size + 0.0) / width
        max_size = (size, int(height * r))
        thumb = cv2.resize(img, max_size, interpolation=cv2.INTER_AREA)
    return thumb

if __name__ == '__main__':
    create_thumbnails()
