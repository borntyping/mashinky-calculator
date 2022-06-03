from __future__ import annotations

import collections
import dataclasses
import enum
import itertools
import math
import typing

from mashinky.models import Engine, Epoch, Amount, TokenType, Track, Wagon, CargoType, WagonType

T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class Train:
    wagon_types: tuple[WagonType, ...]

    def __iter__(self) -> typing.Iterator[WagonType]:
        return iter(self.wagon_types)

    @property
    def wagon_type_set(self) -> frozenset[WagonType]:
        return frozenset(self.wagon_types)

    @property
    def wagon_type_counter(self) -> collections.Counter[WagonType]:
        return collections.Counter(self.wagon_types)

    @property
    def engines(self) -> typing.Generator[Engine]:
        return (wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Engine))

    @property
    def wagons(self) -> typing.Generator[Wagon]:
        return (wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Wagon))

    # WagonType properties

    @property
    def epoch_start(self) -> typing.Optional[Epoch]:
        epochs = {
            wagon_type.epoch_start for wagon_type in self.wagon_types if wagon_type.epoch_start
        }
        return max(epochs) if epochs else None

    @property
    def epoch_end(self) -> typing.Optional[Epoch]:
        epochs = {wagon_type.epoch_end for wagon_type in self.wagon_types if wagon_type.epoch_start}
        return min(epochs) if epochs else None

    @property
    def track(self) -> Track:
        return max(wagon_type.track for wagon_type in self.wagon_types)

    @property
    def weight_empty(self) -> int:
        return sum(wagon_type.weight_empty for wagon_type in self.wagon_types)

    @property
    def weight_full(self) -> int:
        return sum(wagon_type.weight_full for wagon_type in self.wagon_types)

    @property
    def length(self) -> float:
        return sum(wagon_type.length for wagon_type in self.wagon_types)

    @property
    def depo_upgrade(self) -> bool:
        return any(wagon_type.depo_upgrade for wagon_type in self.wagon_types)

    @property
    def cargo_types(self) -> typing.Sequence[CargoType]:
        # This relies on dict ordering.
        unique = {w.cargo_type: None for w in self.wagon_types if w.cargo_type is not None}
        return list(unique.keys())

    @property
    def cargo(self) -> typing.Counter[WagonType]:
        counter = collections.Counter()

        for wagon_type in self.wagon_types:
            if wagon_type.cargo_type:
                counter[wagon_type.cargo_type] += wagon_type.capacity

        return counter

    @property
    def capacity(self) -> int:
        return sum(wagon_type.capacity for wagon_type in self.wagon_types)

    @staticmethod
    def _payments(payments: typing.Iterable[Amount]) -> dict[TokenType, int]:
        total = collections.Counter()

        for payment in sorted(payments, key=lambda p: p.token_type.id):
            total[payment.token_type] += payment.amount

        return total

    @property
    def cost(self) -> dict[TokenType, int]:
        return self._payments(payment for wt in self.wagon_types for payment in wt.cost)

    @property
    def sell(self) -> dict[TokenType, int]:
        return self._payments(payment for wt in self.wagon_types for payment in wt.sell)

    @property
    def fuel(self) -> dict[TokenType, int]:
        return self._payments(payment for wt in self.wagon_types for payment in wt.fuel)

    # Engine properties

    @property
    def power(self) -> int:
        return sum(engine.power for engine in self.engines)

    @property
    def max_speed(self) -> int:
        return min(engine.max_speed for engine in self.engines)

    @property
    def recommended_weight(self) -> int:
        return sum(engine.recommended_weight for engine in self.engines)

    # Train properties

    @property
    def bonus_incomes(self) -> list[WagonType]:
        return [wt for wt in self.wagon_types if wt.bonus_income]

    @property
    def bonus_cargo(self) -> typing.dict[WagonType, int]:
        counter = collections.Counter()

        # No idea if this is max or sum or something else.
        bonuses = [wt.bonus_income for wt in self.wagon_types if wt.bonus_income]
        bonus = max(bonuses) if bonuses else 0
        multiplier = (bonus + 100) / 100

        return {cargo_type: round(multiplier * amount) for cargo_type, amount in self.cargo.items()}

    @property
    def bonus_capacity(self) -> int:
        return sum(self.bonus_cargo.values())

    @property
    def estimated_capacity(self) -> int:
        return sum(self.bonus_cargo[wagon_type] for wagon_type in self.wagon_types)

    def add_wagons(self, wagon_types: typing.Sequence[WagonType]):
        """Inserts wagons after the last engine."""
        index = max(i for i, wt in enumerate(self.wagon_types, 1) if isinstance(wt, Engine))
        wagon_types = (*self.wagon_types[:index], *wagon_types, *self.wagon_types[index:])
        return dataclasses.replace(self, wagon_types=wagon_types)

    def add_wagons_to_recommended_weight(self: T, wagon: Wagon) -> T:
        count = math.floor((self.recommended_weight - self.weight_full) / wagon.weight_full)
        return self.add_wagons(wagon.times(count))

    def add_wagons_to_length(self: T, wagon: Wagon, length: int) -> T:
        count = math.floor((length - self.length) / wagon.length)
        return self.add_wagons(wagon.times(count))

    def is_over_recommended_weight_empty(self) -> bool:
        return self.weight_empty > self.recommended_weight

    def is_over_recommended_weight_full(self) -> bool:
        return self.weight_full > self.recommended_weight

    @property
    def weight_usage(self) -> float:
        return self.weight_full / self.recommended_weight

    def length_usage(self, length: int) -> float:
        return self.length / length


class MaximumWeight(enum.Enum):
    FULL = "full"
    EMPTY = "empty"
    INFINITE = "infinite"


