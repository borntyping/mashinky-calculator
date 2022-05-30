import dataclasses
import pathlib
import typing

import mashinky.extract.config
import mashinky.extract.images


@dataclasses.dataclass(frozen=True)
class CargoType:
    icon: pathlib.Path


@dataclasses.dataclass(frozen=True)
class TokenType:
    icon: pathlib.Path


@dataclasses.dataclass(frozen=True)
class Color:
    name: str
    red: int
    green: int
    blue: int


@dataclasses.dataclass(frozen=True)
class Vehicle:
    id: str
    name: str


@dataclasses.dataclass(frozen=True)
class Models:
    cargo_types: typing.Mapping[str, CargoType]
    token_types: typing.Mapping[str, TokenType]
    colors: typing.Mapping[str, Color]

    engines: typing.Mapping[str, Vehicle]
    wagons: typing.Mapping[str, Vehicle]
    road_vehicles: typing.Mapping[str, Vehicle]


class ModelsBuilder:
    def build(
        self,
        config: mashinky.extract.config.Config,
        images: mashinky.extract.images.Images,
    ):
        cargo_types = {
            identifier: CargoType(
                icon=images.cargo_types_icons[identifier],
            )
            for identifier, attrs in config.cargo_types.items()
        }

        token_types = {
            identifier: TokenType(
                icon=images.token_types_icons[identifier],
            )
            for identifier, attrs in config.token_types.items()
        }

        colors = {
            identifier: Color(
                name=attrs["name"],
                red=int(attrs["red"]),
                green=int(attrs["green"]),
                blue=int(attrs["blue"]),
            )
            for identifier, attrs in config.colors.items()
        }

        engines = []
        wagons = []
        road_vehicles = []

        for wagon_id, wagon_type in config.wagon_types.items():
            vehicle_type = int(wagon_type["vehicle_type"])
            icon = images.wagon_types_icons[wagon_type["id"]]

            if vehicle_type == 0:
                # Engine or wagon
                ...
            else:
                # Road vehicle
                ...

        return cargo_types, token_types, colors
