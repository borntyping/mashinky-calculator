from __future__ import annotations

import collections
import dataclasses
import math
import typing

from mashinky.models import Amount, CargoType, Engine, Epoch, TokenType, Track, Wagon, WagonType


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

    @property
    def engine_count(self) -> int:
        return len(tuple(self.engines))

    def __repr__(self) -> str:
        return "Train[{}]".format(
            ", ".join(
                list(
                    "{} x{}".format(wagon_type, n)
                    for wagon_type, n in self.wagon_type_counter.items()
                )
            )
        )

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
    def has_bonus(self) -> bool:
        return any((wt.bonus_income for wt in self.wagon_types))

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

    def weight_usage(self) -> float:
        return self.weight_full / self.recommended_weight

    def length_usage(self, length: int) -> float:
        return self.length / length
