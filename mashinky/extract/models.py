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
import mashinky.models
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

    def build(self):
        cargo_types = {k: self.build_cargo_type(v) for k, v in self.config.cargo_types.items()}
        token_types = {k: self.build_token_type(v) for k, v in self.config.token_types.items()}
        wagon_types = {
            id: self.build_wagon_type(attrs, token_types)
            for id, attrs in self.config.wagon_types.items()
        }
        colors = {k: self.build_color(v) for k, v in self.config.colors.items()}

        logger.info("Writing models to database", url=self.engine.url)

        with sqlalchemy.orm.Session(self.engine) as session:
            session.add_all(list(cargo_types.values()))
            session.add_all(list(token_types.values()))
            session.add_all(list(wagon_types.values()))
            session.add_all(list(colors.values()))
            session.commit()

        logger.info(
            "Wrote models to database",
            cargo_types=session.query(mashinky.models.Cargo).count(),
            token_types=session.query(mashinky.models.TokenType).count(),
            wagon_types=session.query(mashinky.models.WagonType).count(),
            colors=session.query(mashinky.models.Color).count(),
            cost=session.query(mashinky.models.Cost).count(),
            sell=session.query(mashinky.models.Sell).count(),
            fuel=session.query(mashinky.models.Fuel).count(),
        )

    def build_cargo_type(self, attrs: dict[str, str]) -> mashinky.models.Cargo:
        name = self.config.english.get(attrs.get("name"))
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=attrs["id"],
            group="cargo_type",
        )
        if "icon_mini" in attrs:
            icon_mini = self.images.extract_icon(
                icon_texture=attrs["icon_texture"],
                icon=attrs["icon_mini"],
                name=attrs["id"],
                group="cargo_type_mini",
            )
        else:
            icon_mini = None
        return mashinky.models.Cargo(
            id=attrs["id"],
            name=name,
            color=attrs["color"],
            icon=icon,
            icon_mini=icon_mini,
            type=attrs.get("type"),
            load_speed=optional(int, attrs.get("load_speed")),
            sell_immediately=attrs.get("sell_immediately") == "1",
            affect_city_grow=optional(int, attrs.get("affect_city_grow")),
            train_stop_capacity=optional(int, attrs.get("train_stop_capacity")),
            road_stop_capacity=optional(int, attrs.get("road_stop_capacity")),
            stop_capacity=optional(int, attrs.get("stop_capacity")),
        )

    def build_token_type(self, attrs: dict[str, str]) -> mashinky.models.TokenType:
        name = self.config.english.get(attrs["name"])
        icon = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=name,
            group="token_type",
        )
        return mashinky.models.TokenType(id=attrs["id"], icon=icon, name=name)

    def build_color(self, attrs: dict[str, str]) -> mashinky.models.Color:
        return mashinky.models.Color(
            id=attrs["id"],
            name=attrs["name"],
            red=int(attrs["red"]),
            green=int(attrs["green"]),
            blue=int(attrs["blue"]),
        )

    def build_wagon_type(
        self,
        attrs: dict[str, str],
        token_types: dict[str, mashinky.models.TokenType],
    ) -> mashinky.models.WagonType:
        id: str = attrs["id"]
        name: str = attrs["name"]

        logger.debug("Building vehicle", id=id, name=name)

        icon: str = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon"],
            name=attrs["name"],
            group="wagon_type_icon",
        )
        icon_color: str = self.images.extract_icon(
            icon_texture=attrs["icon_texture"],
            icon=attrs["icon_color"],
            name=attrs["name"],
            group="wagon_type_icon_color",
        )
        epoch_start, epoch_end = parse_epoch(attrs["epoch"])
        track = mashinky.models.Track(int(attrs["track"]))
        weight_empty: int = int(attrs["weight_empty"])
        weight_full: int = int(attrs["weight_full"])
        depo_upgrade: bool = attrs.get("depo_upgrade") == "0"

        main_length = float(attrs["length"])
        head_length = float(attrs.get("head_length", 0.0))
        tail_length = float(attrs.get("tail_length", 0.0))
        length: float = round(head_length + main_length + tail_length, 2)

        cargo_type_id: str = attrs.get("cargo", None)
        capacity: int = int(attrs.get("capacity", 0))

        cost = [
            mashinky.models.Cost(
                wagon_type_id=attrs["id"],
                token_type=token_types[token_type_id],
                amount=amount,
            )
            for amount, token_type_id in parse_payments(attrs.get("cost"))
        ]
        sell = [
            mashinky.models.Sell(
                wagon_type_id=attrs["id"],
                token_type=token_types[token_type_id],
                amount=amount,
            )
            for amount, token_type_id in parse_payments(attrs.get("sell"))
        ]
        fuel = [
            mashinky.models.Fuel(
                wagon_type_id=attrs["id"],
                token_type=token_types[token_type_id],
                amount=amount,
            )
            for amount, token_type_id in parse_payments(attrs.get("fuel_cost"))
        ]

        kwargs = dict(
            id=id,
            name=name,
            icon=icon,
            icon_color=icon_color,
            epoch_start=epoch_start,
            epoch_end=epoch_end,
            track=track,
            weight_empty=weight_empty,
            weight_full=weight_full,
            length=length,
            cost=cost,
            sell=sell,
            fuel=fuel,
            cargo_type_id=cargo_type_id,
            capacity=capacity,
            depo_upgrade=depo_upgrade,
        )

        if attrs["vehicle_type"] == "0" and attrs.get("power"):
            power = int(attrs["power"])
            max_speed = int(attrs["max_speed"])
            max_speed_reverse = optional(int, attrs.get("max_speed_reverse"))
            return mashinky.models.Engine(
                **kwargs,
                power=power,
                max_speed=max_speed,
                max_speed_reverse=max_speed_reverse,
            )
        elif attrs["vehicle_type"] == "0":
            return mashinky.models.Wagon(**kwargs)
        elif attrs["vehicle_type"] == "1":
            return mashinky.models.RoadVehicle(**kwargs)
        raise ValueError(attrs["vehicle_type"])


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
) -> typing.Tuple[typing.Optional[mashinky.models.Epoch], typing.Optional[mashinky.models.Epoch]]:
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

    return mashinky.models.Epoch(int(start)), mashinky.models.Epoch(int(end))


@parse
def parse_track(value: str) -> mashinky.models.Track:
    return mashinky.models.Track(int(value))


def parse_payments(
    value: typing.Optional[str],
    default_token_type: str = "F0000000",
) -> typing.Sequence[typing.Tuple[int, str]]:
    if value is None or value == "0":
        return []

    if matches := re.findall(r"(?P<amount>-?\d+)(?:\[(?P<token_type_id>\w+)])?", value):
        return [
            (abs(int(amount)), token_type or default_token_type) for amount, token_type in matches
        ]

    raise ValueError(f"Could not parse {value} as payments")
