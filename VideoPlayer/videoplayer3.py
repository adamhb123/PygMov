import os
import subprocess
import wave
import pygame

pygame.mixer.pre_init(frequency=44100, size=-16, channels=1)


class FrameBuffer(object):
    pass


class AudioAdapter(object):
    def __init__(self, filename, path=""):
        self._filename = filename
        self._path = path

        self._audio_file = wave.open(os.path.join(self._path, self._filename.split(".")[0] + ".wav"), "r")  # open wave
        self._audio_frames = self._audio_file.getnframes()  # get n frames
        self._audio_frame_rate = self._audio_file.getframerate()  # get fps
        self._audio_array = self._audio_file.readframes(self._audio_frames)  # read frames to array
        self._audio_sound_array = pygame.sndarray.array(self._audio_array)  # create sound array
        self._audio_sound = pygame.mixer.Sound(self._audio_sound_array)  # load sound

        self._audio_is_playing = False

    def set_pos(self, index):
        """
        set position of sound
        :param index: num in seconds
        :return: None
        """
        self._audio_sound = pygame.mixer.Sound(
            pygame.sndarray.array(self._audio_array[index * self._audio_frame_rate:])
        )

    def play(self):
        """
        start playback
        :return: None
        """
        self._audio_sound.play()
        self._audio_is_playing = True

    def stop(self):
        """
        stop audio playback
        :return: None
        """
        self._audio_sound.stop()
        self._audio_is_playing = False

    @property
    def is_playing(self):
        """
        returns bool
        :return: bool
        """
        return self._audio_is_playing


