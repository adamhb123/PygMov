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
    def __init__(self, filepath):
        print()
        d = "/"
        s = [e + d for e in filepath.split(d) if e]
        s[-1] = s[-1].replace('/','').split('.')[0]
        print(s)
        path = lts(s)
        command = "ffmpeg -i %s -ab 160k -ac 2 -ar 44100 -vn %s.mp3" % (filepath,path)
        subprocess.call(command, shell=True)
        audio = AudioSegment.from_mp3(path+'.mp3')
        array = audio.get_array_of_samples()
        array = np.asarray(array)
        a = array[0:][::2]
        b = array[1:][::2]
        array = np.array([a,b])
        s = pygame.sndarray.array(array)
        self.audio = pygame.mixer.Sound(s)
