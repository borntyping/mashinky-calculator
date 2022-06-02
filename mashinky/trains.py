from __future__ import annotations

import collections
import dataclasses
import itertools
import math
import typing

from mashinky.models import Engine, Epoch, Payment, TokenType, Track, Wagon, CargoType, WagonType

T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class Train:
    wagon_types: typing.Sequence[WagonType]

    def __iter__(self) -> typing.Iterator[WagonType]:
        return iter(self.wagon_types)

    @property
    def counter(self) -> collections.Counter[WagonType]:
        return collections.Counter(self.wagon_types)

    @property
    def engines(self) -> typing.Generator[Engine]:
        return (wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Engine))

    # @property
    # def engines_as_counter(self) -> typing.Set[Engine]:
    #     return collections.Counter(self.engines)

    @property
    def engine(self) -> typing.Optional[Engine]:
        engines = list(self.engines)

        if len(engines) == 1:
            return engines[0]

        return None

    @property
    def wagons(self) -> typing.Generator[Wagon]:
        return (wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Wagon))

    # @property
    # def wagons_as_counter(self) -> typing.Set[Engine]:
    #     return collections.Counter(self.wagons)

    @property
    def wagon(self) -> typing.Optional[Wagon]:
        wagons = list(self.wagons)

        if len(wagons) == 1:
            return wagons[0]

        return None

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
    def cargo_types(self) -> typing.Set[CargoType]:
        return {wt.cargo_type for wt in self.wagon_types if wt.cargo_type is not None}

    @property
    def capacity(self) -> int:
        if len(self.cargo_types) > 1:
            raise ValueError("Train has multiple cargo types")

        return sum(wagon_type.capacity for wagon_type in self.wagon_types)

    @staticmethod
    def _payments(payments: typing.Iterable[Payment]) -> dict[TokenType, int]:
        total = {}

        for payment in payments:
            total.setdefault(payment.token_type, 0)
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

    def extend(self, wagon_types: typing.Sequence[WagonType], **kwargs):
        return dataclasses.replace(self, wagon_types=[*self.wagon_types, *wagon_types], **kwargs)

    def add_wagons_to_weight(self: T, wagon: Wagon, weight: int) -> T:
        return self.extend(wagon.times(math.floor((weight - self.weight_full) / wagon.weight_full)))

    def add_wagons_to_length(self: T, wagon: Wagon, length: int) -> T:
        return self.extend(wagon.times(math.floor((length - self.length) / wagon.length)))

    # def add_wagons_within_limits(self, wagon: Wagon) -> Train:
    #     length_max = self.station_length - self.length
    #     weight_max = self.recommended_weight - self.weight_full
    #
    #     length_count = math.floor(length_max / wagon.length)
    #     weight_count = math.floor(weight_max / wagon.weight_full)
    #
    #     if length_count < weight_count:
    #         count = length_count
    #         limited_by_length = True
    #         limited_by_weight = False
    #     elif length_count > weight_count:
    #         count = weight_count
    #         limited_by_length = False
    #         limited_by_weight = True
    #     else:
    #         count = length_count
    #         limited_by_length = True
    #         limited_by_weight = True
    #
    #     wagons = [wagon for _ in range(count)]
    #     return Train(
    #         wagon_types=[*self, *wagons],
    #         station_length=self.station_length,
    #         limited_by_length=limited_by_length,
    #         limited_by_weight=limited_by_weight,
    #     )

    def is_over_recommended_weight_empty(self) -> bool:
        return self.weight_empty > self.recommended_weight

    def is_over_recommended_weight_full(self) -> bool:
        return self.weight_full > self.recommended_weight


@dataclasses.dataclass(frozen=True)
class Options:
    epoch: Epoch
    engines: typing.Sequence[Engine]
    wagons: typing.Sequence[Wagon]
    cargo_types: typing.Sequence[CargoType]

    station_length_short: int = 6
    station_length_long: int = 8
    maximum_engines: int = 2

    include_over_station_length_short: bool = True
    include_over_station_length_long: bool = False

    include_over_recommended_weight_full: bool = True
    include_over_recommended_weight_empty: bool = False

    def collect(self) -> typing.Sequence[Train]:
        # Dedupe engine+wagon variations with the same capacity
        capacities: dict[tuple[Engine, Wagon, int], Train] = {}

        wagons = [wagon for wagon in self.wagons if wagon.cargo_type in self.cargo_types]

        for engine, wagon in itertools.product(self.engines, wagons):
            for train in self.variations(engine, wagon):
                # This uses setdefault instead of []=, so the first train generated wins.
                capacities.setdefault((engine, wagon, train.capacity), train)

        trains = filter(self.should_include, capacities.values())
        trains = sorted(trains, key=lambda t: t.capacity, reverse=True)
        return trains

    def variations(
        self,
        engine: Engine,
        wagon: Wagon,
    ) -> typing.Generator[Train]:
        for engine_count in range(1, self.maximum_engines + 1):
            train = Train(engine.times(engine_count))
            yield train.add_wagons_to_weight(wagon, train.recommended_weight)
            yield train.add_wagons_to_length(wagon, self.station_length_short)
            yield train.add_wagons_to_length(wagon, self.station_length_long)

    def should_include(self, train: Train) -> bool:
        if self.include_over_station_length_short and train.length > self.station_length_short:
            return False

        if self.include_over_station_length_long and train.length > self.station_length_long:
            return False

        if self.include_over_recommended_weight_full and train.is_over_recommended_weight_full():
            return False

        if self.include_over_recommended_weight_empty and train.is_over_recommended_weight_empty():
            return False

        return True
