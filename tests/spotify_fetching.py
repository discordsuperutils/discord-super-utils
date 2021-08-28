from tester import Tester
import discordSuperUtils
import asyncio
from spotify_dl import spotify


client_id = ...
client_secret = ...
playlist_url = ...


async def start_testing():
    tester = Tester()
    tester.add_test(fetch_spotify_client, ...)
    tester.add_test(fetch_spotify_dl_client, ...)
    await tester.run()

    """
    Tested with a playlist containing 463 songs.
    
    RESULTS
    --------
        Our spotify client: ~1181ms
        spotify_dl: ~94000ms
    
    Conclusion
    ----------
        Our spotify client is ~80x faster than spotify_dl and is optimised for discord.py spotify fetching.
    """


async def fetch_spotify_client():
    # Our spotify client is optimized for large playlists.
    # spotify_dl is a great library, but is not meant to be used in an async program.
    return (await spotify_client.get_songs(playlist_url))[0]


async def fetch_spotify_dl_client():
    return (await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: spotify.fetch_tracks(spotify_client.sp, spotify.parse_spotify_url(playlist_url)[0], playlist_url)
    ))[0]['name']


loop = asyncio.get_event_loop()
spotify_client = discordSuperUtils.SpotifyClient(client_id, client_secret, asyncio.get_event_loop())
loop.run_until_complete(start_testing())