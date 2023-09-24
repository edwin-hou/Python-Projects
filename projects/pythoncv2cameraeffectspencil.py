from PIL import Image
import numpy as np
import cv2
import pyvirtualcam

from PIL import Image, ImageDraw, ImageFont

cap = cv2.VideoCapture(0)
cap.set(3, 512)
cap.set(4, 288)

fmt = pyvirtualcam.PixelFormat.BGR
with pyvirtualcam.Camera(width=1280, height=720, fps=30, device='OBS Virtual Camera', fmt=fmt) as cam:
    while True:
        succes, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
        inverted_blurred = 255 - blurred
        pencil = cv2.divide(gray, inverted_blurred, scale=256.0)
        pencil = cv2.merge((pencil, pencil, pencil))

        pencil = cv2.resize(pencil, (1280, 720))
        data = np.asarray(pencil, dtype="uint8")
        cam.send(data)
        cam.sleep_until_next_frame()
        # cv2.imshow('a', pencil)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break
