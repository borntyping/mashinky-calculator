from __future__ import annotations

import dataclasses
import itertools
import math
import typing

from mashinky.models import Engine, Epoch, Payment, TokenType, Track, Wagon, CargoType, WagonType


@dataclasses.dataclass(frozen=True)
class Limit:
    name: typing.ClassVar[str]
    unit: typing.ClassVar[str]
    maximum: typing.Union[int, float]


@dataclasses.dataclass(frozen=True)
class LengthLimit(Limit):
    name = "length"
    unit = "tiles"
    maximum: float

    def __str__(self) -> str:
        return f"Length ({self.maximum:.2f} tiles)"


@dataclasses.dataclass(frozen=True)
class WeightLimit(Limit):
    name = "weight"
    unit = "tons"
    maximum: int

    def __str__(self) -> str:
        return f"Weight ({self.maximum} tons)"


@dataclasses.dataclass(frozen=True)
class Train:
    wagon_types: typing.Sequence[WagonType]
    limits: typing.Sequence[Limit] = ()

    def __iter__(self) -> typing.Iterator[WagonType]:
        return iter(self.wagon_types)

    @property
    def engines(self) -> typing.Sequence[Engine]:
        return [wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Engine)]

    @property
    def engine(self) -> Engine:
        if len(set(self.engines)) > 1:
            raise ValueError("Train has multiple types of engine")

        return self.engines[0]

    @property
    def wagons(self) -> typing.Sequence[Wagon]:
        return [wagon_type for wagon_type in self.wagon_types if isinstance(wagon_type, Wagon)]

    @property
    def wagon(self) -> Wagon:
        if len(set(self.wagons)) > 1:
            raise ValueError("Train has multiple types of wagon")

        return self.wagons[0]

    # WagonType properties

    @property
    def epoch(self) -> typing.Optional[Epoch]:
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
    def cargo_type(self) -> CargoType:
        if len(self.cargo_types) > 1:
            raise ValueError("Train has multiple cargo types")

        return self.cargo_types.pop()

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

    # def remaining_length(self, max_length: int) -> float:
    #     return max_length - self.length
    #
    # def remaining_weight(self) -> float:
    #     return self.recommended_weight - self.weight_full

    def add_wagons(self, wagon: Wagon, max_length: int) -> Train:
        length = LengthLimit(max_length)
        weight = WeightLimit(self.recommended_weight)

        length_max = max_length - self.length
        weight_max = self.recommended_weight - self.weight_full

        length_count = math.floor(length_max / wagon.length)
        weight_count = math.floor(weight_max / wagon.weight_full)

        if length_count < weight_count:
            count = length_count
            limits = (length,)
        elif length_count > weight_count:
            count = weight_count
            limits = (weight,)
        else:
            count = length_count
            limits = (length, weight)

        wagons = [wagon for _ in range(count)]
        return Train([*self, *wagons], limits=limits)


def combinations(
    engines: typing.Iterable[Engine],
    wagons: typing.Iterable[Wagon],
    *,
    station_length: int,
) -> typing.Iterable[Train]:
    """
    - Skips double-engine trains that use a unique engine.
    - Skips double-engine trains that have a lower capacity.
    """
    for engine, wagon in itertools.product(engines, wagons):
        single = Train([engine]).add_wagons(wagon, station_length)
        double = Train([engine, engine]).add_wagons(wagon, station_length)

        yield single

        if double.capacity > single.capacity and not engine.unique:
            yield double
