import time
from django.core.files.base import ContentFile
from django.core.files import File
from django.conf import settings
from .youtube import YT
import time
from pathlib import Path
from youtube_dl.utils import ExtractorError, YoutubeDLError

import requests
import re

import logging
newlogger = logging.getLogger(__name__)
from .logging.LoggingAdapter import LoggingAdapter

def get_video(instance):
    logger = LoggingAdapter(newlogger, {'id': instance.id})
    try:
        logger.info("Download Task starting")
        instance.status = instance.Status.BUSY
        instance.save()
        youtube_process = YT(instance)
        logger.info("Extracting Metadata ...")    

        try:
            youtube_process.extract_info(is_music_url=True)
            logger.info("succesfully extracted using music url ...")
        except Exception as ex:
            logger.error(ex)
            logger.info("music url not available...trying regular url")
            try:
                youtube_process.extract_info(is_music_url=False)
            except Exception as ey:
                logger.error(f"regular url failed: {ey}")
                raise Exception(ey)
            
        logger.info("Finished extracting metadata ...")
        logger.info("Running download process ...")
        youtube_process.run()
        logger.info("Finished download process ...")
    except YoutubeDLError as ex:
        logger.error(f"YoutubeDL error: {ex}")
        instance.error = ex.args
        instance.status = instance.Status.FAILED
        instance.save()
    except Exception as e:
        logger.error(f"YoutubeDL general error: {e}")
        instance.error = str(e)
        instance.status = instance.Status.FAILED
        instance.save()


def archive_oldest():
    from .models import YoutubeResource
    grab_only_music = YoutubeResource.objects.filter(is_music=True).filter(
        is_playlist=False
    )
    grab_only_done = grab_only_music.filter(status=YoutubeResource.Status.DONE)
    if len(grab_only_done) == 0:
        newlogger.info(f"Nothing to archive")
    else:
        oldest = grab_only_done.order_by("created_at")[0]
        oldest.status = oldest.Status.ARCHIVE
        oldest.save()
        newlogger.info(f"Archiving : {oldest.id}")


def archive(instance):
    logger = LoggingAdapter(newlogger, {'id': instance.id})
    # check if Needs review
    if instance.status == instance.Status.REVIEW:
        raise ArchiveError("Needs review before archiving")

    # check if Done. Review done or download done
    if not instance.status == instance.Status.ARCHIVE:
        raise ArchiveError("not ready for archive")
    # check if audiofile is there
    path = Path(
        settings.MEDIA_ROOT + str(instance.youtube_id) + "/" + instance.filename
    )
    if not path.is_file():
        raise ArchiveError(instance, "file is missing")
    
    logger.info("Audio file is present")

    # check if music
    if not instance.is_music:
        raise ArchiveError(instance, "not Music category")
    logger.info("is Music category")

    # check if title is available
    if instance.title == None:
        raise ArchiveError(instance, "title is missing")


    # # check if artist exists
    # if instance.artist == None or instance.artist == "":
    #     # check if title exists
    #     if instance.title == None:
    #         raise ArchiveError(instance, "title is missing")
    #     else:
    #         # check if tags
    #         possible_artist = None
    #         x = re.search(r"(^.*)-", instance.title)
    #         if x is None:
    #             raise ArchiveError(instance, "Could not derive artist from title")
    #         else:
    #             possible_artist = x.group(1).strip()
    #             if not instance.tags == None:
    #                 for tag in instance.tags:
    #                     if possible_artist.lower() in tag.lower():
    #                         instance.artist = possible_artist
    #                         break
    #                     else:
    #                         instance.status = instance.Status.REVIEW
    #                         instance.error = "Could not derive artist from title"
    #                         instance.save()
    #                         return
    #             else:
    #                 instance.status = instance.Status.REVIEW
    #                 instance.error = "no tags present"
    #                 instance.save()
    #                 return
    

    if instance.status == instance.Status.ARCHIVE:
        values = {}
        values["title"] = instance.title
        artists = []
        artists.append(instance.artist)
        tags = []
        if not instance.tags == None:
            for tag in instance.tags:
                tags.append(tag)
        values["tags"] = tags
        values["artists"] = artists
        values["description"] = instance.description

        url_create = "http://" + settings.PLAPI_PATH + "/mediaresources/"
        logger.info(f"API: {url_create}")
        try:
            r1 = requests.post(
                url_create, files={"audiofile": path.open(mode="rb")}, data=values
            )
            if r1.status_code == requests.codes.created:
                logger.info("mediaresource created on Archive backend")
                instance.status = instance.Status.ARCHIVED
                instance.save()
            else:
                instance.status = instance.Status.REVIEW
                instance.save()
        except Exception as e:
            logger.error(f"Failed to Archive {e}")
            instance.status = instance.Status.REVIEW
            instance.save()
            raise ArchiveError(e)

    else:
        instance.status = instance.Status.REVIEW
        instance.save()
        logger.info(f"Needs review")
        return

    logger.info("Archive finished succesfully")


class ArchiveError(Exception):
    def __init__(self, reason, message="ArchiveError"):
        self.message = message
        self.reason = reason
    def __str__(self):
        return f"{self.message} -> {self.reason}"
