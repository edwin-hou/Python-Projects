from PIL import Image
import numpy
import cv2
import pyvirtualcam
import mss
import dxcam

sct = mss.mss()

# monitor = {'top': 130, 'left': 0, 'width': 1919, 'height': 1020}
monitor = {'top': 0, 'left': 0, 'width': 1919, 'height': 1200}
camera = dxcam.create(output_color='BGR')


def rgba2rgb(rgba, background=(255, 255, 255)):
    row, col, ch = rgba.shape

    if ch == 3:
        return rgba

    assert ch == 4, 'RGBA image has 4 channels.'

    rgb = numpy.zeros((row, col, 3), dtype='float32')
    r, g, b, a = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2], rgba[:, :, 3]

    a = numpy.asarray(a, dtype='float32') / 255.0

    R, G, B = background
    rgb[:, :, 0] = r * a + (1.0 - a) * R
    rgb[:, :, 1] = g * a + (1.0 - a) * G
    rgb[:, :, 2] = b * a + (1.0 - a) * B

    return numpy.asarray(rgb, dtype='uint8')

frame = camera.grab()
fmt = pyvirtualcam.PixelFormat.BGR
with pyvirtualcam.Camera(width=1280, height=720, fps=30, device='OBS Virtual Camera', fmt=fmt) as cam:
    while True:
        new_frame = camera.grab()
        # print(type(new_frame))
        if type(new_frame)==numpy.ndarray:
            frame = new_frame
        else:
            new_frame = frame
        img = numpy.array(frame)
        # img = rgba2rgb(img)
        img = cv2.resize(img, (1280, 720))
        # img = cv2.flip(img, 1)
        data = numpy.asarray(img, dtype="uint8")
        cam.send(data)
        cam.sleep_until_next_frame()
        cv2.imshow('a', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
