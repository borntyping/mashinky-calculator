import dataclasses
import pathlib
import typing

import structlog
import sqlalchemy
import sqlalchemy.engine

import mashinky.extract.config
import mashinky.extract.images
import mashinky.extract.models
import mashinky.extract.reader
import mashinky.models
import mashinky.paths

logger = structlog.get_logger(logger_name=__name__)


@dataclasses.dataclass()
class Factory:
    readers: typing.Sequence[mashinky.extract.reader.Reader]
    images_directory: pathlib.Path
    sqlalchemy_database_path: pathlib.Path
    sqlalchemy_database_url: str

    def engine(self) -> sqlalchemy.engine.Engine:
        engine = sqlalchemy.create_engine(self.sqlalchemy_database_url, future=True)
        self.sqlalchemy_database_path.unlink(missing_ok=True)
        logger.info("Creating database", url=engine.url)
        mashinky.models.Base.metadata.create_all(engine)
        return engine

    def manufacture(self):
        engine = self.engine()

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
            engine=engine,
        )

        models_factory.build()
