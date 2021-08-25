import aiohttp
import aiohttp.client_exceptions


class ServerNotFound(Exception):
    """Raises an error when a server is invalid or offline."""


class FiveMPlayer:
    def __init__(self, player_id, identifiers, name, ping):
        self.player_id = player_id
        self.identifiers = identifiers
        self.name = name
        self.ping = ping

    def __str__(self):
        return f"<FiveM Player {self.player_id=}>"

    def __repr__(self):
        return f"<FiveM Player {self.name=}, {self.player_id=}, {self.identifiers=}, {self.ping=}>"

    @classmethod
    def fetch(cls, player_dict):
        identifiers = dict([x.split(':') for x in player_dict['identifiers']])
        return cls(player_dict['id'], identifiers, player_dict['name'], player_dict['ping'])


class FiveMServer:
    def __init__(self, ip, resources, players, name, variables):
        self.ip = ip
        self.resources = resources
        self.players = players
        self.name = name
        self.variables = variables

    def __str__(self):
        return f"<FiveM Server {self.name=}>"

    def __repr__(self):
        return f"<FiveM Server {self.ip=}," \
               f" {self.name=}," \
               f" {self.players=}," \
               f" {self.resources=}," \
               f" {self.variables=}>"

    @classmethod
    async def fetch(cls, ip):
        base_address = "http://" + ip + "/"

        async with aiohttp.ClientSession() as session:
            try:
                await session.get(base_address)  # Server status check
            except (aiohttp.client_exceptions.ClientConnectorError, aiohttp.client_exceptions.InvalidURL):
                raise ServerNotFound(f"Server '{ip}' is invalid or offline.")

            players_request = await session.get(base_address + "players.json")
            info_request = await session.get(base_address + "info.json")
            dynamic_info_request = await session.get(base_address + "dynamic.json")

            info = await info_request.json(content_type=None)
            players = await players_request.json(content_type=None)
            dynamic = await dynamic_info_request.json(content_type=None)
            # This is still included in the session because parsing the json outside of it sometimes doesnt work
            # and block the program (?) :(

        return cls(ip,
                   info['resources'],
                   [FiveMPlayer.fetch(player) for player in players],
                   dynamic["hostname"],
                   info['vars'])