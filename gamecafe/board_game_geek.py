import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import requests
import requests_cache


class BoardGameGeek:
    BASE_URL = "https://boardgamegeek.com/xmlapi2"

    @dataclass
    class Publisher:
        id: int
        name: str

    @dataclass
    class Game:
        id: int
        name: str
        image_url: str | None
        publishers: list["BoardGameGeek.Publisher"]
        comment: str | None = None

        def save_image(self, image_path: Path):
            if self.image_url is None:
                return None

            resp = requests.get(self.image_url, stream=True)

            with image_path.open("wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)

            return image_path

    @classmethod
    def get_game(cls, game_id, rc: requests_cache.CachedSession = None):
        game_id = str(game_id)

        rc = rc or requests_cache.CachedSession(stale_if_error=True)

        while (resp := rc.get(f"{cls.BASE_URL}/thing", params={"id": game_id})).status_code != 200:
            time.sleep(5)

        root = ET.fromstring(resp.content)

        name = root.find('.//*name[@type="primary"]').attrib["value"]
        image_url_element = root.find(".//*image")
        image_url = image_url_element.text if image_url_element is not None else None
        publishers_elements = root.findall('.//*link[@type="boardgamepublisher"]')

        publishers = [
            cls.Publisher(int(pub.attrib["id"]), pub.attrib["value"]) for pub in publishers_elements
        ]

        return cls.Game(int(game_id), name, image_url, publishers)

    @classmethod
    def get_collection(cls, username: str, rc: requests_cache.CachedSession = None) -> list[Game]:
        resp = None

        rc = rc or requests_cache.CachedSession(stale_if_error=True)

        with rc.cache_disabled():
            while (
                resp := rc.get(
                    f"{cls.BASE_URL}/collection",
                    params={"username": username, "excludesubtype": "boardgameexpansion"},
                )
            ).status_code == 202:
                print(resp.text)
                time.sleep(5)

        if resp.status_code != 200:
            raise Exception(resp.text)

        root = ET.fromstring(resp.content)

        game_elements = root.findall("item")

        games = []

        for i, game_element in enumerate(game_elements):
            game_id = game_element.attrib["objectid"]

            print(f"Fetching game_id {game_id} - {i}/{len(game_elements)}")
            game = cls.get_game(game_id, rc=rc)

            if (comment_element := game_element.find("comment")) is not None:
                game.comment = comment_element.text

            games.append(game)

            time.sleep(0.2)

        return games
