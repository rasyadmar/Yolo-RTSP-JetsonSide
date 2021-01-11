import cv2
from time import sleep
import time
import subprocess as sp
from utils.yolo_classes import get_cls_dict
from utils.visualization import BBoxVisualization
from utils.yolo_with_plugins import TrtYOLO
import pycuda.autoinit

cap = cv2.VideoCapture('rtsp://localhost:8554/stream_input')
cls_dict = get_cls_dict(80)
h = w = 288
model = 'yolov4-tiny-288'
trt_yolo = TrtYOLO(model, (h, w))
vis = BBoxVisualization(cls_dict)
rtsp_server_output = 'rtsp://localhost:8554/stream_output'
command = ['ffmpeg',
               '-re',
               # '-s', sizeStr,
               # '-r', str(fps),  # rtsp fps (from input server)
               # '-f', 'v4l2',
               '-i', '-',

               # You can change ffmpeg parameter after this item.
               # '-pix_fmt', 'yuv420p',
               # '-r', '30',  # output fps
               # '-g', '50',
               # '-c:v', 'libx264',
               # '-b:v', '2M',
               # '-bufsize', '64M',
               # '-maxrate', "4M",
               # '-preset', 'ultrafast',
               # '-rtsp_transport', 'udp',
               # '-segment_times', '2',
               '-f', 'rtsp',
               rtsp_server_output]
process = sp.Popen(command, stdin=sp.PIPE)
font = cv2.FONT_HERSHEY_PLAIN
fps = 0.0
tic = time.time()

def closedCapCallback():
    global cap
    print("no connection in the stream, reconnecting")
    cap = cv2.VideoCapture('rtsp://localhost:8554/stream_input')
    sleep(0.5)

while True:
    if not cap.isOpened():
        print('error while subprocess not running')
        closedCapCallback()
    else:
        _,frame = cap.read()
        if not frame is None:
            boxes, confs, clss = trt_yolo.detect(frame, 0.3)
            frame = vis.draw_bboxes(frame, boxes, confs, clss)
            cv2.putText(frame, "FPS: " + str(round(fps, 2)), (10, 50), font, 3, (0, 0, 0), 3)
            toc = time.time()
            curr_fps = 1.0 / (toc - tic)

            fps = curr_fps if fps == 0.0 else (fps * 0.95 + curr_fps * 0.05)
            tic = toc

            ret_toRTSP, frame_toRTSP = cv2.imencode('.png', frame)
            process.stdin.write(frame_toRTSP.tobytes())

        else:
            print('error while subprocess is running')
            closedCapCallback()

cam.release()
cv2.destroyAllWindows()