class VideoPlayer(object):
    FFMPEG_BINARY = "binaries/ffmpeg.exe"
    FFPROBE_BINARY = "binaries/ffprobe.exe"
    THREAD_NUM = 0

    def __init__(self, filename, path="", position=(0, 0), resolution=None):
        if not os.path.isfile(os.path.join(path, filename)):
            raise FileNotFoundError("File or Path incorrect > ", path, filename)

        # private arguments
        self._filename = filename
        self._path = path

        self.video_data = self._get_video_data()

        if resolution is None:
            self._resize_resolution = self.video_data["RESOLUTION"]  # get default video resolution to resize image
        else:
            self._resize_resolution = resolution  # set default resolution
            self._resize_video(size)

        self._fps = self.video_data["FPS"]  # get fps
        self._total_frames = self.video_data["DURATION"]  # get frame count
        self._resolution = self.video_data["RESOLUTION"]  # get video resolution

        # audio
        self._extract_audio()  # extract audio
        self._audio = AudioAdapter(self._filename, self._path)  # create audio adapter

        # private attributes
        self._image = pygame.Surface(self._resize_resolution)  # set empty surface
        self._image.fill((255, 0, 0))  # fill image in case it remains empty
        self._rect = self._image.get_rect(topleft=position)  # get boundary

        # frame pipe
        self._pipe = self._open_frame_pipe(0)  # open pipe at the beginning of the video

        # time management
        self._internal_current_time = 0
        self._delta_time = 0
        self._last_frame_time = 0

        # video management
        self._video_cursor = 0  # current video cursor
        self._last_video_cursor = 0  # last video cursor
        self._frame_buffer_size = self._resolution[0] * self._resolution[1] * 3  # set frame buffer size for rgb24
        self._image_format = "RGB"
        self._video_is_playing = False

        # audio management

    def play(self):
        """
        start video and audio call back
        :return: none
        """
        self._video_is_playing = True

    def stop(self):
        """
        stop video and audio playback
        :return: None
        """
        self._video_is_playing = False
        self._audio.stop()

    def update(self):
        """
        update time and frames
        :return: None
        """
        self._internal_current_time = pygame.time.get_ticks()
        self._delta_time = (self._internal_current_time - self._last_frame_time) / 1000.0  # calc delta time
        if self._video_is_playing:
            if not self._audio.is_playing:
                self._audio.play()
            self._video_cursor += self._delta_time * self._fps  # increase video cursor
            if int(self._video_cursor) != self._last_video_cursor:
                if self._last_video_cursor < self._total_frames:
                    self._read_frame()
                    self._last_video_cursor = int(self._video_cursor)

        self._last_frame_time = self._internal_current_time  # set last frame time

    def render(self, surface):
        """
        render image to a certain surface
        :param surface: pg.Surface
        :return: None
        """
        surface.blit(self._image, self._rect)

    def _scale(self):
        self._image = pygame.transform.scale(self._image, self._resize_resolution)

    def _read_frame(self):
        """
        read frames in async 'thread'
        :return:
        """
        if int(self._video_cursor) != self._last_video_cursor:
            if self._last_video_cursor < self._total_frames:
                raw_image_buffer = self._pipe.stdout.read(self._frame_buffer_size)
                self._image = pygame.image.frombuffer(raw_image_buffer, self._resolution, self._image_format)
                self._scale()

    def _open_frame_pipe(self, index):
        """
        open ffmpeg frame pipe at index
        :param index: start index
        :return: PIP obj
        """
        command = [self.FFMPEG_BINARY,
                   '-loglevel', 'fatal',
                   '-ss', str(index / self._fps),
                   '-i', os.path.join(self._path, self._filename),
                   '-threads', str(self.THREAD_NUM),
                   '-vf', 'scale=%d:%d' % (self._resolution[0], self._resolution[1]),
                   '-vframes', str(self._total_frames),
                   '-f', 'image2pipe',
                   '-pix_fmt', 'rgb24',
                   '-vcodec', 'rawvideo', '-']

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _get_video_data(self):
        """
        get the video data
        :return: dictionary containing video data
        """
        info_dictionary = {
            "FILE": os.path.join(self._path, self._filename),  # fill file
            "RESOLUTION": self._get_video_resolution(),  # fill video resolution
            "FPS": self._get_video_fps(),  # fill fps
            "DURATION": self._get_total_frames(),  # get total frames
        }
        return info_dictionary

    def _get_video_resolution(self):
        """
        get video resolution
        :return: (width:int , height: int)
        """
        command = [self.FFPROBE_BINARY,
                   '-v', 'error', '-select_streams',
                   'v:0', '-show_entries',
                   'stream=width,height', '-of',
                   'csv=s=x:p=0',
                   os.path.join(self._path, self._filename)]

        return [int(res) for res in subprocess.check_output(command).decode("utf-8").split("x")]

    def _get_video_fps(self):
        """
        get video frame per second
        :return: int(fps)
        """
        command = [self.FFPROBE_BINARY,
                   '-v', '0', '-of', 'csv=p=0',
                   '-select_streams', 'v:0',
                   '-show_entries', 'stream=r_frame_rate',
                   os.path.join(self._path, self._filename)]

        fps = int(subprocess.check_output(command).decode("utf-8").split("/")[0])
        return fps / 1000 if fps > 1000 else fps

    def _get_total_frames(self):
        """
        get total frame count of file
        :return: int(nFrames)
        """
        command = [self.FFPROBE_BINARY,
                   '-v', 'error', '-select_streams',
                   'v:0', '-show_entries',
                   'stream=nb_frames', '-of',
                   'default=nokey=1:noprint_wrappers=1',
                   os.path.join(self._path, self._filename)]

        return int(subprocess.check_output(command).decode("utf-8"))

    def _resize_video(self,size):
        """
        resize the video to given resolution
        :return: None
        """
        command = [self.FFMPEG_BINARY,
                   "-loglevel", "fatal",
                   os.path.join(self._path, self._filename),
                   "-vf", "scale=%d:%d" % (size[0], size[1]),
                   "SCALED_%s" % (self._filename.split["."][0])]
        self._filename = "SCALED_%s" % self._filename

    def _extract_audio(self):
        """
        get sound of the video
        :return: None
        """
        command = [self.FFMPEG_BINARY, '-loglevel', 'quiet',
                   '-i', os.path.join(self._path, self._filename),
                   '-vn', os.path.join(self._path, self._filename.split(".")[0] + ".wav")]

        if not os.path.isfile(os.path.join(self._path, self._filename.split(".")[0] + ".wav")):
            subprocess.call(command)
