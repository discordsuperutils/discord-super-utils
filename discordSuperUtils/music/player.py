from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING, List, Iterable

if TYPE_CHECKING:
    from ..youtube import YoutubeClient
    import discord


__all__ = ("Player",)


class Player:
    """
    Represents a music player.
    """

    __slots__ = (
        "data",
        "title",
        "stream_url",
        "url",
        "start_timestamp",
        "last_pause_timestamp",
        "duration",
        "requester",
        "source",
        "autoplayed",
    )

    def __init__(self, requester: Optional[discord.Member], data):
        self.source = None
        self.data = data
        self.requester = requester
        self.title = data["videoDetails"]["title"]
        self.stream_url = data.get("url")
        self.url = "https://youtube.com/watch/?v=" + data["videoDetails"]["videoId"]

        self.autoplayed = False
        self.start_timestamp = 0
        self.last_pause_timestamp = 0

        duration = int(data["videoDetails"]["lengthSeconds"])
        self.duration = duration if duration != 0 else "LIVE"

    def __str__(self):
        return self.title

    @staticmethod
    def _get_stream_url(player: dict) -> str:
        """
        Returns the stream url of a player.

        :param dict player: The player.
        :return: The stream url.
        :rtype: str
        """

        stream_urls = [
            x
            for x in sorted(
                player["streamingData"]["adaptiveFormats"],
                key=lambda x: x.get("averageBitrate", 0),
                reverse=True,
            )
            if "audio" in x["mimeType"] and "opus" not in x["mimeType"]
        ]

        return player["streamingData"].get("hlsManifestUrl") or stream_urls[0]["url"]

    @classmethod
    async def make_multiple_players(
        cls,
        youtube: YoutubeClient,
        songs: Iterable[str],
        requester: Optional[discord.Member],
    ) -> List[Player]:
        """
        |coro|

        Returns a list of players from a iterable of queries.

        :param YoutubeClient youtube: The youtube client.
        :param requester: The requester.
        :type requester: Optional[discord.Member]
        :param songs: The queries.
        :type songs: Iterable[str]
        :return: The list of created players.
        :rtype: List[Player]
        """

        tasks = [cls.fetch_song(youtube, song, playlist=False) for song in songs]

        songs = await asyncio.gather(*tasks)

        return [cls(requester, data=x[0]) for x in songs if x]

    @classmethod
    async def get_similar_videos(
        cls, video_id: str, youtube: YoutubeClient
    ) -> List[Player]:
        """
        |coro|

        Creates similar videos related to the video id.

        :param str video_id: The video id
        :param YoutubeClient youtube: The youtube client.
        :return: The list of similar players
        :rtype: List[Player]
        """

        similar_video = await youtube.get_similar_videos(video_id)
        players = await cls.make_players(
            youtube, f"https://youtube.com/watch/?v={similar_video[0]}", None, False
        )
        for player in players:
            player.autoplayed = True

        return players

    @staticmethod
    async def fetch_data(
        youtube: YoutubeClient, query: str, playlist: bool = True
    ) -> List[dict]:
        """
        |coro|

        Fetches the youtube data of the query.

        :param YoutubeClient youtube: The youtube client.
        :param bool playlist: Indicating if it should fetch playlists.
        :param str query: The query.
        :return: The youtube data.
        :rtype: Optional[dict]
        """

        return [
            x
            for x in await youtube.get_videos(
                await youtube.get_query_id(query), playlist
            )
            if "streamingData" in x
        ]

    @classmethod
    async def fetch_song(
        cls, youtube: YoutubeClient, query: str, playlist: bool = True
    ) -> List[dict]:
        """
        |coro|

        Fetches the song's or playlist's data.
        Will return the first song in the playlist if playlist is False.

        :param YoutubeClient youtube: The youtube client.
        :param query: The query.
        :type query: str
        :param playlist: A bool indicating if the function should fetch playlists or get the first video.
        :type playlist: bool
        :return: The list of songs.
        :rtype: List[dict]
        """

        data = await cls.fetch_data(youtube, query, playlist)
        if not data:
            return []

        players = []
        for player in data:
            player["url"] = cls._get_stream_url(player)
            players.append(
                {x: y for x, y in player.items() if x in ["url", "videoDetails"]}
            )

        return players

    @classmethod
    async def make_players(
        cls,
        youtube: YoutubeClient,
        query: str,
        requester: Optional[discord.Member],
        playlist: bool = True,
    ) -> List[Player]:
        """
        |coro|

        Returns a list of players from the query.

        :param YoutubeClient youtube: The youtube client.
        :param Optional[discord.Member] requester: The song requester.
        :param query: The query.
        :type query: str
        :param playlist: A bool indicating if the function should fetch playlists or get the first video.
        :type playlist: bool
        :return: The list of created players.
        :rtype: List[Player]
        """

        return [
            cls(requester, data=player)
            for player in await cls.fetch_song(youtube, query, playlist)
        ]
