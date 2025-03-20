from datetime import datetime
from pathlib import Path
from uuid import uuid4

import click
from flask import Blueprint, current_app

from .board_game_geek import BoardGameGeek
from .models import Game, Publisher, Tag, db

commands = Blueprint("commands", __name__, cli_group=None)

root_image_path = Path(current_app.config.get("IMAGE_STORAGE_ROOT"))


def get_publishers(bgg_publishers: list[BoardGameGeek.Publisher]) -> list[Publisher]:
    pubs = []
    for bgg_publisher in bgg_publishers:
        if (publisher := Publisher.get_by_bgg_id(bgg_publisher.id)) is None:
            publisher = Publisher(bgg_publisher.id, bgg_publisher.name).save(commit=False)

        pubs.append(publisher)

    return pubs


TAG_TYPE_MAP = {"boardgamecategory": Tag.Type.CATEGORY, "boardgamemechanic": Tag.Type.MECHANIC}


def get_tags(bgg_tags: list[BoardGameGeek.Tag]) -> list[Tag]:
    tags = []
    for bgg_tag in bgg_tags:
        if (tag := Tag.get_by_bgg_id(bgg_tag.id)) is None:
            tag_type = TAG_TYPE_MAP[bgg_tag.type]

            tag = Tag(bgg_tag.id, bgg_tag.name, tag_type).save(commit=False)

        tags.append(tag)

    return tags


@commands.cli.command("import-collection")
@click.argument("username")
def import_collection(username):
    print("Fetching collection")
    games = BoardGameGeek.get_collection(username)

    for bgg_game in games:
        print(f"Processing game: {game.name}")

        if (game := Game.get_by_bgg_id(game.id)) is None:
            image_path = game.save_image(root_image_path / uuid4().hex)
            image_path = str(image_path) if image_path else None

            game = Game(game.id, game.name, image_path)

            if bgg_game.comment:
                game.location = game.comment

        game.publishers = get_publishers(game.publishers)
        game.tags = get_tags(game.tags)

        game.save()


@commands.cli.command("update-games")
@click.argument("before_date")
def update_games(before_date: str):
    dt = datetime.strptime(before_date, r"%Y-%m-%d").date()

    stmt = Game.select().where(Game.last_updated <= dt)

    games = db.session.scalars(stmt).all()

    for game in games:
        bgg_game = BoardGameGeek.get_game(game.bgg_id)

        if bgg_game.image_url is not None and game.image_path is None:
            image_path = str(bgg_game.save_image(root_image_path / uuid4().hex))
            game.image_path = image_path

        game.publishers = get_publishers(bgg_game.publishers)
        game.tags = get_tags(bgg_game.tags)

        game.last_updated = datetime.now()

        game.save()

    db.session.commit()
