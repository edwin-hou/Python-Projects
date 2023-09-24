import pyautogui
import time
import random
import string


time.sleep(3)
pyautogui.mouseDown()
pyautogui.moveTo(753, 443)
while True:
    #pyautogui.mouseDown()
    pyautogui.hotkey('ctrl','shift','3')
    target = pyautogui.locateCenterOnScreen('touch.png', confidence=0.7)
    #print(target)
    if target != None:
        pyautogui.moveTo(target,duration=1)
#    loss = pyautogui.locateCenterOnScreen('eliminated.png', confidence=0.8)
#    start = pyautogui.locateCenterOnScreen('playagain.png', confidence=0.8)
#    if start != None:
#        pyautogui.click(start)
#        time.sleep(0.1)
#        pyautogui.mouseDown()
#        print(start)
#
#    start = pyautogui.locateCenterOnScreen('playagain1.png', confidence=0.8)
#    if start != None:
#        pyautogui.click(start)
#        time.sleep(0.1)
#        pyautogui.mouseDown()
#        print(start)
#
#    if loss != None:
#        print('loss')
#        letters = string.ascii_lowercase
#        st = (''.join(random.choice(letters) for i in range(10)))
#        im = pyautogui.screenshot()
#        im.save('loses/lose' + st + ".png")