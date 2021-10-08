from disney_mm.settings import bot_settings
from mmpy_bot import Bot, Plugin, listen_to, Message, Settings
from datetime import date
import humanize
import requests


class DisneyBot(Bot):
    def __init__(self):
        plugin = DisneyPlugin()
        super(DisneyBot, self).__init__(settings=plugin.mm_settings, plugins=[plugin])


class TouringPlans(object):
    TOURING_PLANS = "https://touringplans.com"
    DINING = "/dining.json"
    MK = TOURING_PLANS + "/magic-kingdom"
    AK = TOURING_PLANS + "/animal-kingdom"
    HS = TOURING_PLANS + "/hollywood-studios"
    EPCOT = TOURING_PLANS + "/epcot"

    def _dining_request(self, location):
        return requests.get(location + self.DINING).json()

    def mk_dining(self):
        return self._dining_request(self.MK)

    def ak_dining(self):
        return self._dining_request(self.AK)

    def hs_dining(self):
        return self._dining_request(self.HS)

    def epcot_dining(self):
        return self._dining_request(self.EPCOT)


class DisneyPlugin(Plugin):
    def __init__(self):
        super(DisneyPlugin, self).__init__()
        self._settings = bot_settings()
        self._touring_plans = TouringPlans()

    @property
    def mm_settings(self) -> Settings:
        _config = self._settings
        return Settings(
            MATTERMOST_URL=_config.mm_host,
            MATTERMOST_PORT=_config.mm_port,
            BOT_TOKEN=_config.mm_bot_token,
            BOT_TEAM=_config.mm_bot_team,
            SSL_VERIFY=_config.ssl_verify
        )

    @listen_to("how long", needs_mention=True)
    async def how_long(self, message: Message):
        diff = self._settings.trip_start_date - date.today()
        human_diff = humanize.precisedelta(diff)
        self.driver.reply_to(message, f"{human_diff}")

    @listen_to("^(?:food|dining|restaurants) (?:in|at) (.*)", needs_mention=True)
    async def restaurant(self, message: Message, location: str):
        req, loc = None, location.lower()
        if "magic" in loc or "mk" in loc:
            req = self._touring_plans.mk_dining
        elif "epcot" in loc:
            req = self._touring_plans.epcot_dining
        elif "animal" in loc or "ak" in loc:
            req = self._touring_plans.ak_dining
        elif "holly" in loc or "hs" in loc:
            req = self._touring_plans.hs_dining

        if not req:
            self.driver.reply_to(message, f"I don't know this park '{location}'?")
        else:
            j = req()
            names = [spot['name'] for spot in j[0]]  # counter-service
            self.driver.reply_to(message, f"*Counter Service:* {', '.join(names)}")
            names = [spot['name'] for spot in j[1]]  # table-service
            self.driver.reply_to(message, f"*Table Service:* {', '.join(names)}")
