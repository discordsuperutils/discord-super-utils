from spotipy import SpotifyClientCredentials
import spotipy


class Spotify:
    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id,
                                                                        client_secret=client_secret))

    @staticmethod
    async def get_type(url):
        url = url.replace("https://open.spotify.com/", "")
        return url.split("/")[0]

    @staticmethod
    async def make_title(song):
        artists = " ".join([artist['name'] for artist in song.get('artists')])
        return f"{song['name']} by {artists}"

    async def get_songs(self, url):
        playlist_type = await self.get_type(url)

        if playlist_type == "playlist":
            playlist = self.sp.playlist_items(playlist_id=url, fields='items.track.name,items.track.artists(name)',
                                              offset=0)
            playlist = playlist.get('items')
            return [await self.make_title(song['track']) for song in playlist]

        elif playlist_type == "track":
            song = self.sp.track(track_id=url)
            return [await self.make_title(song)]

        elif playlist_type == "album":
            album = self.sp.album_tracks(album_id=url, limit=50)
            album = album.get("items")
            return [await self.make_title(song) for song in album]
