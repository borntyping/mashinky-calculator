import dataclasses
import pathlib
import typing

import mashinky.extract.config
import mashinky.extract.images
import mashinky.extract.models
import mashinky.extract.reader
import mashinky.paths


@dataclasses.dataclass()
class Factory:
    readers: typing.Sequence[mashinky.extract.reader.Reader]
    images_directory: pathlib.Path
    sqlalchemy_database_url: str

    def manufacture(self):
        config_factory = mashinky.extract.config.ConfigFactory(readers=self.readers)
        config = config_factory.load_patched_config()

        images = mashinky.extract.images.ImageFactory(
            readers=self.readers,
            directory=self.images_directory,
            tcoords=config.tcoords,
        )

        models_factory = mashinky.extract.models.ModelFactory(
            config=config,
            images=images,
            sqlalchemy_database_url=self.sqlalchemy_database_url,
        )

        models_factory.init()
        models_factory.build()
