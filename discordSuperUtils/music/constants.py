import re

import youtube_dl

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

SPOTIFY_RE = re.compile("^https://open.spotify.com/")
DEEZER_RE = re.compile("^https://deezer.page.link/")
SOUNDCLOUD_RE = re.compile("^https://soundcloud.com/")

YTDL_OPTS = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": False,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
}
YTDL = youtube_dl.YoutubeDL(YTDL_OPTS)
