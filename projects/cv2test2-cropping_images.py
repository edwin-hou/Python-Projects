#resize an image and cropping
import cv2
import numpy as np

img = cv2.imread('click.png')
imgResize = cv2.resize(img,(300,200))# define width and the height

imgCropped = img[0:200,200:500] # height first and then the width, [height, width] you can treat an image as an array

cv2.imshow("image",img)
cv2.imshow("resized image",imgResize)
cv2.imshow("cropped image",imgCropped)
cv2.waitKey(0)