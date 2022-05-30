import dataclasses
import json
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
    icon: pathlib.Path


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

        engines = {}
        wagons = {}
        road_vehicles = {}

        for identifier, attrs in config.wagon_types.items():
            vehicle_type = int(attrs["vehicle_type"])
            name = attrs["name"]
            icon = images.wagon_types_icons[attrs["id"]]

            if vehicle_type == 0 and "cargo" not in attrs:
                engines[identifier] = Vehicle(
                    id=identifier,
                    name=name,
                    icon=icon,
                )
            elif vehicle_type == 0 and "cargo" in attrs:
                wagons[identifier] = Vehicle(
                    id=identifier,
                    name=name,
                    icon=icon,
                )
            elif vehicle_type == 1:
                road_vehicles[identifier] = Vehicle(
                    id=identifier,
                    name=name,
                    icon=icon,
                )

        return Models(
            cargo_types=cargo_types,
            token_types=token_types,
            colors=colors,
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
