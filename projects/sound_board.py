from __future__ import unicode_literals
import argparse
import os
import sounddevice as sd
import numpy
import tkinter as tk
import youtube_dl

assert numpy
import soundfile as sf


def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-i', '--input-device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-o', '--output-device', type=int_or_str,
    help='output device (numeric ID or substring)')
parser.add_argument(
    '-c', '--channels', type=int, default=2,
    help='number of channels')
parser.add_argument('--dtype', help='audio data type')
parser.add_argument('--samplerate', type=float, help='sampling rate')
parser.add_argument('--blocksize', type=int, help='block size')
parser.add_argument('--latency', type=float, help='latency in seconds')
args = parser.parse_args(remaining)


def callback(indata, outdata, frames, t, status):
    if status:
        print(status)
    outdata[:] = indata
    # outdata = []


# print(sd.query_devices())  # I don't know your devices but you will see them here
# print(default.device)
# sd.default.device[0] = 1
# recording = sd.rec(frames=44100 * 5, samplerate=44100, blocking=True, channels=1)
# sd.wait()
#
#

# print('a')
# sd.play(recording, 44100, device=(1, 8), loop=True, blocking=True)
sd.default.device = 4, 12


#
# input device = VoiceMeeter Output(VB-Audio)
def PlaySound():
    if decide_sound.get() == "":
        data, fs = sf.read("loud_sound.wav", dtype='float32')
        sd.play(data, fs, loop=True)
    elif decide_sound.get() == "last":
        data, fs = sf.read("test.wav", dtype='float32')
        sd.play(data, fs, loop=True)
    else:
        # try:
        #     os.remove('test.wav')
        # except:
        #     pass

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([decide_sound.get()])
            # data, fs = sf.read("test.wav", dtype='float32')
            # sd.play(data, fs, loop=True)


def StopSound():
    sd.stop()


ydl_opts = {
    'outtmpl': 'test.wav',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192'

    }],
    # 'quiet': True

}
root = tk.Tk()
root.title("Sound Customization")
root.geometry('500x135')

decide_sound = tk.Entry(root, width=15)
decide_sound.pack()
decide_sound.place(x=350, y=60)

stop_recording = tk.Button(root, text="Start Sound", height=5, width=15, command=PlaySound)
stop_recording.pack()
stop_recording.place(x=10, y=10)

start_recording = tk.Button(root, text="Stop Sound", height=5, width=15, command=StopSound)
start_recording.pack()
start_recording.place(x=150, y=10)
with sd.Stream(
        samplerate=args.samplerate, blocksize=args.blocksize,
        dtype=args.dtype, latency=args.latency,
        channels=args.channels, callback=callback):
    root.mainloop()
