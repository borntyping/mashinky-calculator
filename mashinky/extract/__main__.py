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

game_data = pathlib.Path(os.environ["MASHINKY_GAME_DATA"])
factory = mashinky.extract.factory.Factory(
    readers=[
        mashinky.extract.reader.DirReader(game_data / "media"),
        mashinky.extract.reader.ZipReader(game_data / "mods/elishka.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/finished_texts.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/philip.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/unique_vehicles.zip"),
        mashinky.extract.reader.ZipReader(game_data / "mods/world_cities.zip"),
    ],
    images_directory=mashinky.paths.static,
    sqlalchemy_url=mashinky.paths.sqlalchemy_url,
)
factory.manufacture()
