import asyncio
import re
from typing import Dict, Any, List, Optional
from urllib import parse

import aiohttp

__all__ = ("YoutubeClient",)


class YoutubeClient:
    """
    Represents a Youtube client that fetches music.
    """

    __slots__ = ("session", "timeout", "loop")

    # This access key is not private, and is used in ALL youtube API requests from the website (from any user).
    ACCESS_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    BASE_URL = "https://www.youtube.com/youtubei/v1"
    CONTEXT = (
        b"{'context': {'client': {'clientName': 'ANDROID','clientVersion': '16.20'}}}"
    )
    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "accept-language": "en-US,en",
    }

    def __init__(
        self,
        session: aiohttp.ClientSession = None,
        loop: asyncio.AbstractEventLoop = None,
        timeout: int = 10,
    ):
        self.timeout = timeout
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout, connect=3), loop=self.loop
        )

    async def request(
        self,
        url: str,
        query: Dict[str, Any],
        headers: Dict[str, str] = None,
        payload: bytes = CONTEXT,
    ) -> Optional[aiohttp.ClientResponse]:
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

        try:
            return await self.session.post(
                f"{url}?{parse.urlencode(query)}", data=payload, headers=headers
            )
        except asyncio.exceptions.TimeoutError:
            return None

    async def get_query_id(self, query: str) -> Optional[str]:
        """
        |coro|

        Gets the query video or playlist id.

        :param str query: The query.
        :return: The video or playlist id is applicable.
        :rtype: Optional[str]
        """

        query_arguments = dict(parse.parse_qsl(parse.urlparse(query).query))

        result_id = query_arguments.get("list") or query_arguments.get("v")
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

        try:
            r = await self.session.get(
                f"https://www.youtube.com/results?search_query={query}"
            )
        except asyncio.exceptions.TimeoutError:
            return []

        return re.findall(r"watch\?v=(\S{11})", await r.text())

    async def get_similar_videos(self, video_id: str) -> List[str]:
        """
        |coro|

        Returns similar videos to the video id.
        Simply returns the suggestions in the suggestions section when watching a video.

        :param str video_id: The video id.
        :return: The list of similar videos.
        :rtype: List[str]
        """

        query = {
            "key": self.ACCESS_KEY,
            "contentCheckOk": True,
            "racyCheckOk": True,
            "videoId": video_id,
        }

        r = await self.request(f"{self.BASE_URL}/next", query=query)
        if not r:
            return []

        r_json = await r.json()

        suggestions_list = r_json["contents"]["singleColumnWatchNextResults"][
            "results"
        ]["results"]["contents"]

        suggestions = {}
        for suggestion_object in suggestions_list:
            if "shelfRenderer" in suggestion_object:
                suggestions = suggestion_object
                break

        return [
            x["gridVideoRenderer"]["videoId"]
            for x in suggestions["shelfRenderer"]["content"]["horizontalListRenderer"][
                "items"
            ]
            if "gridVideoRenderer" in x
        ]

    async def get_playlist_information(self, playlist_id: str) -> Dict:
        """
        |coro|

        Returns the playlist information.

        :param str playlist_id: The playlist id.
        :return: The playlist information.
        :rtype: Dict
        """

        query = {
            "key": self.ACCESS_KEY,
            "contentCheckOk": True,
            "racyCheckOk": True,
            "playlistId": playlist_id,
        }

        r = await self.request(f"{self.BASE_URL}/next", query=query)
        if not r:
            return {}

        r_json = await r.json()

        if "contents" not in r_json:
            return {}

        playlist_info = r_json["contents"]["singleColumnWatchNextResults"]["playlist"][
            "playlist"
        ]

        playlist_information = {
            x: y for x, y in playlist_info.items() if not isinstance(y, (dict, list))
        }

        author_information = playlist_info["longBylineText"]["runs"][0]

        playlist_information["songs"] = [
            x["playlistPanelVideoRenderer"]["navigationEndpoint"]["watchEndpoint"][
                "videoId"
            ]
            for x in playlist_info["contents"]
        ]

        playlist_information["channel"] = {
            "name": author_information["text"],
            "id": author_information["navigationEndpoint"]["browseEndpoint"][
                "browseId"
            ],
        }

        return playlist_information

    async def get_videos(
        self, video_id: str, playlist: bool = True
    ) -> List[Dict[str, Any]]:
        """
        |coro|

        Returns the videos data including title, duration, stream urls.

        :param bool playlist: Fetches playlists if True.
        :param str video_id: The video or playlist id.
        :return List[Dict[str, Any]]: The video data.
        """

        if not video_id:
            return []

        if len(video_id) == 11:  # Video
            queries = [
                {
                    "key": self.ACCESS_KEY,
                    "videoId": video_id,
                    "contentCheckOk": True,
                    "racyCheckOk": True,
                }
            ]

        else:  # Playlist
            queries = [
                {
                    "key": self.ACCESS_KEY,
                    "videoId": playlist_video_id,
                    "contentCheckOk": True,
                    "racyCheckOk": True,
                }
                for playlist_video_id in (
                    await self.get_playlist_information(video_id)
                )["songs"]
            ]

        queries = queries[:1] if not playlist else queries

        requests = await asyncio.gather(
            *[self.request(f"{self.BASE_URL}/player", query=query) for query in queries]
        )

        try:
            tracks = [await r.json() if r else {} for r in requests]
        except asyncio.exceptions.TimeoutError:
            tracks = []

        return tracks
