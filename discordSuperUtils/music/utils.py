from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .playlist import Playlist
from .constants import *

if TYPE_CHECKING:
    from ..spotify import SpotifyClient
    from ..youtube import YoutubeClient


async def get_playlist(
    spotify: SpotifyClient, youtube: YoutubeClient, url: str
) -> Optional[Playlist]:
    if SPOTIFY_RE.match(url) and spotify:
        spotify_info = await spotify.fetch_full_playlist(url)
        return Playlist.from_spotify_dict(spotify_info) if spotify_info else None

    playlist_info = await youtube.get_playlist_information(
        await youtube.get_query_id(url)
    )
    return Playlist.from_youtube_dict(playlist_info) if playlist_info else None
