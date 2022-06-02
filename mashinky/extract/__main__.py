import dataclasses
import logging
import os
import pathlib

import structlog

import mashinky.extract.factory
import mashinky.extract.reader
import mashinky.paths

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.dev.ConsoleRenderer(sort_keys=False),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

default_game_data = pathlib.Path("C:/Program Files (x86)/Steam/steamapps/common/Mashinky")
game_data = pathlib.Path(os.environ.get("MASHINKY_GAME_DATA", default_game_data))
factory = mashinky.extract.factory.Factory(
    readers=[
        mashinky.extract.reader.DirReader(game_data / "media"),
        mashinky.extract.reader.ZipReader(game_data / "mods/elishka.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/finished_texts.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/philip.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/unique_vehicles.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/world_cities.zip"),
    ],
    images_directory=mashinky.paths.static_folder,
    sqlalchemy_database_path=mashinky.paths.sqlalchemy_database_path,
    sqlalchemy_database_url=mashinky.paths.sqlalchemy_database_url,
)
factory.manufacture()
