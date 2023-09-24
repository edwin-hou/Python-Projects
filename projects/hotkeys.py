import win32api
import time
import mouse
import tkinter as tk
import keyboard
import pyautogui
import ctypes, time
import win32gui, win32api, win32con, ctypes

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions


PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def addKey(key, id):
    global keys, del_keys
    contain = False
    for el in keys:
        if el['id'] == id:
            contain = True
    if not contain:
        entry = {}
        entry['key'] = key
        entry['time'] = time.time()
        entry['pressed'] = False
        entry['released'] = False
        entry['id'] = id
        keys.append(entry)


def KeyPress():
    global delta_time, ready, keys, click_ready
    if keys != []:
        el = keys[0]
        # if time.time() - delta_time >= 0.03:
        if el['pressed'] == False and el['key'] != 'click':  #
            delta_time = time.time()
            ready = False
            PressKey(el['key'])
            el['pressed'] = True
            el['time'] = time.time()

        if el['pressed'] == False and el['key'] == 'click':
            delta_time = time.time()
            ready = False
            ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
            el['pressed'] = True
            el['time'] = time.time()


def clearKeys(key=''):
    global keys

    if key == '':
        keys = []
    for el in keys:
        if el['key'] == key:
            keys.remove(el)


def click():
    addKey('click', 'click')


def Release():
    global ready, keys
    if keys == []:
        ready = True
    else:
        el = keys[0]
        if el['pressed'] == True and el['key'] != 'click' and time.time() - el['time'] >= 0.01:
            ready = True
            ReleaseKey(el['key'])
            keys.pop(0)
            # break
        if el['pressed'] == True and el['key'] == 'click' and time.time() - el['time'] >= 0.01:
            ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
            ready = True
            keys.pop(0)
            # break
        # keys.pop(0)


keys = []
click_ready = True
ready = True
delta_time = time.time()
mouse_down = False
key_down = False
click_time = time.time()
key_time = time.time()
delete = False
upgrade = True
clear_del_que = False
del_time = time.time()
previousmousestate = win32api.GetKeyState(0x01)

while True:
    # print(win32api.GetKeyState(0x06), win32api.GetKeyState(0x05))
    if (win32api.GetKeyState(0x05) < 0 or win32api.GetKeyState(0x06) < 0) and win32api.GetKeyState(
            0x01) >= 0 and previousmousestate != win32api.GetKeyState(0x01):
        previousmousestate = win32api.GetKeyState(0x01)
        delete = True
    if win32api.GetKeyState(0x01) >= 0:
        previousmousestate = win32api.GetKeyState(0x01)
    if not (win32api.GetKeyState(0x05) < 0 or win32api.GetKeyState(0x06) < 0):
        # if time.time() - del_time >= 0.1 and clear_del_que == False:
        #     clear_del_que = True
        #     clearKeys(14)
        delete = False
    if win32api.GetKeyState(0x02) < 0:
        if upgrade == True:
            clearKeys(14)
        click()
        addKey(52, '.1')
        addKey(52, '.2')
        addKey(52, '.3')
        addKey(52, '.4')
        for i in range(2, 6):
            addKey(i, i)
    else:
        upgrade = True
        # clearKeys(52)
        # clearKeys(1)
        # clearKeys(2)
        # clearKeys(3)
        # clearKeys(4)
        # clearKeys(5)
        # clearKeys('click')
    if delete:
        # del_time = time.time()
        # clear_del_que = False
        addKey(14, 'del')
        addKey(14, 'del1')
        addKey(14, 'del2')
        addKey(14, 'del3')
        addKey(14, 'del4')
        addKey(14, 'del5')
        addKey(14, 'del6')
        addKey(14, 'del7')

    KeyPress()
    Release()
