from __future__ import annotations

from typing import Dict, List, Any, TYPE_CHECKING, Union, Optional
from .enums import PlaylistType

if TYPE_CHECKING:
    import discord
    from .music import MusicManager

__slots__ = ("SpotifyTrack", "YoutubeAuthor", "Playlist", "UserPlaylist")


class SpotifyTrack:
    """
    Represents a spotify track.
    """

    __slots__ = ("name", "authors")

    def __init__(self, name: str, authors: List[str]) -> None:
        self.name = name
        self.authors = authors

    def __str__(self):
        return f"{self.name} by {self.authors[0]}"

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, authors={self.authors}>"

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> SpotifyTrack:
        """
        Creates a Spotify track from the dictionary.

        :param Dict[str, Any] dictionary: The dictionary.
        :return: The spotify track.
        :rtype: SpotifyTrack
        """

        return cls(
            dictionary["track"]["name"],
            [artist["name"] for artist in dictionary["track"]["artists"]],
        )


class YoutubeAuthor:
    """
    Represents a YouTube author / channel.
    """

    def __init__(self, name: str, id_: str) -> None:
        self.id = id_
        self.name = name

    def __str__(self):
        return f"<{self.__class__.__name__} name={self.name}>"

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, id={self.id}>"

    @classmethod
    def from_dict(cls, dictionary: Dict[str, str]) -> YoutubeAuthor:
        """
        Creates a YouTube author from the dictionary.

        :param Dict[str, str] dictionary: The dictionary.
        :return: The YouTube author.
        :rtype: YoutubeAuthor
        """

        return cls(dictionary["name"], dictionary["id"])


class Playlist:
    """
    Represents a playlist.
    Supports Spotify and YouTube.
    """

    __slots__ = ("title", "author", "songs", "url", "type")

    def __init__(
        self,
        title: str,
        author: Optional[YoutubeAuthor],
        songs: List[Union[str, SpotifyTrack]],
        url: str,
        type_: PlaylistType,
    ) -> None:
        self.title = title
        self.author = author
        self.songs = songs
        self.url = url
        self.type = type_

    def __str__(self):
        return f"<{self.__class__.__name__} title={self.title}, author={self.author}>"

    def __repr__(self):
        return f"<{self.__class__.__name__} title={self.title}, author={self.author}>, total_songs={len(self.songs)}>"

    @classmethod
    def from_youtube_dict(cls, dictionary: Dict[str, Any]) -> Playlist:
        """
        Creates a playlist object from the YouTube dictionary

        :param Dict[str, Any] dictionary: The YouTube dictionary.
        :return: The playlist.
        :rtype: Playlist
        """

        return cls(
            dictionary["title"],
            YoutubeAuthor.from_dict(dictionary["channel"]),
            dictionary["songs"],
            f"https://www.youtube.com/watch?v={dictionary['songs'][0]}&list={dictionary['playlistId']}",
            PlaylistType.YOUTUBE,
        )

    @classmethod
    def from_spotify_dict(cls, dictionary: Dict[str, Any]) -> Playlist:
        """
        Creates a playlist object from the Spotify dictionary

        :param Dict[str, Any] dictionary: The spotify dictionary.
        :return: The playlist.
        :rtype: Playlist
        """

        return cls(
            dictionary["name"],
            None,
            [SpotifyTrack.from_dict(track) for track in dictionary["tracks"]],
            dictionary["url"],
            PlaylistType.SPOTIFY,
        )


class UserPlaylist:
    """
    Represents a playlist stored in the database.
    """

    __slots__ = ("owner", "id", "playlist", "music_manager", "table")

    def __init__(
        self,
        music_manager: MusicManager,
        owner: discord.User,
        id_: str,
        playlist: Playlist,
    ) -> None:
        self.owner = owner
        self.id = id_
        self.playlist = playlist
        self.music_manager = music_manager
        self.table = music_manager.tables["playlists"]

    async def delete(self) -> None:
        """
        |coro|

        Deletes the playlist from the database.

        :return: None
        :rtype: None
        """

        await self.music_manager.database.delete(
            self.table, {"user": self.owner.id, "id": self.id}
        )

    def __str__(self):
        return f"<{self.__class__.__name__} owner={self.owner}>"

    def __repr__(self):
        return f"<{self.__class__.__name__} owner={self.owner}, id={self.id}, playlist={self.playlist}>"
