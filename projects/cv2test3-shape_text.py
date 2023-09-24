import cv2
import numpy as np

img = np.zeros((512, 512, 3), np.uint8)  # a matrix of 512 by 512 by 3

# img[:] = 255,0,0 # set the whole matrix to 255,0,0 which makes the color blue
# create a line with starting point and ending point the next arg is colors and the next one is thickness
# img[0] is the width of the image and img[1] is the height of the image
cv2.line(img, (0, 0), (512, 512), (0, 255, 0), 3)

# create a rectangle with edge at 0,0 and the other edge at 250,350, the next arg is color and the next is thickness

cv2.rectangle(img, (0, 0), (250, 350), (0, 0, 255), 2)

# same thing as before but instead of thickness, the whole shape gets filled

cv2.rectangle(img, (300, 300), (512, 512), (255, 0, 0), cv2.FILLED)

# create a circle centered at 400,50 with radius of 30 with color of 255 255 0 and a thickness of 5

cv2.circle(img, (400, 50), 30, (255, 255, 0), 5)
# create hello world text starting at 300,200 with italic font, font scale of 1, color of 0 150 0 and thickness of 1
cv2.putText(img,"Hello World", (300,200),cv2.FONT_ITALIC,1, (0,150,0), 1)

cv2.imshow("Image", img)

cv2.waitKey(0)
