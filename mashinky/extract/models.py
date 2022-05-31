from __future__ import annotations

import dataclasses
import functools
import re
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


@dataclasses.dataclass()
class ModelFactory:
    config: mashinky.extract.config.Config
    images: mashinky.extract.images.ImageFactory
    engine: sqlalchemy.engine.Engine

    def __init__(
        self,
        config: mashinky.extract.config.Config,
        images: mashinky.extract.images.ImageFactory,
        sqlalchemy_database_url: str,
    ) -> None:
        self.config = config
        self.images = images
        self.engine = sqlalchemy.create_engine(sqlalchemy_database_url, future=True)

    def init(self) -> None:
        logger.info("Creating database", url=self.engine.url)
        mashinky.paths.sqlalchemy_path.unlink(missing_ok=True)
        mashinky.models.base.Base.metadata.create_all(self.engine)

    def build(self):
        cargo_types = {k: self.build_cargo_type(v) for k, v in self.config.cargo_types.items()}
        token_types = {k: self.build_token_type(v) for k, v in self.config.token_types.items()}
        wagon_types = {k: self.build_wagon_type(v) for k, v in self.config.wagon_types.items()}
        colors = {k: self.build_color(v) for k, v in self.config.colors.items()}

        logger.info("Writing models to database", url=self.engine.url)

        with sqlalchemy.orm.Session(self.engine) as session:
            session.add_all(cargo_types.values())
            session.add_all(token_types.values())
            session.add_all(wagon_types.values())
            session.add_all(colors.values())
            session.commit()

        logger.info(
            "Wrote models to database",
            cargo_types=len(cargo_types),
            token_types=len(token_types),
            colors=len(colors),
            wagon_types=len(wagon_types),
        )

    def build_cargo_type(self, attrs: dict[str, str]) -> mashinky.models.config.CargoType:
        name = self.config.english.get(attrs.get("name"))
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=name or attrs["id"],
            group="cargo_type",
        )
        return mashinky.models.config.CargoType(id=attrs["id"], icon=icon, name=name)

    def build_token_type(self, attrs: dict[str, str]) -> mashinky.models.config.TokenType:
        name = self.config.english.get(attrs["name"])
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

    def build_wagon_type(
        self,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.WagonType:
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
        epoch, epoch_end = parse_epoch(attrs["epoch"])
        track = int(attrs["track"])
        weight_empty = int(attrs["weight_empty"])
        weight_full = int(attrs["weight_full"])
        length = optional(float, attrs["length"])

        cost = parse_payments(attrs.get("cost"), mashinky.models.trains.Cost)
        sell = parse_payments(attrs.get("sell"), mashinky.models.trains.Sell)
        fuel = parse_payments(attrs.get("fuel"), mashinky.models.trains.Fuel)

        vehicle = mashinky.models.trains.WagonType(
            id=id,
            name=name,
            icon=icon,
            icon_color=icon_color,
            epoch=epoch,
            epoch_end=epoch_end,
            track=track,
            weight_empty=weight_empty,
            weight_full=weight_full,
            length=length,
            cost=cost,
            sell=sell,
            fuel=fuel,
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
        vehicle: mashinky.models.trains.WagonType,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.Engine:
        return mashinky.models.trains.Engine(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch=vehicle.epoch,
            epoch_end=vehicle.epoch_end,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
            power=int(attrs["power"]),
            max_speed=int(attrs["max_speed"]),
            max_speed_reverse=optional(int, attrs.get("max_speed_reverse")),
        )

    def build_wagon(
        self,
        vehicle: mashinky.models.trains.WagonType,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.Wagon:
        return mashinky.models.trains.Wagon(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch=vehicle.epoch,
            epoch_end=vehicle.epoch_end,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
            cargo_id=attrs["cargo"],
            capacity=int(attrs["capacity"]),
        )

    def build_road_vehicle(
        self,
        vehicle: mashinky.models.trains.WagonType,
        attrs: dict[str, str],
    ) -> mashinky.models.trains.RoadVehicle:
        return mashinky.models.trains.RoadVehicle(
            id=vehicle.id,
            name=vehicle.name,
            icon=vehicle.icon,
            icon_color=vehicle.icon_color,
            epoch=vehicle.epoch,
            epoch_end=vehicle.epoch_end,
            track=vehicle.track,
            weight_empty=vehicle.weight_empty,
            weight_full=vehicle.weight_full,
            length=vehicle.length,
            cargo_id=attrs["cargo"],
            capacity=int(attrs["capacity"]),
        )


def parse(method: typing.Callable[[str], T]) -> typing.Callable[[str], T]:
    @functools.wraps(method)
    def wrapper(value: str) -> T:
        try:
            return method(value)
        except Exception as exception:
            raise RuntimeError(f"Could not parse {value!r} using {method.__name__}") from exception

    return wrapper


@parse
def parse_epoch(
    value: str,
) -> typing.Tuple[mashinky.models.trains.Epoch, mashinky.models.trains.Epoch]:
    if value == "0":
        return None, None

    parts = value.split("-", 1)
    if len(parts) == 1:
        (start,) = (end,) = parts
    elif len(parts) == 2:
        (start, end) = parts
    else:
        raise NotImplementedError

    if start == "0":
        logger.warning("starts at 0", value=value)

    return mashinky.models.trains.Epoch(int(start)), mashinky.models.trains.Epoch(int(end))


@parse
def parse_track(value: str) -> mashinky.models.trains.Track:
    return mashinky.models.trains.Track(int(value))


def parse_payments(
    value: typing.Optional[str],
    model: typing.Type,
) -> typing.Sequence[mashinky.models.trains.Cost]:
    if value is None:
        return []

    if matches := re.findall(r"(?P<amount>-?\d+)(?:\[(?P<token_type>\w+)])?", value):
        return [
            model(
                amount=int(amount),
                token_type_id=token_type or "F0000000",
            )
            for amount, token_type in matches
        ]

    raise ValueError(f"Could not parse {value} as payments")
