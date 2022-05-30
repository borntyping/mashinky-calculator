from __future__ import annotations

import dataclasses
import pathlib
import typing

import PIL.Image
import structlog

import mashinky.console
import mashinky.extract.config
import mashinky.extract.reader

logger = structlog.get_logger(logger_name=__name__)

Attrs = dict[str, str]


@dataclasses.dataclass(frozen=True)
class Coord:
    x: int
    y: int
    w: int
    h: int

    @classmethod
    def from_attrs(cls, attrs: Attrs) -> Coord:
        return cls(
            x=int(attrs["x"]),
            y=int(attrs["y"]),
            w=int(attrs["w"]),
            h=int(attrs["h"]),
        )


@dataclasses.dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    @classmethod
    def from_attrs(cls, attrs: Attrs) -> Color:
        return cls(
            r=int(attrs["red"]),
            g=int(attrs["green"]),
            b=int(attrs["blue"]),
        )


@dataclasses.dataclass(frozen=True)
class Images:
    cargo_types_icons: typing.Mapping[str, pathlib.Path]
    token_types_icons: typing.Mapping[str, pathlib.Path]
    wagon_types_icons: typing.Mapping[str, pathlib.Path]


@dataclasses.dataclass(frozen=True)
class ImagesBuilder:
    readers: typing.Sequence[mashinky.extract.reader.Reader]
    directory: pathlib.Path

    def extract_images(self, config: mashinky.extract.config.Config) -> Images:
        coords = {i: Coord.from_attrs(attrs) for i, attrs in config.tcoords.items()}
        colors = {i: Color.from_attrs(attrs) for i, attrs in config.colors.items()}
        return Images(
            cargo_types_icons=self.extract_icons(config.cargo_types, coords, colors, "cargo_types"),
            token_types_icons=self.extract_icons(config.token_types, coords, colors, "token_types"),
            wagon_types_icons=self.extract_icons(config.wagon_types, coords, colors, "wagon_types"),
        )

    def extract_icons(
        self,
        things: dict[str, dict[str, str]],
        coords: typing.Mapping[str, Coord],
        colors: typing.Mapping[str, Color],
        category: str,
    ) -> typing.Mapping[str, pathlib.Path]:
        self.directory.mkdir(exist_ok=True)
        (self.directory / "images").mkdir(exist_ok=True)
        return {
            identifier: self.extract_icon(attrs, coords, colors, category)
            for identifier, attrs in things.items()
            if all(("icon_texture" in attrs, "icon" in attrs))
        }

    def extract_icon(
        self,
        attrs: typing.Mapping[str, str],
        coords: typing.Mapping[str, Coord],
        colors: typing.Mapping[str, Color],
        category: str,
    ) -> pathlib.Path:
        identifier = attrs["id"]
        icon_texture = attrs["icon_texture"]
        coord = coords[attrs["icon"]]

        output_path = self.directory / "images" / category / f"{identifier}.png"

        logger.info(
            "Extracting icon",
            icon_texture=icon_texture,
            output_path=output_path.relative_to(self.directory).as_posix(),
        )

        if not output_path.exists():
            output_path.parent.mkdir(exist_ok=True)

            paths = [reader.path_object(icon_texture) for reader in self.readers]
            paths = [path for path in paths if path.exists()]

            if not paths:
                raise FileNotFoundError(icon_texture)

            x1, y1, x2, y2 = (coord.x, coord.y, coord.x + coord.w, coord.y + coord.h)
            box = (x1 * 2, y1 * 2, x2 * 2, y2 * 2)

            texture = PIL.Image.open(paths[0])
            image = texture.crop(box)
            image.save(output_path)

        return output_path.relative_to(self.directory)
