import abc
import dataclasses
import json
import pathlib
import pprint
import textwrap
import zipfile

import typing.io


@dataclasses.dataclass(frozen=True)
class Reader(abc.ABC):
    base: pathlib.Path

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.base.as_posix())

    def path_object(self, filename: str) -> typing.Union[pathlib.Path, zipfile.Path]:
        raise NotImplementedError

    def read_text(self, filename: str) -> str:
        path = self.path_object(filename)

        if not path.exists():
            raise FileNotFoundError(f"{filename} does not exist")

        errors = {}

        for encoding in (None, "utf-8", "utf-16-le", "utf-16-be"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError as error:
                errors[encoding] = {
                    "reason": error.reason,
                    "encoding": error.encoding,
                    "start": error.start,
                    "end": error.end,
                }

        raise RuntimeError(f"Could not load {filename} from {path} {json.dumps(errors, indent=2)}")

    def open(self, filename: str, mode: typing.Literal["r", "w"]) -> typing.io.IO:
        path = self.path_object(filename)

        if not path.exists():
            raise FileNotFoundError(f"{filename} does not exist")

        return path.open(mode)


class DirReader(Reader):
    def path_object(self, filename: str) -> pathlib.Path:
        return self.base / filename


class ZipReader(Reader):
    def path_object(self, filename: str) -> zipfile.Path:
        return zipfile.Path(self.base, at=filename)
