import abc
import dataclasses
import pathlib
import zipfile

import typing.io


class Reader(abc.ABC):
    def path(self, filename: str) -> typing.Union[pathlib.Path, zipfile.Path]:
        raise NotImplementedError

    def read_text(self, filename: str) -> str:
        path = self.path(filename)

        if not path.exists():
            raise FileNotFoundError(f"{filename} does not exist")

        return path.read_text()

    def open(self, filename: str, mode: typing.Literal["r", "w"]) -> typing.io.IO:
        path = self.path(filename)

        if not path.exists():
            raise FileNotFoundError(f"{filename} does not exist")

        return path.open(mode)


@dataclasses.dataclass(frozen=True)
class DirReader(Reader):
    directory: pathlib.Path

    def path(self, filename: str) -> pathlib.Path:
        return self.directory / filename


@dataclasses.dataclass(frozen=True)
class ZipReader(Reader):
    mod: pathlib.Path

    def path(self, filename: str) -> zipfile.Path:
        return zipfile.Path(self.mod, at=filename)
