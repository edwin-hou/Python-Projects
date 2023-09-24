import cv2
import numpy as np
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # width
cap.set(4, 480)  # length
cap.set(10, 150)  # brightness
while True:
    succes, img = cap.read()

    cv2.imshow("window",img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
