import os  # os module -> for path and file checking
import subprocess  # subprocess module -> for ffmpeg communication
import wave  # wave module -> for wave file processing

import pygame  # pygame module -> for frame displaying
import platform  # get os running on

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)  # pre init pygame mixer module

if int(pygame.__version__.split(".")[0]) > 2:
    raise SystemExit("No Backwards compatibility use pygame 2.0 instead")

operating_system = platform.system()  # get os
os_release = platform.release()  # get os release


class GUIAdapter(object):
    """
    gui class wraps pygame polygon etc to create video icons
    """
    IMAGE_PATH = "resources/_images"

    def __init__(self, resolution):
        self._resolution = resolution  # assign resolution

        # play element
        self._gui_element_PLAY = pygame.image.load(os.path.join(self.IMAGE_PATH, "play.png")).convert_alpha()
        self._gui_element_PLAY = pygame.transform.scale(
            self._gui_element_PLAY, (
                self._resolution[0] // 4, self._resolution[1] // 4
            )
        )
        self._gui_element_PLAY_rect = self._gui_element_PLAY.get_rect(center=(
            self._resolution[0] // 2,
            self._resolution[1] // 2
        ))  # set position to center
        self._gui_element_PLAY.set_alpha(0)  # set alpha to zero
        self._gui_element_PLAY_alpha = 0  # store

    def resize(self, resolution):
        """
        resize elements
        :return: None
        """
        self._resolution = resolution  # assign resolution
        # play
        self._gui_element_PLAY = pygame.transform.scale(
            self._gui_element_PLAY, (
                self._resolution[0] // 4, self._resolution[1] // 4
            )
        )
        self._gui_element_PLAY_rect = self._gui_element_PLAY.get_rect(center=(
            self._resolution[0] // 2,
            self._resolution[1] // 2
        ))  # set position to center


class AudioAdapter(object):
    """
    Audio class wraps wave access and positioning
    """

    def __init__(self, filename, path):
        """
        constructor -> setting default args
        :param filename: audio filename
        :param path: audio path
        """
        # private attributes
        # Audio should only used by VideoPlayer so access is not necessary -> private attr

        self._filename = filename.split(".")[0] + ".wav"  # set filename
        self._path = path  # set path

        self._audio_file = wave.open(os.path.join(self._path, self._filename), "r")  # open the audio file
        self._audio_total_frames = self._audio_file.getnframes()  # get total frame count
        self._audio_frame_rate = self._audio_file.getframerate()  # get audio frame rate
        self._audio_channels = self._audio_file.getnchannels()  # get channels
        self._audio_sample_width = self._audio_file.getsampwidth()  # get sample width
        self._audio_raw_array = self._audio_file.readframes(self._audio_total_frames)  # read all frames into buffer
        self._audio_sound_array = pygame.sndarray.array(self._audio_raw_array)  # create sound array buffer
        self._audio_sound = pygame.mixer.Sound(self._audio_sound_array)  # initialize sound

        self._audio_is_playing = False  # boolean to control audio playback
        self._audio_is_muted = False

    def play(self):
        """
        start Audio playback
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
        property to check playing status
        :return: boolean
        """
        return self._audio_is_playing

    @property
    def is_muted(self):
        """
        returns mute state boolean
        :return: boolean
        """
        return self._audio_is_muted

    @is_muted.setter
    def is_muted(self, bool):
        """
        set mute state
        :param bool: boolean
        :return: None
        """
        self._audio_is_muted = bool

    def set_pos(self, index):
        """
        set position of sound
        :param index: num in seconds
        :return: None
        """
        index = self._audio_frame_rate * index * self._audio_channels * self._audio_sample_width  # get music index
        self._audio_sound.stop()  # stop current play back
        self._audio_sound = pygame.mixer.Sound(pygame.sndarray.array(self._audio_raw_array[index:]))
        self.play()  # start new music

    def get_volume(self):
        """
        get volume
        :return: float
        """
        return self._audio_sound.get_volume()

    def set_volume(self, vol):
        """
        set volume
        :param vol: float
        :return: None
        """
        self._audio_sound.set_volume(vol)


