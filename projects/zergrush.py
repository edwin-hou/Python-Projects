import cv2
import numpy
import mss
import pyautogui
import time
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
sct = mss.mss()
monitor = {'top': 300, 'left': 0, 'width': 1919, 'height': 843}
prevclicks = []
import math
def distance(a,b) :
    return math.sqrt(pow((a[0]-b[0]),2) + pow((a[1]-b[1]),2) )
def clean_array2d(array,limit) :
    result = array
    i = 0
    while(i < len(array)-10):
        j = 0
        while(j < len(result)):
            if j != i:
                dist = distance(array[i], result[j])
                if dist < limit:
                    result.pop(j)
            j = j + 1
        i = i + 1

    return result
while True:

    clicks = []
    im = numpy.array(sct.grab(monitor))
    im = numpy.flip(im[:, :, :3], 2)  # 1

    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    H, W = im.shape[:2]

    condition = numpy.logical_or(numpy.all(im == [234, 67, 53][::-1], axis=-1),
                                 numpy.all(im == [251, 188, 5][::-1], axis=-1))
    indices = numpy.where(condition)
    coordinates = zip(indices[0], indices[1])
    unique_coordinates = list(set(list(coordinates)))

    clicks = unique_coordinates
    if clicks!=[]:
        clicks = clean_array2d(clicks, 30)
    for click in clicks:
        x, y = click[0], click[1]
        for i in range(3):
            pyautogui.click(y + monitor['left'], x + monitor['top'])
    ## cv2.imshow('hello', im)
    ## if cv2.waitKey(1) & 0xFF == ord('q'):
    ##    break
