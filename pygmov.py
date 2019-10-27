_FFPATH = ".\dependencies"

import skvideo, pygame, sys
skvideo.setFFmpegPath(_FFPATH)
import skvideo.io
from copy import copy
from scipy.ndimage import rotate
from PIL import Image
from cv2 import resize
import numpy as np
#THIS REQUIRES THE FFMPEG BINARIES: ffmpeg.exe, ffprobe.exe


class Movie():
    def __init__(self,filename):
        mov = skvideo.io.vread(filename)
        
        self.movie = []
        self.reverse = 0
        #Cursor is used for playing the video, could be used to display only a frame
        self.cursor = 0
        self.cursor_inc = 0
        for frame in mov:
            self.movie.append(frame)
        #Need unmod movie to be able to do multiple transformations without absolutely demolishing the video quality
        self.unmodified_movie = copy(self.movie)
        self.length = len(self.movie)
    def play(self):
        self.cursor_inc = 1

    def stop(self):
        self.cursor_inc = 0

    def apply_transform(self,scale=None,rotation=0):
        self.movie = copy(self.unmodified_movie)
        for i,frame in enumerate(self.movie):
            im = Image.fromarray(frame)
            #Video is rotated by 90 no matter what to orient it properly
            im = im.rotate(rotation+90)
            self.movie[i] = np.asarray(im)
        if scale is not None:
            for i, frame in enumerate(self.movie):
                self.movie[i] = resize(frame,None,fx=scale,fy=scale)
    def blit(self, screen, pos):
        screen.blit(pygame.surfarray.make_surface(self.movie[self.cursor]),
                    pos)
        self.cursor += self.cursor_inc
        if self.cursor == self.length:
            self.cursor = 0

    def blit_frame(self, screen, pos, frame=0):
        if not frame <= self.length:
            frame = 0
            warnings.warn("At 'blit_frame' call: requested frame number greater than movie length.")
            
        screen.blit(pygame.surfarray.make_surface(self.movie[frame]),
                        pos)

def test():
    pygame.init()
    screen = pygame.display.set_mode((1280,720))
    clock = pygame.time.Clock()
    mov = Movie("rsc_testing/epicsteve.mpg")
    mov.play()
    i = 1
    while True:
        i += .05
        mov.apply_transform(scale=i,rotation=0)
        screen.fill((255,255,255))
        mov.blit(screen,(0,0))
        #mov.blit_frame(screen,(100,100),20000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                  pygame.quit()
                  sys.exit()
                  
        clock.tick(30)
        pygame.display.update()

if __name__=="__main__":
    test()

