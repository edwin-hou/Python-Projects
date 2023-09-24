import time

from windowcapture import WindowCapture
# import time
import pyautogui
import pyvirtualcam

import numpy
import cv2

for x in pyautogui.getAllWindows():
    if "Paint" in x.title:
        win = x.title
        break
wincap = WindowCapture(win)
fmt = pyvirtualcam.PixelFormat.BGR
start_time = time.time()
with pyvirtualcam.Camera(width=1280, height=720, fps=60, device='OBS Virtual Camera', fmt=fmt) as cam:
    while True:
        # start_time = time.time() # start time of the loop

        # if time.time() - start_time<5 and time.time() - start_time>0:
        #     img = cv2.imread("C:\\Users\\edwin\\Downloads\\id2.png")
        # elif time.time() - start_time<10 and time.time() - start_time>5:
        #     img = cv2.imread("C:\\Users\\edwin\\Downloads\\id3.png")
        # elif time.time() - start_time<15 and time.time() - start_time>10:
        #     img = cv2.imread("C:\\Users\\edwin\\Downloads\\id5 (2).png")
        # else:
        #     img = wincap.get_screenshot(1304, 751, 35, 229)
        # cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        # print(img[600][600])
        img = cv2.resize(img, (1280, 720))
        # data = numpy.asarray(img, dtype="uint8")
        img = numpy.flip(img, 1)
        cam.send(img)
        # cam.sleep_until_next_frame()
        # cv2.imshow('a', numpy.flip(img, 1))
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        # print("FPS: ", 1.0 / (time.time() - start_time))  # FPS = 1 / time to process loop
