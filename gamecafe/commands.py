from pathlib import Path
from uuid import uuid4

import click
import requests
from flask import Blueprint, current_app

from .board_game_geek import BoardGameGeek
from .models import Game, Publisher, db

commands = Blueprint("commands", __name__, cli_group=None)

root_image_path = Path(current_app.config.get("IMAGE_STORAGE_ROOT"))


@commands.cli.command("import-collection")
@click.argument("username")
def import_collection(username):
    print("Fetching collection")
    games = BoardGameGeek.get_collection(username)

    for game in games:
        print(f"Processing game: {game.name}")
        pubs = []

        if (db_game := Game.get_by_bgg_id(game.id)) is None:
            print("Fetching game image")
            image_path = game.save_image(root_image_path / uuid4().hex)

            db_game = Game(game.name, game.id, str(image_path))

            if game.comment:
                db_game.location = game.comment

            print("Populating publishers")
            for publisher in game.publishers:
                if (pub := Publisher.get_by_bgg_id(publisher.id)) is None:
                    pub = Publisher(publisher.name, publisher.id).save(commit=False)

                pubs.append(pub)

            db_game.publishers = pubs

            db_game.save()
