import cv2
import numpy as np
 # video capture from different cameras
cap = cv2.VideoCapture(0)
cap.set(3, 640)#width
cap.set(4, 480)#length
cap.set(10, 100)#brightness
while True:
    succes, img = cap.read()
    cv2.imshow("output", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

"""
kernel = np.ones((5,5),np.uint8) # create a matrix with all 1's that is 5 by 5
img = cv2.imread("click.png")
imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # create gray image
imgBlur = cv2.GaussianBlur(imgGray,(7,7),0) # kernel size 7x7, the kernel size must be an odd number, the 0 in the end is sigma x
imgCanny = cv2.Canny(img,100,100) # create edge on image the two parameters are tresholds
imgDilation = cv2.dilate(imgCanny,kernel,iterations=1) # add a kernel after image the iteration is how thick the edges are going to be
imgEroded = cv2.erode(imgDilation,kernel,iterations=1) # the iteration is how thin the edges are going to be
cv2.imshow("Gray image", imgGray) # gray image
cv2.imshow("Blur image", imgBlur) # blurred image
cv2.imshow("Canny image", imgCanny) # image with edges
cv2.imshow("Dilation image", imgDilation) # image with thicker edges
cv2.imshow("Eroded image", imgEroded) # image with thinner edges

cv2.waitKey(0)
"""