from PIL import Image
import cv2
import numpy
import mss
import pyautogui
#import math

pyautogui.FAILSAFE = False
sct = mss.mss()
pyautogui.PAUSE = 0
start = False

while True:
    monitor = {'top': 290, 'left': 700, 'width': 512, 'height': 650}
    im = numpy.array(sct.grab(monitor))
    im = numpy.flip(im[:, :, :3], 2)  # 1
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    H, W = im.shape[:2]
    breakloop = False
    clicks = []
    if start == False:
        for x in range(H - 1, 0, -100):
            for y in range(W - 1, 0, -100):
                #print(im[x,y])
                if numpy.any(im[x, y] == [54, 159, 198]):
                    pyautogui.click(y + 700, x + 290)
                    breakloop = True
                    start = True
                    break
            if breakloop:
                break
    else:
        #print('started')
        for x in range(H - 1, 0, -100):
            for y in range(W - 1, 0, -100):

                if numpy.all(im[x, y] == [0, 0, 0]):
                    # print([x, y])
                    clicks.append([x, y])
                    # im = cv2.circle(im, (x, y), radius=0, color=(0, 0, 255), thickness=-1)
        #            breakloop = True
        #            break
        #    if breakloop:
        #        break

        for click in clicks:
            x, y = click[0], click[1]
            pyautogui.click(y + 700, x + 290)

    #cv2.imshow('hello', im)
    #if cv2.waitKey(1) & 0xFF == ord('q'):
    #    break
