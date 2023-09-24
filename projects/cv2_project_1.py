import cv2
import numpy as np
from skimage.transform import (hough_line, hough_line_peaks)

cap = cv2.VideoCapture(1)
cap.set(3, 640)  # width
cap.set(4, 480)  # length
cap.set(10, 150)  # brightness


def getContours(img):
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    point = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= 50:
            cv2.drawContours(imgContour, cnt, -1, (255, 0, 0), 3)
            peri = cv2.arcLength(cnt, True)
            # print(peri)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            objCor = len(approx)
            x, y, w, h = cv2.boundingRect(approx)
#            cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 255, 0), 2)


            point.append((x + w // 2, y + h // 2))
            if len(point) > 1:
                if list(point[1])[1] > list(point[0])[1]:
                    print(point)
                    cv2.line(imgContour, point[0], (list(point[0])[0], 0), (0, 255, 0), 5)
                elif list(point[1])[1] < list(point[0])[1]:
                    cv2.line(imgContour, point[1], (list(point[1])[0], 0), (0, 255, 0), 5)
                cv2.line(imgContour, point[0], point[1], (0, 255, 0), 5)
                image = np.mean(imgContour, axis=2)
                hspace, angles, distances = hough_line(image)
                angle = []
                for _, a, distances in zip(*hough_line_peaks(hspace, angles, distances)):
                    angle.append(a)

                # Obtain angle for each line
                angles = [a * 180 / np.pi for a in angle]

                # Compute difference between the two lines
                angle_difference = np.max(angles) - np.min(angles)
                print(angle_difference)


while True:
    succes, img = cap.read()

    imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([25, 144, 101])
    upper = np.array([161, 218, 170])
    mask = cv2.inRange(imgHSV, lower, upper)

    imgResult = cv2.bitwise_and(img, img, mask=mask)
    imgContour = imgResult.copy()
    imgGray = cv2.cvtColor(imgResult, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (7, 7), 1)
    imgCanny = cv2.Canny(imgBlur, 20, 20)
    getContours(imgCanny)
    cv2.imshow("output", imgContour)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
