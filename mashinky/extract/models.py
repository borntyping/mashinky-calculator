import dataclasses
import decimal
import json
import pathlib
import typing

import rich.status
import sqlalchemy.orm
import structlog

import mashinky.extract.config
import mashinky.extract.images
import mashinky.models
import mashinky.paths

logger = structlog.get_logger(logger_name=__name__)


def get_float(attrs: dict[str, str], key: str) -> typing.Optional[float]:
    if value := attrs.get(key):
        return float(value)
    return None


def get_int(attrs: dict[str, str], key: str) -> typing.Optional[int]:
    if value := attrs.get(key):
        return int(value)
    return None


@dataclasses.dataclass(frozen=True)
class Models:
    config_cargo_types: typing.Sequence[mashinky.models.CargoType]
    config_token_types: typing.Sequence[mashinky.models.TokenType]
    config_colors: typing.Sequence[mashinky.models.Color]
    config_wagon_types: typing.Sequence[mashinky.models.WagonType]

    app_engines: typing.Sequence[mashinky.models.WagonType]
    app_wagons: typing.Sequence[mashinky.models.WagonType]
    app_road_vehicles: typing.Sequence[mashinky.models.WagonType]


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

        wagon_types = []
        engines = []
        wagons = []
        road_vehicles = []

        # TODO: load coloured icons
        for id, attrs in config.wagon_types.items():
            log = logger.bind(id=id, name=attrs["name"])
            log.info("Parsing wagon type")

            vehicle_type = int(attrs["vehicle_type"])
            icon = images.wagon_types_icons[attrs["id"]].as_posix()

            wagon_types.append(
                mashinky.models.WagonType(
                    id=id,
                    name=attrs["name"],
                    icon=icon,
                    epoch=attrs["epoch"],
                    track=int(attrs["track"]),
                    cost=attrs.get("cost"),
                    sell=attrs.get("sell"),
                    weight_empty=int(attrs["weight_empty"]),
                    weight_full=int(attrs["weight_full"]),
                    length=get_float(attrs, "length"),
                    fuel_cost=attrs.get("fuel_cost"),
                    power=get_int(attrs, "power"),
                    max_speed=get_int(attrs, "max_speed"),
                    max_speed_reverse=get_int(attrs, "max_speed_reverse"),
                    depo_upgrade=attrs.get("depo_upgrade"),
                    cargo_id=attrs.get("cargo_id"),
                    capacity=get_int(attrs, "capacity"),
                )
            )

            if vehicle_type == 0 and "cargo" not in attrs:
                ...
                # engines.append(
                #     mashinky.models.WagonType(
                #         id=id,
                #         name=name,
                #         icon=icon,
                #     )
                # )
            elif vehicle_type == 0 and "cargo" in attrs:
                ...
                # wagons.append(
                #     mashinky.models.WagonType(
                #         id=id,
                #         name=name,
                #         icon=icon,
                #     )
                # )
            elif vehicle_type == 1:
                ...
                # road_vehicles.append(
                #     mashinky.models.WagonType(
                #         id=id,
                #         name=name,
                #         icon=icon,
                #     )
                # )

        return Models(
            config_cargo_types=list(cargo_types.values()),
            config_token_types=list(token_types.values()),
            config_colors=list(colors.values()),
            config_wagon_types=wagon_types,
            app_engines=engines,
            app_wagons=wagons,
            app_road_vehicles=road_vehicles,
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
                session.add_all(models.config_cargo_types)
                session.add_all(models.config_token_types)
                session.add_all(models.config_colors)
                session.add_all(models.config_wagon_types)
                session.add_all(models.app_engines)
                session.add_all(models.app_wagons)
                session.add_all(models.app_road_vehicles)
                session.commit()

        logger.info(
            "Committed models",
            cargo_types=len(models.config_cargo_types),
            token_types=len(models.config_token_types),
            colors=len(models.config_colors),
            wagon_types=len(models.config_wagon_types),
            engines=len(models.app_engines),
            wagons=len(models.app_wagons),
            road_vehicles=len(models.app_road_vehicles),
        )