class VideoPlayer(object):
    """
    VideoPlayer class provides functions to play videos in pygame
    """
    if operating_system == "Windows":
        FFMPEG_BINARY = "binaries/ffmpeg.exe"  # hard code ffmpeg
        FFPROBE_BINARY = "binaries/ffprobe.exe"  # hard code ffprobe

    elif operating_system == "Linux":
        FFMPEG_BINARY = "binaries/ffmpeg"  # hard code ffmpeg
        FFPROBE_BINARY = "binaries/ffprobe"  # hard code ffprobe

    elif operating_system == "Darwin":
        FFMPEG_BINARY = "binaries/_MACOSX/._ffmpeg"  # hard code ffmpeg
        FFPROBE_BINARY = "binaries/_MACOSX/._ffprobe"  # hard code ffprobe

    else:
        raise SystemExit("Your OS seems to be not supported :/")

    THREAD_NUMBERS = 0  # set pipe threads

    def __init__(self, filename, path="", position=(0, 0), resolution=None, doVideoResize=True, doVideoConvert=True,
                 hasSound=True, bindGUI=True):
        """
        constructor -> set default args
        :param filename: filename
        :param path: path
        :param position: position where to render
        :param resolution: setting arbitrary resolution
        :param doVideoResize: boolean if video should resized once
        :param doVideoConvert: boolean if video should converted to the best format
        :param hasSound: boolean if video contains audio line
        :param bindGUI: boolean if hud should be displayed
        """
        if not os.path.isfile(os.path.join(path, filename)):  # check if file exists
            raise FileNotFoundError("File or path incorrect > ", path, filename)  # raise exit condition

        # private attributes
        self._filename = filename  # assign filename
        self._path = path  # assign file path

        if not os.path.isdir("resources"):
            os.makedirs("resources")  # create 'home' folder

        if not os.path.isdir(os.path.join("resources", "resources_" + self._filename)):
            os.makedirs("resources/resources_" + self._filename)  # create folder for video player instance

        self._destination_path = "resources/resources_" + self._filename  # set destination path

        if not self._filename.endswith(".mp4"):
            if not os.path.isfile(os.path.join(self._destination_path, filename.split(".")[0] + ".mp4")):
                if doVideoConvert:
                    self._convert_video()  # convert video to mp4 if necessary

            self._filename = self._filename.split(".")[0] + ".mp4"  # set new filename

        self._origin_filename = self._filename  # set original filename to avoid extra parsing
        self._origin_path = self._path  # set original filename to avoid extra parsing

        # video
        if resolution is not None:  # if resolution is not predefined
            if not os.path.isfile(os.path.join(self._destination_path, "SCALED_%s" % self._filename)):
                if doVideoResize:
                    self._resize_video(resolution)  # resize video
            else:
                self._filename = "SCALED_%s" % self._filename  # set new filename
                if tuple(self._get_video_resolution()) != resolution:
                    os.remove(os.path.join(self._destination_path, self._filename))  # remove scaled video
                    self._filename = self._filename[7:]
                    self._resize_video(resolution)  # force resize
                else:
                    self._filename = self._filename[7:]

            self._filename = "SCALED_%s" % self._filename  # set new filename
            self._resize_resolution = resolution  # set resize resolution

        self.video_data = self._get_video_data()  # get video data as dict

        self._fps = self.video_data["FPS"]  # get fps
        self._total_frames = self.video_data["DURATION"]  # get total frames
        self._resolution = self.video_data["RESOLUTION"]  # get video resolution
        self._frame_buffer_size = self._resolution[0] * self._resolution[1] * 3  # calculate frame buffer size
        self._video_format = "RGB"  # set video format

        # audio
        self._hasSound = hasSound
        if self._hasSound:
            self._extract_audio()  # extract video audio as wave file
            self._audio = AudioAdapter(self._origin_filename, self._destination_path)  # create audio adapter instance

        # private pygame necessary arguments
        self._image = pygame.Surface(self._resolution)  # set default surface
        self._image.fill((255, 0, 0))  # fill image red in case an error occurs
        self._rect = self._image.get_rect(topleft=position)  # define position

        # frame pipe
        self._pipe = self._open_frame_pipe(0)  # open a frame pipe from the beginning of the video

        # time management
        self._internal_current_time = 0  # init internal time
        self._delta_time = 0  # init delta time
        self._last_frame_time = 0  # init last frame time

        # video management
        self._video_cursor = 0  # current video cursor
        self._last_video_cursor = 0  # last video cursor
        self._do_resize = False  # no resize is needed
        self._video_is_playing = False  # boolean to toggle video playback
        self._first_call = True  # boolean to avoid wrong entry

        # GUI management
        if bindGUI:
            self._gui_is_enabled = True  # activate GUI
            self._gui = GUIAdapter(self._resolution)  # create GUI instance

    def play(self):
        """
        start video and audio playback
        :return: None
        """
        self._video_is_playing = True

    def stop(self):
        """
        stop video and audio playback
        :return: None
        """
        self._video_is_playing = False
        if self._hasSound:
            self._audio.stop()  # stop audio playback

    def set_position(self, index):
        """
        set video and audio position
        :param index: int
        :return: None
        """
        if self._hasSound:
            self._audio.set_pos(index)  # set audio pos

        self._pipe.terminate()
        self._pipe.kill()
        self._pipe = self._open_frame_pipe(index)  # set video pos
        self._video_cursor = index * self._fps  # set video cursor
        self._last_video_cursor = int(index * self._fps)

    @property
    def volume(self):
        """
        get volume of video
        :return: float
        """
        if self._hasSound:
            return self._audio.get_volume()

    @volume.setter
    def volume(self, vol):
        """
        set volume
        :param vol: float or int
        :return: None
        """
        if self._hasSound:
            self._audio.set_volume(vol)

    def mute(self):
        """
        mutes sound
        :return: None
        """
        if self._hasSound:
            self._audio.set_volume(0)  # set volume to 0
            self._audio.is_muted = True

    def unmute(self, vol=1):
        """
        unmutes sound
        :return: None
        """
        if self._hasSound:
            self._audio.set_volume(vol)  # set volume to 0
            self._audio.is_muted = False

    @property
    def ismuted(self):
        """
        returns muted boolean
        :return: boolean
        """

        return self._audio.is_muted

    @property
    def isplaying(self):
        """
        return playing state
        :return: boolean
        """
        return self._video_is_playing

    def pause(self):
        """
        pause video and sound
        :return: None
        """
        self._video_is_playing = False
        if self._hasSound:
            self._audio.stop()  # stop audio

    def unpause(self):
        """
        unpause video
        :return: None
        """
        self._video_is_playing = True
        self.set_position(self._last_video_cursor // self._fps)

    def update(self):
        """
        updates the frames
        :return: None
        """
        if self._first_call:
            self._first_call = False
            self._last_frame_time = pygame.time.get_ticks()  # do this once to sync video - audio

        self._internal_current_time = pygame.time.get_ticks()  # get ticks since last call in ms
        self._delta_time = (self._internal_current_time - self._last_frame_time) / 1000.0  # calc delta time

        if self._video_is_playing:
            if not self._audio.is_playing and self._hasSound and not self._audio.is_muted:
                self._audio.play()  # start audio playback

            if int(self._video_cursor) != self._last_video_cursor:

                if self._last_video_cursor < self._total_frames:
                    difference = int(self._video_cursor) - self._last_video_cursor

                    if difference > 1:
                        for _ in range(difference - 1):
                            self._read_frame()  # skips frames -> might be slow af

                    raw_frame_buffer = self._read_frame()  # read frame
                    self._image = pygame.image.frombuffer(raw_frame_buffer, self._resolution, self._video_format)

                    if self._do_resize:
                        self._image = self._scale(self._image)  # scale image if necessary

                self._last_video_cursor = int(self._video_cursor)  # update last video cursor
            self._video_cursor += self._delta_time * self._fps  # increase video cursor
        self._last_frame_time = self._internal_current_time  # set last frame time

        # gui stuff goes here
        if self._gui_is_enabled:
            pass

    def render(self, surface):
        """
        renders current frame to a surface
        :param surface: pygame Surface
        :return: None
        """
        surface.blit(self._image, self._rect)

    def _scale(self, image):
        """
        scale image to resize resolution
        :param image: pygame Surface
        :return: pygame Surface
        """
        return pygame.transform.scale(image, self._resize_resolution)

    def resize(self, resolution):
        """
        set resize resolution
        :param resolution: int w int h
        :return: None
        """
        self._resize_resolution = resolution
        self._do_resize = True

    def set_screen_position(self, position):
        """
        set the x y position
        :return: None
        """
        self._rect.topleft = position

    def _open_frame_pipe(self, index):
        """
        open ffmpeg frame pipe
        :param index: starting index
        :return: popen object
        """

        command = [
            self.FFMPEG_BINARY,
            '-loglevel', 'fatal',
            '-ss', str(index),
            '-i', os.path.join(self._destination_path, self._filename),
            '-threads', str(self.THREAD_NUMBERS),
            '-vf', 'scale=%d:%d' % (self._resolution[0], self._resolution[1]),
            '-vframes', str(self._total_frames),
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo', '-'
        ]

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _read_frame(self):
        """
        reads a frame from the pipe
        :return: raw frame data
        """
        return self._pipe.stdout.read(self._frame_buffer_size)

    def _get_video_data(self):
        """
        get video data
        :return: data dictionary
        """
        dictionary = {
            "NAME": self._filename,
            "PATH": self._path,
            "FPS": self._get_video_fps(),
            "RESOLUTION": self._get_video_resolution(),
            "DURATION": self._get_total_frames(),
        }

        return dictionary

    def _get_video_fps(self):
        """
        get fps of video
        :return: int/float
        """

        command = [
            self.FFPROBE_BINARY,
            '-v', '0', '-of', 'csv=p=0',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            os.path.join(self._destination_path, self._filename)
        ]

        fps = int(subprocess.check_output(command).decode("utf-8").split("/")[0])
        return fps / 1000 if fps > 1000 else fps

    def _get_video_resolution(self):
        """
        get video resolution
        :return: int w int h
        """
        command = [
            self.FFPROBE_BINARY,
            '-v', 'error', '-select_streams',
            'v:0', '-show_entries',
            'stream=width,height', '-of',
            'csv=s=x:p=0',
            os.path.join(self._destination_path, self._filename)
        ]

        return [int(res) for res in subprocess.check_output(command).decode("utf-8").split("x")]

    def _get_total_frames(self):
        """
        get video total frames
        :return: int
        """
        command = [
            self.FFPROBE_BINARY,
            '-v', 'error', '-select_streams',
            'v:0', '-show_entries',
            'stream=nb_frames', '-of',
            'default=nokey=1:noprint_wrappers=1',
            os.path.join(self._destination_path, self._filename)
        ]

        return int(subprocess.check_output(command).decode("utf-8"))

    def _resize_video(self, size):
        """
        resize video to
        :param size: (int w,int h)
        :return: None
        """
        print("[INFO] Resizing video > ", self._path, self._filename)
        print("[INFO] Depending on video size this may take a few minutes. One-time operation.")

        command = [
            self.FFMPEG_BINARY,
            "-loglevel", "quiet", "-stats",
            '-i', os.path.join(self._path, self._filename),
            '-threads', str(self.THREAD_NUMBERS), "-vf",
            "scale=%d:%d" % (size[0], size[1]),
            "%s/SCALED_%s" % (self._destination_path, self._filename)
        ]

        subprocess.call(command)  # call rescale command
        print("[INFO] Done.")

    def _convert_video(self):
        """
        convert video to mp4 to make it easer to access its data
        :return: None
        """
        print("[INFO] Converting video > ", self._path, self._filename)
        print("[INFO] Depending on video size this may take a few minutes. One-time operation.")
        command = [
            self.FFMPEG_BINARY,
            "-i", os.path.join(self._path, self._filename),
            "-loglevel", "quiet", "-stats",
            os.path.join(self._destination_path, self._filename.split(".")[0] + ".mp4")
        ]

        subprocess.call(command)
        print("[INFO] Done.")

    def _extract_audio(self):
        """
        extract audio of video
        :return: None
        """

        command = [
            self.FFMPEG_BINARY,
            '-loglevel', 'quiet',
            '-i', os.path.join(self._origin_path, self._origin_filename),
            '-vn', os.path.join(self._destination_path, self._origin_filename.split(".")[0] + ".wav")
        ]

        if not os.path.isfile(os.path.join(self._destination_path, self._origin_filename.split(".")[0] + ".wav")):
            subprocess.call(command)
