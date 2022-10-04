FROM python:3.10-slim-buster as base
ENV PYTHONUNBUFFERED 1
ENV PATH /code:/opt/venv/bin:$PATH
COPY requirements.txt ./
RUN set -ex; \
        python -m venv /opt/venv; \
        pip install --upgrade pip; \
        pip install -r requirements.txt;

# ============================================ WEB ASSETS BUILDER

FROM node:lts-alpine as webassets-builder

WORKDIR /code/youtube

COPY youtube ./
RUN npm install
RUN npm run build

# ============================================ Release

FROM python:3.10-slim-buster AS release

ENV PYTHONUNBUFFERED 1
ENV PATH /code:/opt/venv/bin:$PATH

COPY requirements.txt ./

RUN set -ex; \
        apt-get update; \
        apt-get install -y --no-install-recommends \
            ffmpeg;

WORKDIR /code
COPY --from=webassets-builder /code/youtube/static ./youtube/static
COPY --from=base /root/.cache /root/.cache
COPY --from=base /opt/venv /opt/venv

RUN mkdir -p /run/daphne
COPY manage.py supervisord.conf ./
COPY docker-entrypoint.sh /usr/local/bin

COPY playlistenerweb playlistenerweb/
COPY youtube youtube/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 9000

ENTRYPOINT ["docker-entrypoint.sh"]

# CMD ["supervisord", "-c", "supervisord.conf", "-n"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "9000", "playlistenerweb.asgi:application"]
