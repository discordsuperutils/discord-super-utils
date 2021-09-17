import asyncio
import re
from typing import (
    Dict,
    Any,
    List,
    Optional
)
from urllib import parse

import aiohttp


__all__ = ("YoutubeClient",)


class YoutubeClient:
    """
    Represents a Youtube client that fetches music.
    """

    __slots__ = ("session",)

    # This access key is not private, and is used in ALL youtube API requests from the website (from any user).
    ACCESS_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    BASE_URL = "https://www.youtube.com/youtubei/v1"
    CONTEXT = b"{'context': {'client': {'clientName': 'ANDROID','clientVersion': '16.20'}}}"
    HEADERS = {
        'Content-Type': 'application/json',
        "User-Agent": "Mozilla/5.0",
        "accept-language": "en-US,en"
    }

    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session or aiohttp.ClientSession()

    async def request(self,
                      url: str,
                      query: Dict[str, Any],
                      headers: Dict[str, str] = None,
                      payload: bytes = CONTEXT) -> aiohttp.ClientResponse:
        """
        |coro|

        Makes a request to the url with the specified arguments.

        :param str url: The url.
        :param Dict[str, Any] query: The query values.
        :param Dict[str, Any] headers: The request headers.
        :param bytes payload: The payload to send.
        :return: The request object.
        :rtype: aiohttp.ClientResponse
        """

        headers = headers or self.HEADERS

        return await self.session.post(
            f'{url}?{parse.urlencode(query)}',
            data=payload,
            headers=headers
        )

    async def get_query_id(self, query: str) -> Optional[str]:
        """
        |coro|

        Gets the query video or playlist id.

        :param str query: The query.
        :return: The video or playlist id is applicable.
        :rtype: Optional[str]
        """

        query_arguments = dict(parse.parse_qsl(parse.urlparse(query).query))

        result_id = query_arguments.get('list') or query_arguments.get('v')
        if result_id:
            return result_id

        search = await self.search(query)
        return search[0] if search else None

    async def search(self, query: str) -> List[str]:
        """
        |coro|

        Returns the video ids found from the query.

        :param str query: The query.
        :return: The video ids.
        :rtype: List[str]
        """

        # Not using the youtube API as it is inconsistent.

        r = await self.session.get(f"https://www.youtube.com/results?search_query={query}")
        return re.findall(r"watch\?v=(\S{11})", await r.text())

    async def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        |coro|

        Returns the video IDs in the playlist.

        :param str playlist_id: The playlist id.
        :return: The video IDs.
        :rtype: List[str]
        """

        query = {
            'key': self.ACCESS_KEY,
            'contentCheckOk': True,
            'racyCheckOk': True,
            'playlistId': playlist_id
        }

        r = await self.request(f'{self.BASE_URL}/next', query=query)
        r_json = await r.json()

        # Youtube api lol
        return [x['playlistPanelVideoRenderer']['navigationEndpoint']['watchEndpoint']['videoId']
                for x in r_json['contents']['singleColumnWatchNextResults']['playlist']['playlist']['contents']]

    async def get_videos(self, video_id: str) -> List[Dict[str, Any]]:
        """
        |coro|

        Returns the videos data including title, duration, stream urls.

        :param str video_id: The video or playlist id.
        :return Dict[str, Any]: The video data.
        """

        if len(video_id) == 11:  # Video
            queries = [
                {
                    'key': self.ACCESS_KEY,
                    'videoId': video_id,
                    'contentCheckOk': True,
                    'racyCheckOk': True
                }
            ]

        else:  # Playlist
            queries = [
                {
                    'key': self.ACCESS_KEY,
                    'videoId': playlist_video_id,
                    'contentCheckOk': True,
                    'racyCheckOk': True
                } for playlist_video_id in await self.get_playlist_videos(video_id)
            ]

        return [await r.json() for r in await asyncio.gather(
            *[self.request(f'{self.BASE_URL}/player', query=query) for query in queries])]
