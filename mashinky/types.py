from __future__ import annotations

import dataclasses
import enum
import itertools
import math
import typing


@enum.unique
class Era(enum.IntEnum):
    EARLY_STEAM = 1
    STEAM = 2
    EARLY_DIESEL = 3
    DIESEL = 4
    EARLY_ELECTRIC = 5
    ELECTRIC = 6

    descriptions: typing.Mapping[Era, str]

    def __str__(self) -> str:
        return self.description

    @property
    def index(self) -> int:
        return self.value

    @property
    def description(self) -> str:
        return self.descriptions[self.value].title()


Era.descriptions = {
    Era.EARLY_STEAM: "Early steam",
    Era.STEAM: "Steam",
    Era.EARLY_DIESEL: "Early diesel",
    Era.DIESEL: "Diesel",
    Era.EARLY_ELECTRIC: "Early electric",
}

Era.numerals = {
    Era.EARLY_STEAM: "Ⅰ",
    Era.STEAM: "Ⅱ",
    Era.EARLY_DIESEL: "Ⅲ",
    Era.DIESEL: "Ⅳ",
    Era.EARLY_ELECTRIC: "Ⅴ",
}


Era.names = {
    "early steam": Era.EARLY_STEAM,
    "steam": Era.STEAM,
    "early diesel": Era.EARLY_DIESEL,
    "diesel": Era.DIESEL,
    "early electric": Era.EARLY_ELECTRIC,
}


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

    def __mul__(self, other: int) -> Payment:
        return dataclasses.replace(self, amount=self.amount * other)


@dataclasses.dataclass(frozen=True)
class Stock:
    name: str
    era: Era
    requires_depot_extension: bool

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

    @property
    def operating_cost_tokens(self) -> typing.Set[Token]:
        return {payment.token for payment in self.operating_cost}

    @property
    def possible_counts(self) -> typing.Iterable[int]:
        return (1,) if self.quest_reward else (1, 2)


@dataclasses.dataclass(frozen=True)
class Wagon(Stock):
    cargo: Material
    capacity: int
    unloaded: int  # tons
    loaded: int  # tons
    length: float  # tiles

    cost: typing.Sequence[Payment]

    special: typing.Optional[str] = None


class Limit(enum.Enum):
    LENGTH = "length"
    WEIGHT = "weight"


@dataclasses.dataclass(frozen=True)
class Train:
    engine: Engine
    wagon: Wagon

    engine_count: int
    wagon_count: int
    wagon_limit: Limit

    @property
    def speed(self) -> float:
        return self.engine.speed

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
        return self.engine.length * self.engine_count + self.wagon.length * self.wagon_count

    def unloaded_weight(self) -> int:
        return self._weight(wagon_weight=self.wagon.unloaded)

    def loaded_weight(self) -> int:
        return self._weight(wagon_weight=self.wagon.loaded)

    def unloaded_usage(self) -> float:
        return self.unloaded_weight() / self.maximum_weight()

    def loaded_usage(self) -> float:
        return self.loaded_weight() / self.maximum_weight()

    def _weight(self, wagon_weight: int) -> int:
        engine = self.engine.weight * self.engine_count
        wagon = wagon_weight * self.wagon_count
        return engine + wagon

    def maximum_weight(self) -> int:
        return self.engine.capacity * self.engine_count

    @property
    def multiple_engines(self) -> typing.Optional[str]:
        return f"{self.engine_count}" if self.engine_count > 1 else None

    @property
    def multiple_wagons(self) -> typing.Optional[str]:
        return f"{self.wagon_count}" if self.wagon_count > 1 else None

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

    @classmethod
    def combinations(
        cls,
        engines: typing.Iterable[Engine],
        wagons: typing.Iterable[Wagon],
        station_length: int,
        include_all_doubles: bool = False,
    ) -> typing.Iterable[Train]:
        for engine, wagon in itertools.product(engines, wagons):
            single = cls.build(engine, wagon, station_length, 1)
            double = cls.build(engine, wagon, station_length, 2)

            yield single

            if include_all_doubles:
                yield double
            # Skip double-header trains for engines that come from quest rewards.
            elif engine.include_quest_reward:
                continue
            # Only include double headers when they have a greater capacity.
            elif double.capacity > single.capacity:
                yield double
