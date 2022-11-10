from .logging.YoutubeIdFilter import YoutubeIdFilter
import youtube_dl
from django.core.files.base import ContentFile
from pathlib import Path
from django.core.files import File
from django.conf import settings
from youtube_dl.utils import ExtractorError, YoutubeDLError

import logging
newlogger = logging.getLogger(__name__)
from .logging.LoggingAdapter import LoggingAdapter

class YT:
    def __init__(self, youtubeobject):
        self.youtubeobject = youtubeobject
        self.filename_mp3 = ""
        self.filepath_mp3 = ""
        self.youtube_orig = "https://youtube.com/watch?v="
        self.youtube_music = "https://music.youtube.com/watch?v="
        self.ydl_opts = {
            "writethumbnail": True,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {
                    "key": "EmbedThumbnail",
                },
            ],
            "logger": MyLogger(self.youtubeobject),
            "progress_hooks": [self.my_hook],
            "download_archive": settings.MEDIA_ROOT + "/archive",
            "keepvideo": False,
            "cachedir": False,
            # 'forcetitle':
            # True,
            # 'writeinfojson':
            # '/code/dl/' + str(mediaobject.id),
            "restrictfilenames": True,
            "outtmpl": settings.MEDIA_ROOT
            + str(self.youtubeobject.youtube_id)
            + "/%(title)s.%(ext)s",
        }

    def my_hook(self, d):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject.id})
        if d["status"] == "downloading":
            progress = (d["downloaded_bytes"] / d["total_bytes"]) * 100
            self.youtubeobject.eta = d["eta"]
            self.youtubeobject.elapsed = d["elapsed"]
            self.youtubeobject.speed = d["speed"]
            self.youtubeobject.downloadprogress = progress
            self.youtubeobject.save()
        if d["status"] == "error":
            self.youtubeobject.status = self.youtubeobject.Status.FAILED
            self.youtubeobject.save()
        if d["status"] == "finished":
            path = Path(d["filename"])
            if path.is_file():
                # print(path.name)
                # print(path.stem)
                logger.info(f"file found:{path.name} {path.stem}.mp3")
                self.filename_mp3 = path.stem + ".mp3"
                self.filepath_mp3 = (
                    str(self.youtubeobject.youtube_id) + "/" + path.stem + ".mp3"
                )
            else:
                logger.error("file not found")

    def run(self):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject.id})
        youtube_target_url = "https://youtube.com/watch?v=" + str(
            self.youtubeobject.youtube_id
        )

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            logger.info("download starting...")
            ydl.download([youtube_target_url])
            logger.info("download finished")
            path = Path(settings.MEDIA_ROOT + self.filepath_mp3)
            if path.is_file():
                logger.info(f"The file at {self.filepath_mp3} exists")
                self.youtubeobject.status = self.youtubeobject.Status.DONE
                self.youtubeobject.filename = self.filename_mp3
                self.youtubeobject.save()
            else:
                logger.error("file not found")
                self.youtubeobject.status = self.youtubeobject.Status.FAILED
                self.youtubeobject.error = "file not found"
                self.youtubeobject.save()

    def extract_info(self, is_music_url):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject.id})
        youtube_target_url = self.youtube_orig + str(self.youtubeobject.youtube_id)
        if is_music_url:
            youtube_target_url = self.youtube_music + str(self.youtubeobject.youtube_id)
        try:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                logger.info("Starting metadata extraction ...")
                extracted_info = ydl.extract_info(
                    youtube_target_url,
                    download=False,
                    ie_key=None,
                    extra_info={},
                    process=True,
                    force_generic_extractor=False,
                )
                # print(extracted_info.keys())
                try:
                    self.youtubeobject.description = extracted_info.get("description")
                    self.youtubeobject.title = extracted_info.get("title")
                    self.youtubeobject.categories = extracted_info.get("categories")
                    self.youtubeobject.tags = extracted_info.get("tags")
                except Exception as e:
                    logger.warning(f"Some metadata could not be extracted: {e}")

                # CHECK IF PLAYLIST
                if "entries" in extracted_info:
                    self.youtubeobject.is_playlist = True
                    logger.info("Playlist detected")
                    # IF PLAYLIST REPLACE EXTRACTED INFO WITH ONE ENTRY
                    extracted_info = self._extract_single_item()
                else:
                    self.youtubeobject.is_playlist = False
                    logger.info("Not a playlist")

                # CHECK IF MUSIC CATEGORY
                if "Music" in extracted_info.get("categories"):
                    self.youtubeobject.is_music = True
                    logger.info("Music Category assigned")
                    # CHECK IF artist field is present
                    if "artist" in extracted_info:
                        artist = extracted_info.get("artist")
                        self.youtubeobject.artist = artist
                        logger.info(f"Artist field found: {artist}")
                    else:
                        logger.info("Artist field not present")
                else:
                    self.youtubeobject.is_music = False
                    logger.info("Other Category assigned")
                self.youtubeobject.save()
        except Exception as e:
            raise ExtractInfoError(e)

    def _extract_single_item(self):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject.id})
        youtube_target_url = "https://youtube.com/watch?v=" + str(
            self.youtubeobject.youtube_id
        )
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            logger.info("Check single item of playlist ...")
            extracted_info = ydl.extract_info(
                youtube_target_url,
                download=False,
                ie_key=None,
                extra_info={},
                process=True,
                force_generic_extractor=False,
            )
        return extracted_info


class MyLogger(object):
    def __init__(self, youtubeobject_id) -> None:
        self.youtubeobject_id = youtubeobject_id
    def debug(self, msg):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject_id})
        if settings.DEBUG:
            logger.info(msg)
    def warning(self, msg):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject_id})
        logger.warn(msg)
    def error(self, msg):
        logger = LoggingAdapter(newlogger, {'id': self.youtubeobject_id})
        logger.error(msg)

class ExtractInfoError(Exception):
    def __init__(self, reason, message="ExtractInfoError"):
        self.message = message
        self.reason = reason
    def __str__(self):
        return f"{self.message} -> {self.reason}"

# for reference
# {'status': 'downloading', 'downloaded_bytes': 17131, 'total_bytes': 17131, 'tmpfilename':
# '/code/dl/tPEE9ZwTmy0/Shortest Video on Youtube.m4a.part', 'filename':
# '/code/dl/tPEE9ZwTmy0/Shortest Video on Youtube.m4a', 'eta': 0, 'speed':
# 128899.3488425494, 'elapsed': 0.43769383430480957, '_eta_str': '00:00',
# '_percent_str': '100.0%', '_speed_str': '125.88KiB/s', '_total_bytes_str': '16.73KiB'}
