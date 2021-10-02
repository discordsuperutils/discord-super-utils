from __future__ import annotations

from typing import Dict, List, Any


__slots__ = ("YoutubeAuthor", "YoutubePlaylist")


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
        return cls(
            dictionary["name"],
            dictionary["id"]
        )


class YoutubePlaylist:
    """
    Represents a YouTube playlist.
    """

    __slots__ = ("title", "author", "songs", "id")

    def __init__(self, title: str, author: YoutubeAuthor, songs: List[str], id_: str) -> None:
        self.title = title
        self.author = author
        self.songs = songs
        self.id = id_

    def __str__(self):
        return f"<{self.__class__.__name__} title={self.title}, author={self.author}>"

    def __repr__(self):
        return f"<{self.__class__.__name__} title={self.title}, author={self.author}>, total_songs={len(self.songs)}>"

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> YoutubePlaylist:
        return cls(
            dictionary["title"],
            YoutubeAuthor.from_dict(dictionary["channel"]),
            dictionary["songs"],
            dictionary["playlistId"],
        )
