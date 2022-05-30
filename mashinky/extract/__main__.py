import logging

import structlog.stdlib

import mashinky.extract.config
import mashinky.extract.images
import mashinky.extract.models
import mashinky.paths
from mashinky.extract.reader import DirReader, ZipReader

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
        structlog.dev.ConsoleRenderer(sort_keys=False),
    ],
)

readers = [
    DirReader(mashinky.paths.game_data / "media"),
    ZipReader(mashinky.paths.game_data / "mods/elishka.zip"),
    ZipReader(mashinky.paths.game_data / "mods/finished_texts.zip"),
    ZipReader(mashinky.paths.game_data / "mods/philip.zip"),
    ZipReader(mashinky.paths.game_data / "mods/unique_vehicles.zip"),
    ZipReader(mashinky.paths.game_data / "mods/world_cities.zip"),
]

config_builder = mashinky.extract.config.ConfigBuilder(readers)
images_builder = mashinky.extract.images.ImagesBuilder(readers, mashinky.paths.static)
models_builder = mashinky.extract.models.ModelsBuilder()
models_creator = mashinky.extract.models.ModelsCreator()

config = config_builder.load_config().patch()
images = images_builder.extract_images(config)
models = models_builder.build(config, images)

models_creator.write(models, mashinky.paths.sqlalchemy_url)
