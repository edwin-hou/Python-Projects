#from PIL import ImageGrab
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\edwin\AppData\Local\Tesseract-OCR\tesseract.exe'
import time
from color_util import process_image
from PIL import Image
from pytesseract import image_to_string
import pyautogui
import keyboard
from autocorrect import Speller
img = Image.open('click.png')
spell = Speller(lang='en')
import pyperclip
pyautogui.PAUSE = 0
check = False
from PIL import ImageGrab
while True:
    if not keyboard.is_pressed('down') and check == True:
        try:
            img = ImageGrab.grabclipboard()
            #img = process_image(img)
            text = pytesseract.image_to_string(img)
            #corect = ''    
            #for i in text.split(' '):
            #    correct += spell(i)
            #    correct +=' '
            text.replace('\n',' ')
            correct = text
            pyperclip.copy(correct)
            check = False
        except:
            pass
    if keyboard.is_pressed('down'):
        check = True