class MaximumLength(enum.Enum):
    SHORT = "short"
    LONG = "long"
    INFINITE = "infinite"


@dataclasses.dataclass(frozen=True)
class Results:
    trains: list[Train]

    after_generation: list[Train]
    after_discarding: list[Train]
    after_deduplication: list[Train]
    after_applying_rules: list[Train]


@dataclasses.dataclass(frozen=True)
class Options:
    epoch: Epoch
    all_engines: typing.Sequence[Engine]
    all_wagons: typing.Sequence[Wagon]
    all_cargos: typing.Sequence[CargoType]

    selected_engines: typing.Sequence[Engine]
    selected_wagons: typing.Sequence[Wagon]
    selected_cargos: typing.Sequence[CargoType]

    include_depo_upgrade: bool
    include_quest_reward: bool
    maximum_engines: int = 2
    maximum_weight: MaximumWeight = MaximumWeight.FULL
    maximum_length: MaximumLength = MaximumLength.SHORT
    station_length_short: int = 6
    station_length_long: int = 8

    passenger_wagon_suggestions: typing.ClassVar[dict[str, list[list[str]]]] = {
        "Coach car": [
            ["1st Class", "Pwg PR-14"],
            ["1st Class"],
            ["Pwg PR-14"],
        ],
        "1st Class": [
            ["2nd class", "Pwg PR-14"],
            ["Dining car", "Pwg PR-14"],
            ["2nd class"],
            ["Dining car"],
            ["Pwg PR-14"],
        ],
        "2nd class": [
            ["1st Class", "Pwg PR-14"],
            ["Dining car", "Pwg PR-14"],
            ["1st Class"],
            ["Dining car"],
            ["Pwg PR-14"],
        ],
        "SCF": [
            ["SCF Diner", "SCF Mail"],
            ["SCF Diner"],
            ["SCF Mail"],
        ],
        "SCG": [
            ["SCG Diner", "SCF Mail"],
            ["SCG Diner"],
            ["SCG Mail"],
        ],
        "SGV class 1": [
            ["SGV Diner", "SCF Mail"],
            ["SGV Diner"],
            ["SGV Mail"],
        ],
        "SGV class 2": [
            ["SGV class 1", "SCF post"],
            ["SGV bar", "SCF post"],
            ["SGV class 1"],
            ["SGV bar"],
            ["SGV post"],
        ],
    }

    def collect(self) -> Results:
        wagons = [w for w in self.selected_wagons if w.cargo_type in self.selected_cargos]
        groups = [
            group
            for engine, wagon in itertools.product(self.selected_engines, wagons)
            for group in self.groups(engine, wagon)
        ]

        trains = after_generation = [train for group in groups for train in group]
        trains = after_discarding = [train for group in groups for train in self.discard(group)]
        trains = after_deduplication = self.deduplicate(trains)
        trains = after_applying_rules = self.apply_rules(trains)
        trains = sorted(trains, key=lambda t: t.bonus_capacity, reverse=True)

        return Results(
            trains=trains,
            after_generation=after_generation,
            after_discarding=after_discarding,
            after_deduplication=after_deduplication,
            after_applying_rules=after_applying_rules,
        )

    def groups(
        self,
        engine: Engine,
        wagon: Wagon,
        max_engines: int = 2,
    ) -> list[list[Train]]:
        heads = [Train(engine.times(engine_count)) for engine_count in range(1, max_engines + 1)]

        yield from self._groups(heads, wagon)

        if wagon.cargo_type.is_passengers and wagon.name in self.passenger_wagon_suggestions:
            wagons_by_name = {wagon.name: wagon for wagon in self.all_wagons}
            suggestions = [
                [wagons_by_name[name] for name in names if name in wagons_by_name]
                for names in self.passenger_wagon_suggestions[wagon.name]
            ]

            for suggestion in suggestions:
                yield from self._groups([head.add_wagons(suggestion) for head in heads], wagon)

    def _groups(self, heads: list[Train], wagon: Wagon) -> list[list[Train]]:
        return [
            [head.add_wagons_to_recommended_weight(wagon) for head in heads],
            [head.add_wagons_to_length(wagon, self.station_length_short) for head in heads],
            [head.add_wagons_to_length(wagon, self.station_length_long) for head in heads],
        ]

    @staticmethod
    def discard(trains: list[Train]) -> typing.Generator[Train]:
        """
        Remove any trains that are worse than the one before.

        This should remove any trains that add more engines for no improvement.
        """
        # yield from trains
        # return

        best = trains[0]

        if best.capacity > 0:
            yield trains[0]

        for train in trains[1:]:
            if train.capacity > best.capacity:
                yield train

    @staticmethod
    def deduplicate(trains: list[Train]) -> list[Train]:
        """Deduplicate engine+wagon variations with the same capacity."""
        capacities: dict[tuple[frozenset[WagonType], int], Train] = {}

        for train in trains:
            # This uses setdefault instead of []=, so the first train wins.
            capacities.setdefault(train, train)

        return list(capacities.values())

    def apply_rules(self, trains: list[Train]) -> list[Train]:
        return list(filter(self._should_include, trains))

    def _should_include(self, train: Train) -> bool:
        if self.maximum_weight == MaximumWeight.FULL:
            if train.weight_full > train.recommended_weight:
                return False
        elif self.maximum_weight == MaximumWeight.EMPTY:
            if train.weight_empty > train.recommended_weight:
                return False

        if self.maximum_length == MaximumLength.SHORT:
            if train.length > self.station_length_short:
                return False
        elif self.maximum_length == MaximumLength.LONG:
            if train.length > self.station_length_long:
                return False

        return True

    @property
    def display_station_length(self) -> int:
        if self.maximum_length == MaximumLength.SHORT:
            return self.station_length_short

        return self.station_length_long
