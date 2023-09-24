import numpy as np
import cv2
import pyvirtualcam
import time
import tkinter as tk

import keyboard

cap = cv2.VideoCapture(0)
cap.set(3, 512)
cap.set(4, 288)
counter = 0
recording = False
playing = False
fmt = pyvirtualcam.PixelFormat.BGR

# only once/freeze cam
# time.sleep(4)
# cv2.imshow('a', pencil)

# if cv2.waitKey(1) & 0xFF == ord('q'):
#    break
records = []


def loop():
    global counter, cam, data, cap
    counter += 1
    succes, img = cap.read()
    # img = cv2.imread("ai_face.png")

    blurred = cv2.GaussianBlur(img, (13, 13), 0)
    blurred = cv2.resize(blurred, (1280, 720))

    data = np.asarray(blurred, dtype="uint8")
    # cam.send(data)
    # cam.sleep_until_next_frame()
    # time.sleep(0.1)
    # if counter > 3:
    #     if keyboard.is_pressed('`') == True:
    #         # time.sleep(3)
    #         cam.send(data)
    #         cam.sleep_until_next_frame()
    # else:
    #     succes, img = cap.read()
    #     blurred = cv2.GaussianBlur(img, (1, 1), 0)
    #     blurred = cv2.resize(blurred, (1280, 720))
    #     data = np.asarray(blurred, dtype="uint8")
    if recording == True:
        records.append(data)
        cam.send(data)
        cam.sleep_until_next_frame()
    if playing == True:
        cam.send(records[counter % len(records)])
        cam.sleep_until_next_frame()
    if playing == False and recording == False:
        cam.send(data)
        cam.sleep_until_next_frame()
    root.after(30, loop)


def stopRecording():
    global recording
    recording = False


def startRecording():
    global recording, records, playing
    records = []
    recording = True
    playing = False


def stopPlaying():
    global playing
    playing = False


def startPlaying():
    global recording, playing
    recording = False
    playing = True


root = tk.Tk()
root.title("Camera Customization")
root.geometry('570x135')

stop_recording = tk.Button(root, text="Stop Recording", height=5, width=15, command=stopRecording)
stop_recording.pack()
stop_recording.place(x=10, y=10)

start_recording = tk.Button(root, text="Start Recording", height=5, width=15, command=startRecording)
start_recording.pack()
start_recording.place(x=150, y=10)

stop_playing = tk.Button(root, text="Stop Playing", height=5, width=15, command=stopPlaying)
stop_playing.pack()
stop_playing.place(x=290, y=10)

start_playing = tk.Button(root, text="Start Playing", height=5, width=15, command=startPlaying)
start_playing.pack()
start_playing.place(x=430, y=10)

with pyvirtualcam.Camera(width=1280, height=720, fps=30, device='OBS Virtual Camera', fmt=fmt) as cam:
    root.after(1, loop)
    root.mainloop()
