from __future__ import annotations

import pathlib
import typing

import pydantic
import appdirs
import contextlib

from mashinky.engines import ENGINES
from mashinky.types import Engine, Era, Stock, Wagon
from mashinky.wagons import WAGONS

S = typing.TypeVar("S", bound=Stock)


APP_NAME = "mashinky-calculator"
APP_AUTHOR = "borntyping"
APP_VERSION = "1.0"


class State(pydantic.BaseModel, contextlib.AbstractContextManager):
    era: Era = pydantic.Field(default=Era.EARLY_STEAM)
    station_length: int = pydantic.Field(default=6, ge=1, le=8)
    depot_extension: bool = pydantic.Field(default=False)
    quest_rewards: bool = pydantic.Field(default=False)

    def select(self, items: typing.Sequence[S]) -> typing.Sequence[S]:
        depot_extension = {True, False} if self.depot_extension else {False}
        return [
            stock
            for stock in items
            if stock.era <= self.era and stock.requires_depot_extension in depot_extension
        ]

    def engines(self) -> typing.Sequence[Engine]:
        quest_rewards = {True, False} if self.quest_rewards else {False}
        return [engine for engine in self.select(ENGINES) if engine.quest_reward in quest_rewards]

    def wagons(self) -> typing.Sequence[Wagon]:
        return self.select(WAGONS)

    @staticmethod
    def config_path() -> pathlib.Path:
        directory = appdirs.user_config_dir(APP_NAME, APP_AUTHOR, APP_VERSION)
        return pathlib.Path(directory) / "state.json"

    @staticmethod
    def history_path() -> pathlib.Path:
        directory = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR, APP_VERSION)
        return pathlib.Path(directory) / "shell.log"

    @classmethod
    def load(cls) -> State:
        if not cls.config_path().exists():
            return State()

        return cls.parse_file(cls.config_path())

    def save(self) -> None:
        self.config_path().parent.mkdir(exist_ok=True, parents=True)
        self.config_path().write_text(self.json())

    def __enter__(self) -> State:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.save()
