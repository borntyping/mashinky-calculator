from __future__ import annotations

import dataclasses
import functools
import json
import pathlib
import typing

import sqlalchemy.engine
import sqlalchemy.orm
import structlog

import mashinky.extract.config
import mashinky.extract.images
import mashinky.models.base
import mashinky.models.config
import mashinky.models.trains
import mashinky.paths

logger = structlog.get_logger(logger_name=__name__)

T = typing.TypeVar("T")


def optional(t: typing.Type, /, value: typing.Optional[str]) -> typing.Optional[int]:
    return t(value) if value is not None else None


def parse(method: typing.Callable[[typing.Any, str], T]) -> typing.Callable[[str], T]:
    @functools.wraps(method)
    def wrapper(self, value: str) -> T:
        try:
            return method(self, value)
        except Exception as exception:
            raise RuntimeError(f"Could not parse {value!r} using {method.__name__}") from exception

    return wrapper


@dataclasses.dataclass()
class ModelFactory:
    config: mashinky.extract.config.Config
    images: mashinky.extract.images.ImageFactory
    engine: sqlalchemy.engine.Engine

    def __init__(
        self,
        config: mashinky.extract.config.Config,
        images: mashinky.extract.images.ImageFactory,
        sqlalchemy_url: str,
    ) -> None:
        self.config = config
        self.images = images
        self.engine = sqlalchemy.create_engine(sqlalchemy_url, future=True)

    def init(self) -> None:
        logger.info("Creating database", url=self.engine.url)
        mashinky.paths.sqlalchemy_path.unlink(missing_ok=True)
        mashinky.models.base.Base.metadata.create_all(self.engine)

    def build(self):
        cargo_types = {k: self.build_cargo_type(v) for k, v in self.config.cargo_types.items()}
        token_types = {k: self.build_token_type(v) for k, v in self.config.token_types.items()}
        colors = {k: self.build_color(v) for k, v in self.config.colors.items()}
        wagon_types = {k: self.build_wagon_type(v) for k, v in self.config.wagon_types.items()}
        vehicles = {k: self.build_vehicle(v) for k, v in self.config.wagon_types.items()}

        logger.info("Writing models to database", url=self.engine.url)

        with sqlalchemy.orm.Session(self.engine) as session:
            session.add_all(cargo_types.values())
            session.add_all(token_types.values())
            session.add_all(colors.values())
            session.add_all(wagon_types.values())
            session.add_all(vehicles.values())
            session.commit()

        logger.info(
            "Wrote models to database",
            cargo_types=len(cargo_types),
            token_types=len(token_types),
            colors=len(colors),
            wagon_types=len(wagon_types),
            vehicles=len(vehicles),
        )

    def build_cargo_type(self, attrs: dict[str, str]) -> mashinky.models.config.CargoType:
        name = self.config.english.get(attrs.get("name"))
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=name,
            group="cargo_type",
        )
        return mashinky.models.config.CargoType(id=attrs["id"], icon=icon, name=name)

    def build_token_type(self, attrs: dict[str, str]) -> mashinky.models.config.TokenType:
        name = self.config.english.get(attrs.get("name"))
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=name,
            group="token_type",
        )
        return mashinky.models.config.TokenType(id=attrs["id"], icon=icon, name=name)

    def build_color(self, attrs: dict[str, str]) -> mashinky.models.config.Color:
        return mashinky.models.config.Color(
            id=attrs["id"],
            name=attrs["name"],
            red=int(attrs["red"]),
            green=int(attrs["green"]),
            blue=int(attrs["blue"]),
        )

    def build_wagon_type(self, attrs: dict[str, str]) -> mashinky.models.config.WagonType:
        logger.info("Building wagon type", id=attrs["id"], name=attrs["name"])
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=attrs["name"],
            group="wagon_type_icon",
        )
        icon_color = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon_color"],
            name=attrs["name"],
            group="wagon_type_icon_color",
        )
        return mashinky.models.config.WagonType(
            id=attrs["id"],
            name=attrs["name"],
            icon=icon,
            icon_color=icon_color,
            epoch=attrs["epoch"],
            level=attrs.get("level"),
            track=attrs["track"],
            weight_empty=attrs["weight_empty"],
            weight_full=attrs["weight_full"],
            length=attrs.get("length"),
            cost=attrs.get("cost"),
            sell=attrs.get("sell"),
            fuel_cost=attrs.get("fuel_cost"),
            power=attrs.get("power"),
            max_speed=attrs.get("max_speed"),
            max_speed_reverse=attrs.get("max_speed_reverse"),
            depo_upgrade=attrs.get("depo_upgrade"),
            cargo_id=attrs.get("cargo_id"),
            capacity=attrs.get("capacity"),
        )

    def build_vehicle(self, attrs: dict[str, str]) -> mashinky.models.trains.Vehicle:
        id = attrs["id"]
        name = attrs["name"]

        logger.info("Building vehicle", id=id, name=name)

        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=attrs["name"],
            group="wagon_type_icon",
        )
        icon_color = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon_color"],
            name=attrs["name"],
            group="wagon_type_icon_color",
        )
        epoch_min, epoch_max = self.parse_epoch(attrs["epoch"])
        track = int(attrs["track"])
        weight_empty = int(attrs["weight_empty"])
        weight_full = int(attrs["weight_full"])
        length = optional(float, attrs["length"])

        vehicle = mashinky.models.trains.Vehicle(
            id=id,
            name=name,
            icon=icon,
            icon_color=icon_color,
            epoch_min=epoch_min,
            epoch_max=epoch_max,
            track=track,
            weight_empty=weight_empty,
            weight_full=weight_full,
            length=length,
        )

        if attrs["vehicle_type"] == "0" and attrs.get("power"):
            return self.build_engine(vehicle, attrs)
        elif attrs["vehicle_type"] == "0":
            return self.build_wagon(vehicle, attrs)
        elif attrs["vehicle_type"] == "1":
            return self.build_road_vehicle(vehicle, attrs)
        raise ValueError(attrs["vehicle_type"])

    def build_engine(
        self,
        vehicle: mashinky.models.trains.Vehicle,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.Engine:
        return mashinky.models.trains.Engine(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch_min=vehicle.epoch_min,
            epoch_max=vehicle.epoch_max,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
        )

    def build_wagon(
        self,
        vehicle: mashinky.models.trains.Vehicle,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.Wagon:
        return mashinky.models.trains.Wagon(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch_min=vehicle.epoch_min,
            epoch_max=vehicle.epoch_max,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
        )

    def build_road_vehicle(
        self,
        vehicle: mashinky.models.trains.Vehicle,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.RoadVehicle:
        return mashinky.models.trains.RoadVehicle(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch_min=vehicle.epoch_min,
            epoch_max=vehicle.epoch_max,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
        )

    @parse
    def parse_epoch(self, value: str) -> typing.Tuple[int, int]:
        parts = value.split("-", 1)
        if len(parts) == 1:
            epoch = int(parts[0])
            return epoch, epoch
        elif len(parts) == 2:
            epoch_min, epoch_max = parts
            return int(epoch_min), int(epoch_max)
        raise NotImplementedError

    @parse
    def parse_track(self, value: str) -> int:
        track = int(value)
        assert track in (0, 2)
        return track
