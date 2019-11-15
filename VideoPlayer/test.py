
import pygame
from videoplayer import VideoPlayer
import random

pygame.init()
# todo create GUOI bindings

screen = pygame.display.set_mode((500, 500))
video = VideoPlayer("a.mp4",path="resources",resolution=(500,500),position=(0,0))
print(video.video_data)
video.play()
# try multiprocessing
clock = pygame.time.Clock()
press = False
lowest = 100000
highest =0
loops = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print(highest)
            print(lowest)
            pygame.quit()
            quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                if video.isplaying:
                    video.pause()
                else:
                    video.unpause()
            if event.key == pygame.K_m:
                if video.ismuted:
                    video.unmute()
                else:
                    video.mute()

            if event.key == pygame.K_UP:
                video.volume += 0.1
            if event.key == pygame.K_DOWN:
                video.volume -= 0.1

            if event.key == pygame.K_g:
                video.resize((100,100))

    video.update()
    video.render(screen)

    loops += 1
    pygame.display.flip()
    screen.fill((0,0,0))
    clock.tick()
    if clock.get_fps() < lowest and loops > 100:
        lowest = clock.get_fps()
    elif clock.get_fps() > highest:
        highest = clock.get_fps()

    pygame.display.set_caption(str(clock.get_fps()))
