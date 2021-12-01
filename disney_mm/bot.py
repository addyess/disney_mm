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

    def dining_request(self, location):
        return requests.get(location + self.DINING).json()

    def all_dining(self):
        all_req = map(self.dining_request, (self.MK, self.AK, self.HS, self.EPCOT))
        counter, table = [], []
        for counter_resp, table_resp in all_req:
            counter += counter_resp
            table += table_resp
        return [counter, table]

    def find_dining(self, location):
        attributes = ['name']
        loc = location.lower()
        def match(dine): return any(loc in dine[attr].lower() for attr in attributes)
        return (list(filter(match, dining)) for dining in self.all_dining())


class DisneyPlugin(Plugin):
    def __init__(self):
        super(DisneyPlugin, self).__init__()
        self._settings = bot_settings()
        self._tp = TouringPlans()

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

    @listen_to("[Hh]ow long( until .*){0,1}", needs_mention=True)
    async def how_long(self, message: Message, until: str):
        if not until or until.endswith(" until we arrive"):
            diff = self._settings.trip_start_date - date.today()
            human_diff = humanize.precisedelta(diff)
            self.driver.reply_to(message, f"{human_diff}")
        else:
            self.driver.reply_to(message, "I don't know, ask @mama")

    @listen_to("^(?:[Ff]ood|[Dd]ining|[Rr]estaurants) (?:in|at) (.*)", needs_mention=True)
    async def restaurant(self, message: Message, location: str):
        resp, loc = None, location.lower()
        if "magic" in loc or "mk" in loc:
            resp = self._tp.dining_request(self._tp.MK)
        elif "epcot" in loc:
            resp = self._tp.dining_request(self._tp.EPCOT)
        elif "animal" in loc or "ak" in loc:
            resp = self._tp.dining_request(self._tp.AK)
        elif "holly" in loc or "hs" in loc:
            resp = self._tp.dining_request(self._tp.HS)

        if not resp:
            self.driver.reply_to(message, f"I don't know this location '{location}'?")
        else:
            names = [spot['name'] for spot in resp[0]]  # counter-service
            if names:
                self.driver.reply_to(message, f"*Counter Service:* {', '.join(names)}")
            names = [spot['name'] for spot in resp[1]]  # table-service
            if names:
                self.driver.reply_to(message, f"*Table Service:* {', '.join(names)}")

    @listen_to("^(?:[Mm]enu) (?:in|at) (.*)", needs_mention=True)
    async def menu(self, message: Message, location: str):
        resp = self._tp.find_dining(location)
        provided = 0
        for dining_type in resp:
            for rest in dining_type:
                provided += 1
                self.driver.reply_to(
                    message,
                    f"{rest['name']} -- ({rest['category_code']})\n"
                    f"Selection: {rest['selection']}\n"
                    f"Menus:\n"
                    f"   [adult breakfast]({rest['adult_breakfast_menu_url']})\n"
                    f"   [adult lunch]({rest['adult_lunch_menu_url']})\n"
                    f"   [adult dinner]({rest['adult_dinner_menu_url']})\n"
                    f"   [child breakfast]({rest['child_breakfast_menu_url']})\n"
                    f"   [child lunch]({rest['child_lunch_menu_url']})\n"
                    f"   [child dinner]({rest['child_dinner_menu_url']})\n"
                    f"   [disney link]({rest['operator_url']})"
                )
        if not provided:
            self.driver.reply_to(message, f"I couldn't match this location '{location}'?")
