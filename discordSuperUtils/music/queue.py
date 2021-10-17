from __future__ import annotations

from typing import List, TYPE_CHECKING, Union, Any

from .enums import Loops

if TYPE_CHECKING:
    from ..youtube import YoutubeClient
    import discord
    from .player import Player


__all__ = ("QueueManager",)


class QueueManager:
    """
    Represents a queue manager that manages a queue.
    """

    __slots__ = (
        "queue",
        "volume",
        "pos",
        "loop",
        "autoplay",
        "shuffle",
        "vote_skips",
        "played_history",
        "queue_loop_start",
        "original_queue",
    )

    def __init__(self, volume: float, queue: List[Player]):
        self.pos = -1
        self.queue = queue
        self.volume = volume
        self.autoplay = False
        self.shuffle = False
        self.queue_loop_start = 0
        self.loop = Loops.NO_LOOP
        self.vote_skips = []
        self.played_history: List[Player] = []
        self.original_queue: List[Player] = []

    async def get_next_player(self, youtube: YoutubeClient) -> Player:
        """
        |coro|

        Returns the next player that should be played from the queue.

        :param YoutubeClient youtube: The youtube client.
        :return: The player.
        :rtype: Player
        """

        if self.loop != Loops.LOOP:
            self.pos += 1

        if self.loop == Loops.LOOP:
            player = self.now_playing

        elif self.loop == Loops.QUEUE_LOOP:
            if self.is_finished():
                self.pos = self.queue_loop_start

            player = self.queue[self.pos]

        else:
            if not self.queue and self.autoplay:
                last_video_id = self.played_history[-1].data["videoDetails"]["videoId"]
                player = (await Player.get_similar_videos(last_video_id, youtube))[0]

            else:
                player = self.queue[self.pos]

        return player

    def is_finished(self) -> bool:
        """
        Returns a boolean representing if the queue is finished.

        :return: A boolean representing if the queue is finished.
        :rtype: bool
        """

        return self.pos >= len(self.queue)

    @property
    def player_queue(self) -> List[Player]:
        """
        Returns the player queue.

        :return: The list of players
        :rtype: List[Player]
        """

        return self.queue[self.pos + 1 :]

    @property
    def now_playing(self) -> Player:
        """
        Returns the currently playing song.

        :return: The currently playing song.
        :rtype: Player
        """

        return self.queue[self.pos]

    @property
    def history(self) -> List[Player]:
        """
        Returns the player history.

        :return: The history.
        :rtype: List[Player]
        """

        return self.queue[: self.pos]

    def add(self, player: Player) -> None:
        """
        Adds a player to the queue.

        :param player: The player to add.
        :type player: Player
        :return: None
        :rtype: None
        """

        self.queue.append(player)

    def clear(self) -> None:
        """
        Clears the queue.

        :return: None
        :rtype: None
        """

        self.queue = self.queue[: self.pos + 1]

    def remove(self, index: int) -> Union[Player, Any]:
        """
        Removes and element from the queue at the specified index, and returns the element's value.

        :param index: The index.
        :type index: int
        :return: The element's value
        :rtype: Union[Player, Any]
        """

        return self.queue.pop(index)

    def remove_member(self, member: discord.Member) -> List[Player]:
        """
        Removes the member from the queue.

        :param discord.Member member: The member to remove from the queue.
        :return: The players removed.
        :rtype: None
        """

        removed_players = []
        for player in self.player_queue:
            if player.requester == member:
                removed_players.append(player)
                self.queue.remove(player)

        return removed_players

    def cleanup(self):
        """
        Clears the queue.

        :return: None
        :rtype: None
        """

        self.clear()
        self.history.clear()
        del self.played_history
        del self.queue
