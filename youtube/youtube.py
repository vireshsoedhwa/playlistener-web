from .logging.YoutubeIdFilter import YoutubeIdFilter
import youtube_dl
from django.core.files.base import ContentFile
from pathlib import Path
from django.core.files import File
from django.conf import settings
from youtube_dl.utils import ExtractorError, YoutubeDLError

import logging
logger = logging.getLogger(__name__)


class YT:
    def __init__(self, youtube_url, youtube_id=None, youtubeobject=None):
        self.youtubeobject = youtubeobject
        self.filename_mp3 = ""
        self.filepath_mp3 = ""
        self.youtube_id = youtube_id
        self.youtube_url = youtube_url

        self.ydl_opts = {
            'writethumbnail': True,
            'format':
            'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
                {'key': 'EmbedThumbnail', }],
            'logger':
            MyLogger(),
            'progress_hooks': [self.my_hook],
            'download_archive':
            settings.MEDIA_ROOT + '/archive',
            'keepvideo': False,
            'cachedir': False,
            # 'forcetitle':
            # True,
            # 'writeinfojson':
            # '/code/dl/' + str(mediaobject.id),
            'restrictfilenames': True,
            'outtmpl': settings.MEDIA_ROOT + str(youtube_id) + '/%(title)s.%(ext)s',
        }
        # loggingfilter = YoutubeIdFilter(youtuberesource=youtubeobject)
        # logger.addFilter(loggingfilter)

    def my_hook(self, d):
        if d['status'] == 'downloading':
            progress = (d['downloaded_bytes']/d['total_bytes'])*100
            self.youtubeobject.eta = d['eta']
            self.youtubeobject.elapsed = d['elapsed']
            self.youtubeobject.speed = d['speed']
            self.youtubeobject.downloadprogress = progress
            self.youtubeobject.save()
        if d['status'] == 'error':
            self.youtubeobject.status = self.youtubeobject.Status.FAILED
            self.youtubeobject.save()
        if d['status'] == 'finished':
            path = Path(d['filename'])
            if path.is_file():
                # print(path.name)
                # print(path.stem)
                self.filename_mp3 = path.stem + '.mp3'
                self.filepath_mp3 = str(
                    self.youtubeobject.youtube_id) + '/' + path.stem + '.mp3'

    # def run(self):
    #     youtube_target_url = "https://youtube.com/watch?v=" + \
    #         str(self.youtubeobject.youtube_id)

    #     with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
    #         extracted_info = None
    #         extracted_info = ydl.extract_info(youtube_target_url,
    #                                           download=False,
    #                                           ie_key=None,
    #                                           extra_info={},
    #                                           process=True,
    #                                           force_generic_extractor=False)
    #         # check if genre is there
    #         try:
    #             self.youtubeobject.genre = extracted_info["genre"]
    #             logger.info("genre found")
    #         except:
    #             logger.info("genre not available")

    #         self.youtubeobject.title = extracted_info["title"]
    #         self.youtubeobject.description = extracted_info["description"]
    #         self.youtubeobject.save()

    #         ydl.download([youtube_target_url])

    #         path = Path(settings.MEDIA_ROOT + self.filepath_mp3)
    #         if path.is_file():
    #             # print(f'The file at {self.filepath_mp3} exists')
    #             with path.open(mode='rb') as f:
    #                 # self.mediaobject.audiofile = File(f, path.name)
    #                 # self.mediaobject.audiofile.name = path.name
    #                 self.youtubeobject.status = self.youtubeobject.Status.DONE
    #                 self.youtubeobject.filename = self.filename_mp3
    #                 self.youtubeobject.save()
    #                 return True
    #         else:
    #             self.youtubeobject.status = self.youtubeobject.Status.FAILED
    #             self.youtubeobject.error = "Failed to download file"
    #             self.youtubeobject.save()

    def extract_info(self):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            # extracted_info = None
            extracted_info = ydl.extract_info(self.youtube_url,
                                              download=False,
                                              ie_key=None,
                                              extra_info={},
                                              process=True,
                                              force_generic_extractor=False)
            return extracted_info


class MyLogger(object):

    def debug(self, msg):
        if settings.DEBUG:
            # logger.info(msg)
            pass

    def warning(self, msg):
        # logger.warn(msg)
        pass

    def error(self, msg):
        # logger.error(msg)
        pass


# for reference
# {'status': 'downloading', 'downloaded_bytes': 17131, 'total_bytes': 17131, 'tmpfilename':
# '/code/dl/tPEE9ZwTmy0/Shortest Video on Youtube.m4a.part', 'filename':
# '/code/dl/tPEE9ZwTmy0/Shortest Video on Youtube.m4a', 'eta': 0, 'speed':
# 128899.3488425494, 'elapsed': 0.43769383430480957, '_eta_str': '00:00',
# '_percent_str': '100.0%', '_speed_str': '125.88KiB/s', '_total_bytes_str': '16.73KiB'}
