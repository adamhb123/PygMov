import subprocess
from pydub import AudioSegment
import numpy as np
import pygame
pygame.init()
pygame.mixer.init()

def lts(l):
    s = ""
    for x in l:
        s += str(x)
    return s


class Audio():
    def __init__(self, filepath, framerate):
        print()
        d = "/"
        s = [e + d for e in filepath.split(d) if e]
        s[-1] = s[-1].replace('/','').split('.')[0]
        print(s)
        path = lts(s)
        command = "ffmpeg -nostdin -n -i %s -ab 160k -ac 2 -ar 44100 -vn %s.mp3" % (filepath,path)
        subprocess.call(command, shell=True)
        audio = AudioSegment.from_mp3(path+'.mp3')
        self.audio = pygame.mixer.Sound(audio.raw_data)
