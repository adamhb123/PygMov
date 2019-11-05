import os
import subprocess
import wave
from _thread import start_new_thread

import pygame

pygame.mixer.pre_init(frequency=44100, size=-16, channels=1)


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

    def set_pos(self, index):
        """
        set positionof sound
        :param index: num in seconds
        :return: None
        """
        self._audio_sound = pygame.mixer.Sound(
            pygame.sndarray.array(self._audio_array[index * self._audio_frame_rate:])
        )


class VideoPlayer(object):
    FFMPEG_BINARY = "binaries/ffmpeg.exe"  # hard code path to ffmpeg
    FFPROBE_BINARY = "binaries/ffprobe.exe"  # hard code path to ffprobe
    THREAD_NUM = 4
    CHUNK_LENGTH_MS = 1000

    def __init__(self, name, path="", resolution=None, pos=(0, 0)):
        if not os.path.isfile(os.path.join(path, name)):
            raise SystemExit(f"file or path incorrect {name, path}")

        # video
        self._filename = name  # set filename
        self._path = path  # set path

        if resolution is None:
            self._resize_resolution = self.get_resolution()  # set resize resolution
        else:
            self._resize_resolution = resolution

        self.data = self.get_video_info()  # get general information
        self._fps = self.get_fps()  # set fps
        self._resolution = self.get_resolution()  # set resolution
        self._frame_buffer = []  # set frame buffer
        self._total_frames = self.get_frame_count()  # get total frame count


       # if not os.path.isfile(os.path.join(path,name)):
        self._source_file = open(os.path.join(path,name.split(".")[0]+".frames"),"wb")

        for _ in range(self._total_frames):
            self._source_file.write(pygame.image.tostring(self._read_frame(_)[0],"RGB"))
        self._source_file.close()
        # audio
        self._extract_audio()
        self._audio = AudioAdapter(self._filename, self._path)

        self._video_cursor = 0
        self._last_video_cursor = 0
        self._buffer_cursor = 0
        self._is_playing = True
        self.isrunning = True

        self._buffer_is_ready = False

        self.image = pygame.Surface(self._resize_resolution)
        self.rect = self.image.get_rect(topleft=pos)

        # time management
        self._internal_current_time = 0
        self._last_frame_tick = 0
        self._delta_time = 0

        self._preload_pattern(0, 200)  # preload pattern

    def _set_pos(self, index):
        """
        set position of video in seconds
        :param index: int
        :return: None
        """
        self._video_cursor = index  # preload and clear frames todo
        self._audio.set_pos(index)

    def _preload_pattern(self, start, end):
        """
        preload a given amount of frames
        :param index: amount of frames starting from 0
        :return:
        """
        self._frame_buffer.extend(self._read_frame(start, end))
        self._buffer_cursor = end

    # this is all wrong
    def _buffer_video_frames(self):
        """
        keep track of frames inside buffer
        :return: None
        """
        self._frame_buffer.extend(self._read_frame(self._buffer_cursor, 25))
        self._buffer_cursor += 25

    # how dare yoi

    def update(self):
        """
        mainloop running in a thread for changing frames etx
        :return: None
        """
        self._internal_current_time = pygame.time.get_ticks()
        self._delta_time = (self._internal_current_time - self._last_frame_tick) / 1000.0

        if self._is_playing:
            self._video_cursor += self._delta_time * self._fps
            if int(self._video_cursor) != self._last_video_cursor:
                if self._video_cursor <= self._total_frames:
                    self.image = self._frame_buffer[0]
                    self._frame_buffer.pop(0)
                    self._last_video_cursor = int(self._video_cursor)
                    if len(self._frame_buffer) < 225:
                        self._buffer_video_frames()

        self._last_frame_tick = self._internal_current_time
        print(len(self._frame_buffer))

    def play(self):
        """set music to play
        :return:None
        """
        self._is_playing = True

    def render(self, surface):
        """
        render frame to a certain surface
        :return:None
        """
        surface.blit(self.scale(), self.rect)

    def scale(self):
        """
        scale to the resolution
        :return: new pg image
        """
        return pygame.transform.scale(self.image, self._resize_resolution)

    @property
    def resolution(self):
        """
        get resolution
        :return: self.resolution
        """
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        """ resolution setter
        :return: None
        """
        self._resize_resolution = value

    def get_fps(self):
        """
        get the fps count of a video file
        :return: fps
        """
        command = [self.FFPROBE_BINARY,
                   '-v', '0', '-of', 'csv=p=0',
                   '-select_streams', 'v:0',
                   '-show_entries', 'stream=r_frame_rate',
                   os.path.join(self._path, self._filename)]

        return int(subprocess.check_output(command).decode("utf-8").split("/")[0])

    def get_resolution(self):
        """
        get resolution of the a video file
        :return: resolution
        """
        command = [self.FFPROBE_BINARY,
                   '-v', 'error', '-select_streams',
                   'v:0', '-show_entries',
                   'stream=width,height', '-of',
                   'csv=s=x:p=0',
                   os.path.join(self._path, self._filename)]

        return [int(res) for res in subprocess.check_output(command).decode("utf-8").split("x")]

    def get_frame_count(self):
        """
        get total frame count
        :return: total frames
        """
        command = [self.FFPROBE_BINARY,
                   '-v', 'error', '-select_streams',
                   'v:0', '-show_entries',
                   'stream=nb_frames', '-of',
                   'default=nokey=1:noprint_wrappers=1',
                   os.path.join(self._path, self._filename)]

        return int(subprocess.check_output(command).decode("utf-8"))

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

    def _read_frame(self, frame_index, num_frames=1):
        """
        read a frame from a certain position
        queue frames to buffer
        :return:None 
        """
        if frame_index + num_frames > self._total_frames:
            num_frames = self._total_frames - frame_index

        command = [self.FFMPEG_BINARY,
                   '-loglevel', 'fatal',
                   '-ss', str(frame_index / self._fps),
                   '-i', os.path.join(self._path, self._filename),
                   '-threads', str(self.THREAD_NUM),
                   '-vf', 'scale=%d:%d' % (self._resolution[0], self._resolution[1]),
                   '-vframes', str(num_frames),
                   '-f', 'image2pipe',
                   '-pix_fmt', 'rgb24',
                   '-vcodec', 'rawvideo', '-']

        pipe = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        tmplist = []
        for _ in range(num_frames):
            raw_image = pipe.stdout.read(self._resolution[0] * self._resolution[1] * 3)
            tmplist.append(pygame.image.frombuffer(raw_image, self._resolution, "RGB"))
        pipe.stdout.flush()
        return tmplist

    @staticmethod
    def __parse_probe(info_dict,output):
        """
        parses probe output
        :return:None
        """
        for n in range(len(output)):
            output[n].replace('\r','')
            try:
                info_dict['resolution'] = int(output[n]),int(output[n+1])
            except (TypeError,ValueError):
                if output[n].strip() != "0/0":
                    try:
                        int(output[n])
                    except (TypeError,ValueError):
                        if "/" in output[n]:
                            info_dict['fps'] = float(output[n].split('/')[0]) / float(output[n].split('/')[1])
                        elif len(output[n]) != 0:
                            print("O: %s" % output[n])
                            info_dict['duration'] = output[n].replace('\r','')
            except IndexError:
                pass

    def get_video_info(self):
        """
        get important video information
        :return: info dict
        """
        info_dict = {}
        command = [self.FFPROBE_BINARY,
                   '-v', 'fatal',
                   '-show_entries', 'stream=width,height,r_frame_rate,duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1',
                   os.path.join(self._path, self._filename), '-sexagesimal']

        pipe = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = pipe.communicate()
        if (err): print(err);return None;
        output = output.decode("utf-8").split('\n')
        info_dict['file'] = os.path.join(self._path, self._filename)
        self.__parse_probe(info_dict, output)
        print(output)
        print(info_dict)
        return info_dict
