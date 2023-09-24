import pyautogui
import time
import random
import string
import winsound

time.sleep(3)
pyautogui.mouseDown()

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
dur = 0.000005
ydist = 0

pyautogui.moveTo(753, 443 + ydist)
mul = 5

while True:
    pyautogui.hotkey('ctrl', 'shift', '3')
    loss = pyautogui.locateCenterOnScreen('eliminated.png', confidence=0.7)
    if loss != None:
        print('loss')
        for i in range(2):
            winsound.PlaySound('loud.wav', winsound.SND_FILENAME)


    for i in range(24):
        for j in range(340 // mul):
            pyautogui.moveTo(j * mul + 753, 443 + ydist)
            time.sleep(dur)
        ydist += 61.111111
        pyautogui.moveTo(1093, 443 + ydist, dur)
        for j in range(340 // mul):
            pyautogui.moveTo(1093 - j * mul, 443 + ydist)
            time.sleep(dur)
        ydist += 60.11111

        pyautogui.moveTo(753, 443 + ydist, dur)
        if ydist >= 550:
            ydist = 0

