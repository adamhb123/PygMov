import skvideo, pygame, sys
import skvideo.io
from copy import copy
from audio import Audio
import warnings
pygame.init()
pygame.mixer.init()

# THIS REQUIRES THE FFMPEG BINARIES: ffmpeg.exe, ffprobe.exe


class Movie():
    def __init__(self, filepath):
        self.movie = []
        self.reverse = 0
        self.cursor = 0
        self.cursor_inc = 0
        vr = skvideo.io.vreader(filepath)
        for frame in vr:
            surface = pygame.surfarray.make_surface(frame)
            surface = pygame.transform.rotate(surface, -90)
            surface = pygame.transform.flip(surface,True,False)
            self.movie.append(surface)
        self.unmodified_movie = copy(self.movie)
        self.length = len(self.movie)
        self.audio = Audio(filepath)

    def set_rotation(self,angle):
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.rotate(self.unmodified_movie[x], angle-90)

    def set_scale(self, factor):
        w,h = self.movie[0].get_size()
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.scale(self.unmodified_movie[x],(w*factor,h*factor))

    def set_flip(self,bool_x=0,bool_y=0):
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.flip(self.unmodified_movie[x],bool_x,bool_y)

    def play(self):
        self.audio.audio.play()
        self.cursor_inc = 1

    def stop(self):
        self.cursor_inc = 0

    def blit(self, surface, pos):
        surface.blit(self.movie[self.cursor], pos)
        self.cursor += self.cursor_inc
        if self.cursor == self.length:
            self.audio.audio.stop()
            self.cursor = 0
            if self.audio is not None:
                self.audio.audio.play()

    def blit_frame(self, surface, pos, frame=0):
        if not frame <= self.length:
            frame = 0
            warnings.warn("At 'blit_frame' call: requested frame number greater than movie length.")

        surface.blit(self.movie[frame], pos)


def test():

    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    mov = Movie("rsc_testing/aco.mp4")
    mov.play()
    while True:
        screen.fill((255, 255, 255))
        mov.blit(screen, (0, 0))
        # mov.blit_frame(screen,(100,100),20000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        #   Has to be adjusted to fit the video...need to be able to adjust the video framerate to match the user
        #   defined framerate (ex 24->60 fps)
        clock.tick(25)
        pygame.display.update()


if __name__ == "__main__":
    test()
