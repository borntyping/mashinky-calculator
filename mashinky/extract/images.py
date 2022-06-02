from __future__ import annotations

import dataclasses
import pathlib
import typing

import PIL.Image
import structlog

import mashinky.extract.config
import mashinky.extract.reader

logger = structlog.get_logger(logger_name=__name__)

Attrs = dict[str, str]


@dataclasses.dataclass(frozen=True)
class ImageFactory:
    readers: typing.Sequence[mashinky.extract.reader.Reader]
    tcoords: typing.Mapping[str, dict[str, str]]
    directory: pathlib.Path

    def extract_icon(
        self,
        *,
        icon_texture: str,
        icon: str,
        name: str,
        group: str,
    ) -> str:
        output_path = self.directory / "images" / group / f"{name}.png"

        logger.debug(
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

            tcoord = self.tcoords[icon]

            x = int(tcoord["x"]) * 2
            y = int(tcoord["y"]) * 2
            w = int(tcoord["w"]) * 2
            h = int(tcoord["h"]) * 2

            texture = PIL.Image.open(paths[0])
            image = texture.crop((x, y, x + w, y + h))
            image.save(output_path)

        return output_path.relative_to(self.directory).as_posix()
