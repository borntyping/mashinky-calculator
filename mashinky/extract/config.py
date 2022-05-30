from __future__ import annotations

import dataclasses
import typing
import warnings

import bs4.builder
import bs4.element
import structlog

import mashinky.extract.reader
import mashinky.console

logger = structlog.get_logger(logger_name=__name__)

Things = dict[str, dict[str, str]]
Resources = dict[str, dict[str, str]]


@dataclasses.dataclass(frozen=True, kw_only=True)
class Config:
    cargo_types: Things
    token_types: Things
    colors: Things
    tcoords: Things
    texts: Resources
    town_names: Resources
    wagon_types: Things

    def patch(self) -> Config:
        # Incorrect texture reference?
        if "004849B6" in self.wagon_types:
            assert self.wagon_types["004849B6"]["icon_texture"] == "map/gui/wagons_basic_set.png"
            self.wagon_types["004849B6"]["icon_texture"] = "map/gui/wagons_basic_set.png"

        # Unfinished wagon?
        if "1E5C2858" in self.wagon_types:
            assert "icon_texture" not in self.wagon_types["1E5C2858"]
            del self.wagon_types["1E5C2858"]

        # C8980ED0: quest glassworks
        # CE90001A: electricity
        # CE900010: transformer
        # 0BA4580F: "Gold"
        for id in ("C8980ED0", "CE90001A", "CE900010"):
            if id in self.cargo_types and self.cargo_types[id]["name"] == "0BA4580F":
                del self.cargo_types[id]["name"]

        return self

    def text(self, attrs: dict[str, str], language: str = "English") -> typing.Optional[str]:
        if name := attrs.get("name"):
            return self.texts["English"][name]

        return None


@dataclasses.dataclass(frozen=True)
class ConfigBuilder:
    readers: typing.Sequence[mashinky.extract.reader.Reader]

    def load_config(self) -> Config:
        cargo_types = self.cargo_types()
        token_types = self.token_types()
        colors = self.colors()
        tcoords = self.tcoords()
        texts = self.texts()
        town_names = self.town_names()
        wagon_types = self.wagon_types()
        return Config(
            cargo_types=cargo_types,
            token_types=token_types,
            colors=colors,
            texts=texts,
            tcoords=tcoords,
            town_names=town_names,
            wagon_types=wagon_types,
        )

    def cargo_types(self) -> Things:
        return self._xml_things("config/cargo_types.xml", name="cargotype")

    def token_types(self) -> Things:
        return self._xml_things("config/cargo_types.xml", name="tokentype")

    def colors(self) -> Things:
        return self._xml_things("config/colors.xml", name="color")

    def tcoords(self) -> Things:
        return self._xml_things("config/tcoords.xml", name="coord")

    def texts(self) -> Resources:
        return self._xml_resources("config/texts.xml")

    def town_names(self) -> Resources:
        return self._xml_resources("config/town_names.xml")

    def wagon_types(self) -> Things:
        return self._xml_things("config/wagon_types.xml", name="wagontype")

    def _xml_things(self, /, filename: str, *, name: str) -> Things:
        """Watch out for mixed case IDs."""
        return {
            element["id"].upper(): element.attrs
            for soup in self._soups(filename)
            for element in soup.find_all(name)
        }

    def _xml_resources(self, /, filename: str) -> Resources:
        return {
            resources["caption"]: {
                element["name"]: self._mashinky_string(element)
                for element in resources.find_all("string")
            }
            for soup in self._soups(filename)
            for resources in soup.find_all("resources")
        }

    def _mashinky_string(self, element: bs4.element.Tag) -> typing.Optional[str]:
        if element.string is None:
            return None

        return element.string[1:-1]

    def _soups(self, filename: str) -> typing.Iterable[bs4.BeautifulSoup]:
        for reader in self.readers:
            try:
                logger.info("Loading file", filename=filename, base=reader.base.as_posix())
                yield self._soup(reader.read_text(filename))
            except FileNotFoundError:
                pass

    @staticmethod
    def _soup(text: str) -> bs4.BeautifulSoup:
        """
        XML requires a single root node, and these files have many root nodes.
        We use an extremely lenient HTML parser instead.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", bs4.builder.XMLParsedAsHTMLWarning)
            return bs4.BeautifulSoup(text, "html.parser")
