import cv2
import numpy as np
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # width
cap.set(4, 480)  # length
cap.set(10, 100)  # brightness



def empty(a):
    pass

cv2.namedWindow("TrackBars")
cv2.resizeWindow("TrackBars",640,240)
cv2.createTrackbar("Hue Min","TrackBars",0,179,empty)
cv2.createTrackbar("Hue Max","TrackBars",179,179,empty)
cv2.createTrackbar("Sat Min","TrackBars",0,255,empty)
cv2.createTrackbar("Sat Max","TrackBars",255,255,empty)
cv2.createTrackbar("Val Min","TrackBars",0,255,empty)
cv2.createTrackbar("Val Max","TrackBars",255,255,empty)


while True:

    succes, img = cap.read()

    img = cv2.imread("Diepio.png")
    imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    h_min = cv2.getTrackbarPos("Hue Min","TrackBars")
    h_max = cv2.getTrackbarPos("Hue Max","TrackBars")
    s_min = cv2.getTrackbarPos("Sat Min","TrackBars")
    s_max = cv2.getTrackbarPos("Sat Max","TrackBars")
    v_min = cv2.getTrackbarPos("Val Min","TrackBars")
    v_max = cv2.getTrackbarPos("Val Max","TrackBars")
    #print(h_min,h_max)

    lower = np.array([h_min,s_min,v_min])
    upper = np.array([h_max, s_max, v_max])
    #lower = np.array([25, 144, 101])
    #upper = np.array([161, 218, 170])

    mask = cv2.inRange(imgHSV,lower,upper)
    imgResult = cv2.bitwise_and(img,img,mask=mask)

    #cv2.imshow("original", img)
    #cv2.imshow("HSV", imgHSV)
    #cv2.imshow("Mask",mask)
    cv2.imshow("Output", imgResult)
    cv2.waitKey(1)