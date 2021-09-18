import asyncio
from typing import Optional, List, Dict, Union

import spotipy
from spotipy import SpotifyClientCredentials

FIELD = "items.track.name,items.track.artists(name),total"


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, loop=None):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )
        self.loop = asyncio.get_event_loop() if loop is None else loop

    @staticmethod
    def get_type(url: str) -> Optional[str]:
        """
        This function receives a url and returns the type of the URL.
        Return examples: playlist, user, album, etc.

        :param url:
        :return:
        """
        url = url.replace("https://open.spotify.com/", "")
        return url.split("/")[-2]

    @staticmethod
    def make_title(song: Dict[str, dict]) -> str:
        """
        This function receives a song and creates a title that can be used for youtube_dl searching.
        Return example: Never Gonna Give You Up by Rick Astley

        :param song:
        :return:
        """
        artists = " ".join([artist["name"] for artist in song.get("artists")])
        return f"{song['name']} by {artists}"

    async def fetch_playlist_data(
        self, url: str, offset: int
    ) -> Dict[str, Union[int, list]]:
        """
        This function receives a URL and an offset and returns 100 tracks from that offset
        Example: Offset: 50, the URL has 160 tracks, returns tracks from 50-150 (limit is 100).

        :param url:
        :param offset:
        :return:
        """

        return await self.loop.run_in_executor(
            None,
            lambda: self.sp.playlist_items(
                playlist_id=url, fields=FIELD, offset=offset
            ),
        )

    async def fetch_full_playlist(self, url: str) -> List[Dict[str, dict]]:
        """
        This function receives a url and returns all the tracks in that URL.

        :param url:
        :return:
        """

        initial_request = await self.fetch_playlist_data(url, 0)
        total_tracks = initial_request.get("total")

        requests = list(
            await asyncio.gather(
                *(
                    self.fetch_playlist_data(url, offset)
                    for offset in range(100, total_tracks, 100)
                )
            )
        )
        requests.insert(0, initial_request)
        result_tracks = []

        for request in requests:
            result_tracks += request.get("items")

        return result_tracks

    async def get_songs(self, url: str) -> List[str]:
        """
        This function receives a URL and returns all the tracks in that URL.

        :param url:
        :return:
        """

        playlist_type = self.get_type(url)
        songs = []

        if playlist_type == "playlist":
            return [
                self.make_title(song["track"])
                for song in await self.fetch_full_playlist(url)
            ]

        if playlist_type == "track":
            songs = [
                await self.loop.run_in_executor(
                    None, lambda: self.sp.track(track_id=url)
                )
            ]

        if playlist_type == "album":
            album = await self.loop.run_in_executor(
                None, lambda: self.sp.album_tracks(album_id=url, limit=50)
            )
            songs = album.get("items")

        return [self.make_title(song) for song in songs]
