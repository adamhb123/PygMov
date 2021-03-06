import skvideo, pygame, sys
import skvideo.io
from threading import Thread
from copy import copy
from audio import Audio
import warnings
import datetime

#TESTING VIDEOPLAYER
import videoplayer


pygame.init()
pygame.mixer.init()

cursor, cursor_inc = 0, 0


# THIS REQUIRES THE FFMPEG BINARIES: ffmpeg.exe, ffprobe.exe

def cursor_loop(framerate, length, audio):
    global cursor_inc, cursor
    c = pygame.time.Clock()
    #   FOR SYNCING
    secs_per_frame = 1 / framerate
    playing = False
    while True:
        #   NOT DONE HERE
        #   print("Music pos: %d")
        if cursor_inc != 0 and not playing:
            if isinstance(audio, str):
                if pygame.mixer.music.get_pos() != -1:
                    pygame.mixer.music.unpause()
                else:
                    print("Playing music")
                    pygame.mixer.music.play()
            else:
                audio.play()
            cursor = 0
            playing = True
        elif cursor_inc == 0:
            if isinstance(audio, str):
                pygame.mixer.music.pause()
            else:
                audio.stop()
            playing = False

        cursor += cursor_inc
        if cursor == length:
            if isinstance(audio, str):
                pygame.mixer.music.rewind()
            else:
                audio.stop()
                audio.play()
            cursor = 0
        c.tick(framerate)


class Movie():
    def __init__(self, name, filepath, audio_as_sound=False):
        self.movie = []
        vr = skvideo.io.vreader(filepath)
        self.framerate = skvideo.io.ffprobe(filepath)['video']['@avg_frame_rate'].split('/')
        self.framerate = float(int(self.framerate[0]) / int(self.framerate[1]))
        print("FR: %s" % self.framerate)
        start = datetime.datetime.now()
        for frame in vr:
            surface = pygame.surfarray.make_surface(frame)
            surface = pygame.transform.rotate(surface, -90)
            surface = pygame.transform.flip(surface, True, False)
            self.movie.append(surface)
        end = datetime.datetime.now()
        print(end - start)
        self.audio = Audio(filepath, as_sound=audio_as_sound)
        self.length = len(self.movie)
        cursor_loop_thread = Thread(target=cursor_loop, args=(self.framerate, self.length, self.audio.audio))
        cursor_loop_thread.start()
        self.unmodified_movie = copy(self.movie)
        print("Movie len: %d" % self.length)

    def set_rotation(self, angle):
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.rotate(self.unmodified_movie[x], angle - 90)

    def set_scale(self, factor):
        w, h = self.movie[0].get_size()
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.scale(self.unmodified_movie[x], (w * factor, h * factor))

    def set_flip(self, bool_x=0, bool_y=0):
        for x in range(len(self.movie)):
            self.movie[x] = pygame.transform.flip(self.unmodified_movie[x], bool_x, bool_y)

    def play(self):
        global cursor_inc
        cursor_inc = 1

    def stop(self):
        global cursor_inc
        cursor_inc = 0

    def blit(self, surface, pos):
        global cursor

        surface.blit(self.movie[cursor], pos)
        # print(self.length,cursor)

    def blit_frame(self, surface, pos, frame=0):
        if not frame <= self.length:
            frame = 0
            warnings.warn("At 'blit_frame' call: requested frame number greater than movie length.")

        surface.blit(self.movie[frame], pos)


def test():
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    #mov = Movie("Clockwork", "rsc_testing/fsf.mp4")
    #mov.play()
    player = videoplayer.VideoPlayer("fbms.mp4","rsc_testing")
    Thread(target=player.update()).start()
    while True:
        screen.fill((255, 255, 255))
        player.render(screen)

        #mov.blit(screen, (0, 0))
        # mov.blit_frame(screen,(100,100),20000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                pygame.mixer.quit()
                sys.exit()

        clock.tick(60)
        pygame.display.update()


if __name__ == "__main__":
    test()
