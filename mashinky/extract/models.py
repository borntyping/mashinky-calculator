import dataclasses
import json
import pathlib
import typing

import rich.status
import structlog

import mashinky.models
import mashinky.extract.config
import mashinky.extract.images
import mashinky.paths

import sqlalchemy.orm

logger = structlog.get_logger(logger_name=__name__)


@dataclasses.dataclass(frozen=True)
class Models:
    cargo_types: typing.Sequence[mashinky.models.CargoType]
    token_types: typing.Sequence[mashinky.models.TokenType]
    colors: typing.Sequence[mashinky.models.Color]

    engines: typing.Sequence[mashinky.models.WagonType]
    wagons: typing.Sequence[mashinky.models.WagonType]
    road_vehicles: typing.Sequence[mashinky.models.WagonType]


@dataclasses.dataclass(frozen=True)
class ModelsBuilder:
    def build(
        self,
        config: mashinky.extract.config.Config,
        images: mashinky.extract.images.Images,
    ):
        cargo_types = {
            id: mashinky.models.CargoType(
                id=id,
                icon=images.cargo_types_icons[id].as_posix(),
                name=config.text(attrs),
            )
            for id, attrs in config.cargo_types.items()
        }

        token_types = {
            id: mashinky.models.TokenType(
                id=id,
                icon=images.token_types_icons[id].as_posix(),
                name=config.text(attrs),
            )
            for id, attrs in config.token_types.items()
        }

        colors = {
            id: mashinky.models.Color(
                id=id,
                name=attrs["name"],
                red=int(attrs["red"]),
                green=int(attrs["green"]),
                blue=int(attrs["blue"]),
            )
            for id, attrs in config.colors.items()
        }

        engines = []
        wagons = []
        road_vehicles = []

        for id, attrs in config.wagon_types.items():
            vehicle_type = int(attrs["vehicle_type"])
            name = attrs["name"]
            icon = images.wagon_types_icons[attrs["id"]].as_posix()

            if vehicle_type == 0 and "cargo" not in attrs:
                engines.append(
                    mashinky.models.WagonType(
                        id=id,
                        name=name,
                        icon=icon,
                    )
                )
            elif vehicle_type == 0 and "cargo" in attrs:
                wagons.append(
                    mashinky.models.WagonType(
                        id=id,
                        name=name,
                        icon=icon,
                    )
                )
            elif vehicle_type == 1:
                road_vehicles.append(
                    mashinky.models.WagonType(
                        id=id,
                        name=name,
                        icon=icon,
                    )
                )

        return Models(
            cargo_types=list(cargo_types.values()),
            token_types=list(token_types.values()),
            colors=list(colors.values()),
            engines=engines,
            wagons=wagons,
            road_vehicles=road_vehicles,
        )

    def build_uniq_values_file(
        self, config: mashinky.extract.config.Config, directory: pathlib.Path
    ) -> None:
        path = directory / "unique.json"
        keys = {key for attrs in config.wagon_types.values() for key in attrs.keys()}
        uniq = {
            key: list(
                sorted(set(attrs[key] for attrs in config.wagon_types.values() if key in attrs))
            )
            for key in sorted(keys)
        }
        path.write_text(json.dumps(uniq, indent=2))


@dataclasses.dataclass(frozen=True)
class ModelsCreator:
    def write(self, models: Models, url: str):
        mashinky.paths.database.unlink(missing_ok=True)
        engine = sqlalchemy.create_engine(url, future=True)
        mashinky.models.Base.metadata.create_all(engine)

        with rich.status.Status("Writing database"):
            with sqlalchemy.orm.Session(engine) as session:
                session.add_all(models.cargo_types)
                session.add_all(models.token_types)
                session.add_all(models.colors)
                session.add_all(models.engines)
                session.add_all(models.wagons)
                session.add_all(models.road_vehicles)
                session.commit()

        logger.info(
            "Committed models",
            cargo_types=len(models.cargo_types),
            token_types=len(models.token_types),
            colors=len(models.colors),
            engines=len(models.engines),
            wagons=len(models.wagons),
            road_vehicles=len(models.road_vehicles),
        )
