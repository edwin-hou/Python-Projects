import cv2 as cv
import numpy as np
import os
from time import time
from windowcapture import WindowCapture
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2
import pygetwindow
import pyautogui
import win32api

pyautogui.PAUSE = 0
os.chdir(os.path.dirname(os.path.abspath(__file__)))
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
import pandas
from datetime import datetime
pyautogui.PAUSE = 0

def switch():
    name = pygetwindow.getActiveWindowTitle()

    allwindows = pygetwindow.getAllTitles()
    for title in allwindows:
        if 'Google Chrome' in title:
            break
    if 'youtube' in str(name).lower():
        pyautogui.press('space')
    try:
        window = pygetwindow.getWindowsWithTitle(title)[0]
        window.activate()
        pyautogui.hotkey('ctrl', '1')
    except:
        pass




wincap = WindowCapture('EpocCam Viewer: 1920 x 1080')  #

frame1 = wincap.get_screenshot()
frame2 = wincap.get_screenshot()
while True:

    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 35, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)

        if cv2.contourArea(contour) < 700:
            continue
        switch()
    #cv2.imshow("feed", frame1)
    frame1 = frame2
    frame2 = wincap.get_screenshot()
    if cv2.waitKey(40) == 27:
        break
