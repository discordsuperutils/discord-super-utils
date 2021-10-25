from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, TYPE_CHECKING, Union, Optional
from .enums import PlaylistType

if TYPE_CHECKING:
    import discord
    from .music import MusicManager

__slots__ = ("SpotifyTrack", "YoutubeAuthor", "Playlist", "UserPlaylist")


@dataclass
class SpotifyTrack:
    """
    Represents a spotify track.
    """

    name: str
    authors: List[str]

    def __str__(self):
        return f"{self.name} by {self.authors[0]}"

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


@dataclass
class YoutubeAuthor:
    """
    Represents a YouTube author / channel.
    """

    name: str
    id: str

    @classmethod
    def from_dict(cls, dictionary: Dict[str, str]) -> YoutubeAuthor:
        """
        Creates a YouTube author from the dictionary.

        :param Dict[str, str] dictionary: The dictionary.
        :return: The YouTube author.
        :rtype: YoutubeAuthor
        """

        return cls(dictionary["name"], dictionary["id"])


@dataclass
class Playlist:
    """
    Represents a playlist.
    Supports Spotify and YouTube.
    """

    title: str
    author: Optional[YoutubeAuthor]
    songs: List[Union[str, SpotifyTrack]]
    url: str
    type: PlaylistType

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


@dataclass
class UserPlaylist:
    """
    Represents a playlist stored in the database.
    """

    music_manager: MusicManager
    owner: discord.User
    id: str
    playlist: Playlist

    async def delete(self) -> None:
        """
        |coro|

        Deletes the playlist from the database.

        :return: None
        :rtype: None
        """

        await self.music_manager.database.delete(
            self.music_manager.tables["playlists"],
            {"user": self.owner.id, "id": self.id},
        )
