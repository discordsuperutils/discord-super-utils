from .antispam import SpamDetectionGenerator, SpamManager
from .ban import BanManager
from .base import CogManager, questionnaire
from .birthday import BirthdayManager
from .commandhinter import CommandHinter, CommandResponseGenerator
from .convertors import TimeConvertor
from .database import DatabaseManager, create_mysql
from .economy import EconomyManager, EconomyAccount
from .fivem import FiveMServer
from .imaging import ImageManager, Backgrounds
from .infractions import InfractionManager
from .invitetracker import InviteTracker
from .kick import KickManager
from .leveling import LevelingManager
from .messagefilter import MessageFilter, MessageResponseGenerator
from .modmail import ModMailManager
from .music import LavalinkMusicManager
from .music.exceptions import *
from .music.lavalink.lavalink import LavalinkMusicManager
from .music.music import *
from .music.player import Player
from .music.enums import *
from .music.lavalink.equalizer import Equalizer
from .music.queue import QueueManager
from .mute import MuteManager, AlreadyMuted
from .paginator import PageManager, generate_embeds, ButtonsPageManager
from .prefix import PrefixManager
from .punishments import Punishment
from .reactionroles import ReactionManager
from .spotify import SpotifyClient
from .template import TemplateManager
from .youtube import YoutubeClient

__title__ = "discordSuperUtils"
__version__ = "0.2.8"
__author__ = "Koyashie07 & Adam7100"
__license__ = "MIT"
