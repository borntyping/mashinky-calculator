from __future__ import annotations

import pathlib
import typing

import pydantic
import xdg

from mashinky.engines import ENGINES
from mashinky.types import Engine, Era, Stock, Wagon
from mashinky.wagons import WAGONS

S = typing.TypeVar("S", bound=Stock)


class State(pydantic.BaseModel):
    era: Era = pydantic.Field(default=Era.EARLY_STEAM)
    station_length: int = pydantic.Field(default=6, ge=1, le=8)
    depot_extension: bool = pydantic.Field(default=False)
    quest_rewards: bool = pydantic.Field(default=False)

    def select(self, items: typing.Sequence[S]) -> typing.Sequence[S]:
        depot_extension = {True, False} if self.depot_extension else {False}
        return [
            stock
            for stock in items
            if stock.era <= self.era
            and stock.requires_depot_extension in depot_extension
        ]

    def engines(self) -> typing.Sequence[Engine]:
        quest_rewards = {True, False} if self.quest_rewards else {False}
        return [
            engine
            for engine in self.select(ENGINES)
            if engine.quest_reward in quest_rewards
        ]

    def wagons(self) -> typing.Sequence[Wagon]:
        return self.select(WAGONS)

    @staticmethod
    def path() -> pathlib.Path:
        return xdg.xdg_config_home() / "mashinky.json"

    @classmethod
    def load(cls) -> State:
        if not cls.path().exists():
            return State()

        return cls.parse_file(cls.path())

    def save(self) -> None:
        self.path().write_text(self.json())
