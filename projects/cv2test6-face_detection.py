import cv2
import numpy as np

faceCascade = cv2.CascadeClassifier("cv2_resources/haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)
cap.set(3, 640)#width
cap.set(4, 480)#length
cap.set(10, 100)#brightness
while True:
    #img = cv2.imread("Bot_Thumbnail_edited-1.png")
    succes, img = cap.read()
    imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    faces = faceCascade.detectMultiScale(imgGray, 1.1, 4)
    for (x,y,w,h) in faces:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)


    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
