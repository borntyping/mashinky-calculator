import logging
import pathlib

import mashinky.extract.reader
import mashinky.extract.config
import mashinky.extract.models
import mashinky.extract.images


game_path = pathlib.Path("/home/sam/Development/scratch/Mashinky")

readers = [
    mashinky.extract.reader.DirReader(game_path / "media"),
    mashinky.extract.reader.ZipReader(game_path / "mods/finished_texts.zip"),
    mashinky.extract.reader.ZipReader(game_path / "mods/unique_vehicles.zip"),
]

config_builder = mashinky.extract.config.ConfigBuilder(readers)
images_builder = mashinky.extract.images.ImagesBuilder(readers, pathlib.Path("assets"))
models_builder = mashinky.extract.models.ModelsBuilder()

config = config_builder.load_config().patch()
images = images_builder.extract_images(config)
models = models_builder.build(config, images)
