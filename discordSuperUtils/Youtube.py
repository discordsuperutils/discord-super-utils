from typing import (
    Dict,
    Any
)
from urllib import parse

import aiohttp


class YoutubeClient:
    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session or aiohttp.ClientSession()

    async def get_video(self, video_id: str) -> Dict[str, Any]:
        """
        |coro|

        Returns the video data including title, duration, stream urls.

        :param str video_id: The video id.
        :return Dict[str, Any]: The video data.
        """

        payload = b"{'context': {'client': {'clientName': 'ANDROID','clientVersion': '16.20'}}}"

        query = {
            # Not an actual access key, just a key youtube uses in it's requests.
            'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
            'videoId': video_id,
            'contentCheckOk': True,
            'racyCheckOk': True
        }

        headers = {
            'Content-Type': 'application/json',
            "User-Agent": "Mozilla/5.0",
            "accept-language": "en-US,en"
        }

        r = await self.session.post(f'https://www.youtube.com/youtubei/v1/player?{parse.urlencode(query)}',
                                    data=payload,
                                    headers=headers)
        return await r.json()
