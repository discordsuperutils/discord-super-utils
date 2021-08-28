from spotipy import SpotifyClientCredentials
import spotipy
import asyncio

FIELD = "items.track.name,items.track.artists(name),total"


class Spotify:
    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id,
                                                                        client_secret=client_secret))
        self.loop = asyncio.get_event_loop()

    @staticmethod
    def get_type(url):
        url = url.replace("https://open.spotify.com/", "")
        return url.split("/")[-2]

    @staticmethod
    def make_title(song):
        artists = " ".join([artist['name'] for artist in song.get('artists')])
        return f"{song['name']} by {artists}"

    async def fetch_playlist_data(self, url, offset):
        return await self.loop.run_in_executor(None, lambda: self.sp.playlist_items(playlist_id=url,
                                                                                    fields=FIELD,
                                                                                    offset=offset))

    async def fetch_full_playlist(self, url):
        initial_request = await self.fetch_playlist_data(url, 0)
        total_tracks = initial_request.get('total')

        requests = list(
            await asyncio.gather(*(self.fetch_playlist_data(url, offset) for offset in range(100, total_tracks, 100)))
        )
        requests.insert(0, initial_request)
        result_tracks = []

        for request in requests:
            result_tracks += request.get('items')

        return result_tracks

    async def get_songs(self, url):
        playlist_type = self.get_type(url)
        songs = []

        if playlist_type == "playlist":
            return [self.make_title(song['track']) for song in await self.fetch_full_playlist(url)]

        if playlist_type == "track":
            songs = [await self.loop.run_in_executor(None, lambda: self.sp.track(track_id=url))]

        if playlist_type == "album":
            album = await self.loop.run_in_executor(None, lambda: self.sp.album_tracks(album_id=url, limit=50))
            songs = album.get("items")

        return [self.make_title(song) for song in songs]
