from __future__ import annotations

import dataclasses
import decimal
import enum
import math
import typing
import click


MPH = typing.NewType("MPH", int)
Tons = typing.NewType("Tons", int)
HP = typing.NewType("HP", int)


class Era(enum.IntEnum):
    EARLY_STEAM = 1
    STEAM = 2
    EARLY_DIESEL = 3
    DIESEL = 4
    EARLY_ELECTRIC = 5

    @classmethod
    def names(cls) -> typing.Mapping[str, Era]:
        return {
            "early steam": cls.EARLY_STEAM,
            "steam": cls.STEAM,
            "early diesel": cls.EARLY_DIESEL,
            "diesel": cls.DIESEL,
            "early electric": cls.EARLY_ELECTRIC,
        }

    @classmethod
    def named(cls, name: str) -> Era:
        return Era(cls.names()[name])

    @classmethod
    def numerals(cls) -> typing.Mapping[Era, str]:
        return {
            cls.EARLY_STEAM: "Ⅰ",
            cls.STEAM: "Ⅱ",
            cls.EARLY_DIESEL: "Ⅲ",
            cls.DIESEL: "Ⅳ",
            cls.EARLY_ELECTRIC: "Ⅴ",
        }

    @property
    def numeral(self) -> str:
        return self.numerals()[self]

    def __str__(self) -> str:
        return self.numeral


class Material(enum.Enum):
    # Basic materials
    LOGS = "Logs"
    COAL = "Coal"
    IRON_ORE = "Iron Ore"
    CRUDE_OIL = "Crude Oil"
    SAND = "Sand"
    FOOD = "Food"

    # Processed materials
    TIMBER = "Timber"
    IRON = "Iron"
    GOODS = "Goods"
    DIESEL = "Diesel"
    STEEL = "Steel"

    # Commercial materials
    PASSENGERS = "Passengers"
    MAIL = "Mail"

    def __str__(self) -> str:
        return self.value


class Token(enum.Enum):
    MONEY = "money"
    TIMBER = "timber"
    COAL = "coal"
    IRON = "iron"
    DIESEL = "diesel"
    STEEL = "steel"
    ELECTRIC = "electric"

    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class Payment:
    amount: int
    token: Token

    def __str__(self) -> str:
        return f"{self.colourful_amount()} {self.token} tokens"

    def colourful_amount(self) -> str:
        amount = f"{self.amount} {self.token}".ljust(13)

        if self.token is Token.MONEY:
            return click.style(amount, fg="black", bg="green")
        elif self.token is Token.TIMBER:
            return click.style(amount, fg="black", bg="bright_white")
        elif self.token is Token.COAL:
            return click.style(amount, fg="white", bg="black")
        elif self.token is Token.IRON:
            return click.style(amount, fg="black", bg="bright_black")
        elif self.token is Token.DIESEL:
            return click.style(amount, fg="black", bg="magenta")
        elif self.token is Token.STEEL:
            return click.style(amount, fg="black", bg="white")
        elif self.token is Token.ELECTRIC:
            return click.style(amount, fg="black", bg="yellow")

    @staticmethod
    def payments(payments: typing.Sequence[Payment]) -> str:
        return "".join([payment.colourful_amount() for payment in payments])


@dataclasses.dataclass(frozen=True)
class Stock:
    name: str
    era: Era

    def __str__(self) -> str:
        return self.name


@dataclasses.dataclass(frozen=True)
class Engine(Stock):
    speed: int  # mph
    capacity: int  # tons
    power: int  # hp
    weight: int  # tons
    length: float  # tiles

    cost: typing.Sequence[Payment]
    operating_cost: typing.Sequence[Payment]

    quest_reward: bool = False
    requires_depot_extension: bool = False


@dataclasses.dataclass(frozen=True)
class Wagon(Stock):
    cargo: Material
    capacity: int
    unloaded: int  # tons
    loaded: int  # tons
    length: float  # tiles

    cost: typing.Sequence[Payment]

    special: typing.Optional[str] = None
    requires_depot_extension: bool = False


class Limit(enum.Enum):
    LENGTH = "length"
    WEIGHT = "weight"

    def __str__(self) -> str:
        fg = "bright_black" if self is Limit.WEIGHT else "white"
        return click.style(self.value, fg=fg)


@dataclasses.dataclass(frozen=True)
class Train:
    engine: Engine
    wagon: Wagon

    engine_count: int
    wagon_count: int
    wagon_limit: Limit

    @property
    def capacity(self) -> int:
        return self.wagon.capacity * self.wagon_count

    @property
    def weight(self) -> float:
        return self.loaded_weight()

    @property
    def usage(self) -> float:
        return self.loaded_usage()

    @property
    def length(self) -> float:
        return (
            self.engine.length * self.engine_count
            + self.wagon.length * self.wagon_count
        )

    def unloaded_weight(self) -> int:
        return self._weight(wagon_weight=self.wagon.unloaded)

    def loaded_weight(self) -> int:
        return self._weight(wagon_weight=self.wagon.loaded)

    def unloaded_usage(self) -> float:
        return self.unloaded_weight() / (self.engine.capacity * self.engine_count)

    def loaded_usage(self) -> float:
        return self.loaded_weight() / (self.engine.capacity * self.engine_count)

    def format_usage(self) -> str:
        loaded_usage = self.loaded_usage()
        if loaded_usage >= 0.75:
            return click.style(str(loaded_usage), fg="green")
        if loaded_usage >= 0.50:
            return click.style(str(loaded_usage), fg="yellow")
        return click.style(str(loaded_usage), fg="red")

    def _weight(self, wagon_weight: int) -> int:
        engine = self.engine.weight * self.engine_count
        wagon = wagon_weight * self.wagon_count
        return engine + wagon

    @classmethod
    def build(
        cls,
        engine: Engine,
        wagon: Wagon,
        station_length: int,
        engine_count: int = 1,
    ) -> Train:
        max_wagon_length = station_length - (engine.length * engine_count)
        max_wagon_count_for_length = math.floor(max_wagon_length / wagon.length)

        max_wagon_weight = (engine.capacity - engine.weight) * engine_count
        max_wagon_count_for_weight = math.floor(max_wagon_weight / wagon.loaded)

        if max_wagon_count_for_length < max_wagon_count_for_weight:
            wagon_count = max_wagon_count_for_length
            wagon_limit = Limit.LENGTH
        else:
            wagon_count = max_wagon_count_for_weight
            wagon_limit = Limit.WEIGHT

        return Train(
            engine=engine,
            wagon=wagon,
            engine_count=engine_count,
            wagon_count=wagon_count,
            wagon_limit=wagon_limit,
        )
