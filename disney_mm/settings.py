import argparse
from pathlib import Path
from datetime import date
from configparser import ConfigParser


def parseargs():
    parser = argparse.ArgumentParser("disney_mm")
    parser.add_argument("--mm_host")
    parser.add_argument("--mm_bot_token")
    parser.add_argument("--mm_bot_team")
    parser.add_argument("--mm_port", default="443")
    parser.add_argument("--mm_api_path", default="/api/v4")
    parser.add_argument("--ssl_verify", default=True)
    return parser.parse_args()


class Config:
    @classmethod
    def get(cls):
        config_file = Path("disney_mm.ini")
        if config_file.is_file():
            return cls(config_file)

        config_file = Path("/etc/disney_mm/disney_mm.ini")
        if config_file.is_file():
            return cls(config_file)

        return None

    def __init__(self, file_path):
        self._reader = ConfigParser()
        self._reader.read(file_path)

    @property
    def ssl_verify(self):
        return self._reader["DEFAULT"].get("ssl-verify") or True

    @property
    def mm_port(self):
        return self._reader["DEFAULT"].get("mm-port") or 443

    @property
    def mm_api_path(self):
        return self._reader["DEFAULT"].get("mm-api-path") or "/api/v4"

    @property
    def mm_host(self):
        return self._reader["DEFAULT"]["mm-host"]

    @property
    def mm_bot_token(self):
        return self._reader["DEFAULT"]["mm-bot-token"]

    @property
    def mm_bot_team(self):
        return self._reader["DEFAULT"]["mm-bot-team"]

    @property
    def trip_start_date(self):
        try:
            trip_date = self._reader["DISNEY"]["trip-start-date"]
        except KeyError:
            return None

        try:
            return date.fromisoformat(trip_date)
        except ValueError:
            return None

    @property
    def trip_end_date(self):
        try:
            trip_date = self._reader["DISNEY"]["trip-end-date"]
        except KeyError:
            return None

        try:
            return date.fromisoformat(trip_date)
        except ValueError:
            return None


def bot_settings():
    return Config.get() or parseargs()
