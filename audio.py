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
    def __init__(self, filepath, as_sound=False):
        d = "/"
        s = [e + d for e in filepath.split(d) if e]
        s[-1] = s[-1].replace('/','').split('.')[0]
        print(s)
        path = lts(s)
        pull_mp3_command = "ffmpeg -nostdin -n -i %s -ab 160k -ac 2 -ar 44100 -vn %s.mp3" % (filepath,path)
        subprocess.call(pull_mp3_command, shell=True)
        if as_sound:
            audio = AudioSegment.from_mp3(path+'.mp3')
            version = pygame.version.vernum[0]
            print("Pygame major version %d." % version)
            if version == 2:
                self.audio = pygame.mixer.Sound(audio.raw_data)
            else:
                audio = audio.get_array_of_samples()
                audio = np.asarray(audio)
                a = audio[0:][::2]
                b = audio[1:][::2]
                array = np.array([a, b])

                self.audio = pygame.mixer.Sound(pygame.sndarray.array(array))
        else:
            pygame.mixer.music.load(path + '.mp3')
            self.audio = path + '.mp3'
