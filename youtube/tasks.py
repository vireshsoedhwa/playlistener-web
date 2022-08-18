# import youtube_dl
import time
# from .models import DownloadProgress
from django.core.files.base import ContentFile
from django.core.files import File
from django.conf import settings
from .youtube import YT
from .helper import create_hash
import time
import os
from pathlib import Path
from youtube_dl.utils import ExtractorError, YoutubeDLError

import logging
logger = logging.getLogger(__name__)


def get_video(mediaresource):

    try:
        youtube_process = YT(mediaresource)
        youtube_process.run()
    except YoutubeDLError as ex:
        logger.error("YoutubeDL error")
        mediaresource.youtubedata.error = ex.args
        mediaresource.youtubedata.save()
        mediaresource.save()
    # check if file is there
    try:
        path = Path(mediaresource.audiofile.path)
        if path.is_file():

            # add md5 to mediaresource record
            mediaresource.md5_generated = create_hash(
                mediaresource.audiofile.path)
            mediaresource.save()

            # delete archive file that youtube dl creates
            if os.path.exists(settings.MEDIA_ROOT + str(mediaresource.id) + '/archive'):
                os.remove(settings.MEDIA_ROOT +
                          str(mediaresource.id) + '/archive')
                logger.info("deleting youtubedl archive file")

            if os.path.exists(settings.MEDIA_ROOT + str(mediaresource.id) + '/temp/' + path.name):
                os.remove(settings.MEDIA_ROOT +
                          str(mediaresource.id) + '/temp/' + path.name)
                os.rmdir(settings.MEDIA_ROOT + str(mediaresource.id) + '/temp')
                logger.info("deleting temp mp3 file")
    except:
        logger.error("file missing")
