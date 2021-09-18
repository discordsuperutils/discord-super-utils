import asyncio

import youtube_dl as youtube_dl

import discordSuperUtils
from tester import Tester


async def start_testing():
    """
    Tested with a youtube playlist containing 100 songs.

    RESULTS
    --------
        Our youtube client: ~5628.8ms
        youtube_dl: ~89500ms

    Conclusion
    ----------
        Our youtube client is ~15x faster than youtube_dl and is optimised for discord.py youtube fetching.
        youtube_dl is not async, which makes it slow and not optimal for our use case.
    """

    tester = Tester()
    tester.add_test(fetch_youtube_client, "orJSJGHjBLI")
    tester.add_test(fetch_ytdl, "orJSJGHjBLI")
    await tester.run()


async def fetch_youtube_client():
    youtube_client = discordSuperUtils.YoutubeClient()

    r = await youtube_client.get_videos("PLcirGkCPmbmFeQ1sm4wFciF03D_EroIfr")

    await youtube_client.session.close()
    return r[0]["videoDetails"]["videoId"]


async def fetch_ytdl():
    ytdl = youtube_dl.YoutubeDL(
        {
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
    )

    return (
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: ytdl.extract_info(
                "PLcirGkCPmbmFeQ1sm4wFciF03D_EroIfr", download=False
            ),
        )
    )["entries"][0]["id"]


asyncio.run(start_testing())
