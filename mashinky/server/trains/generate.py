from __future__ import annotations

import collections
import dataclasses
import itertools
import json
import logging
import math
import typing

from mashinky.models import CargoType, Engine, Wagon
from mashinky.server.trains.suggestions import WAGON_SUGGESTIONS
from mashinky.server.trains.models import Train
from mashinky.server.trains.options import Options


@dataclasses.dataclass(frozen=True)
class Results:
    options: Options

    all_engines: typing.Sequence[Engine]
    all_wagons: typing.Sequence[Wagon]
    all_cargos: typing.Sequence[CargoType]

    selected_engines: typing.Sequence[Engine]
    selected_wagons: typing.Sequence[Wagon]
    selected_cargos: typing.Sequence[CargoType]

    filtered_wagons: typing.Sequence[Wagon]

    suggestions: dict[Wagon, list[list[Wagon]]]

    trains: list[Train]

    after_generate: list[Train]
    after_deduplicate: list[Train]
    after_filter: list[Train]
    after_discard_empty: list[Train]
    after_discard_extra: list[Train]
    after_sort: list[Train]

    best_capacity: int
    best_bonus_capacity: int
    best_max_speed: int
    best_weight_usage: float
    best_length_usage: float

    any_train_has_bonus: bool

    def all_engines_are_selected(self):
        return self.all_engines == self.selected_engines

    def all_wagons_are_selected(self):
        return self.all_wagons == self.selected_wagons

    def all_cargos_are_selected(self):
        return self.all_cargos == self.selected_cargos


def generate(
    options: Options,
    engine_ids: list[str],
    wagon_ids: list[str],
    cargo_ids: list[str],
) -> Results:
    all_engines = Engine.search(
        epoch=options.epoch,
        depo_upgrade=options.include_depo_upgrade,
        quest_reward=options.include_quest_reward,
    ).all()
    all_wagons = Wagon.search(
        epoch=options.epoch,
        depo_upgrade=options.include_depo_upgrade,
        quest_reward=options.include_quest_reward,
    ).all()
    all_cargos = CargoType.search(
        epoch=options.epoch,
    ).all()

    selected_engines = Engine.search(
        epoch=options.epoch,
        ids=engine_ids,
        depo_upgrade=options.include_depo_upgrade,
        quest_reward=options.include_quest_reward,
    ).all()
    selected_wagons = Wagon.search(
        epoch=options.epoch,
        ids=wagon_ids,
        depo_upgrade=options.include_depo_upgrade,
        quest_reward=options.include_quest_reward,
    ).all()
    selected_cargos = CargoType.search(
        epoch=options.epoch,
        ids=cargo_ids,
    ).all()

    # Filter wagons to only those that carry the cargos we care about.
    filtered_wagons = generate_wagons(
        selected_wagons=selected_wagons or all_wagons,
        selected_cargos=selected_cargos or all_cargos,
    )

    suggestions = generate_suggestions(
        all_wagons=all_wagons,
        selected_wagons=filtered_wagons or selected_wagons or all_wagons,
    )

    trains = after_generate = list(
        generate_trains(
            selected_engines=selected_engines or all_engines,
            selected_wagons=filtered_wagons or selected_wagons or all_wagons,
            suggestions=suggestions,
            station_length_short=options.station_length_short,
            station_length_long=options.station_length_long,
            maximum_engines=options.maximum_engines,
        )
    )
    trains = after_deduplicate = list(generate_deduplicate(trains))
    trains = after_filter = list(generate_filter(trains, options))
    trains = after_discard_empty = list(generate_discard_empty(trains))
    trains = after_discard_extra = list(generate_discard_extra(trains))
    trains = after_sort = list(generate_sort(trains))

    weight_usage = (t.weight_usage() for t in trains)
    length_usage = (t.length_usage(options.station_length) for t in trains)

    best_capacity = max(t.capacity for t in trains) if trains else None
    best_bonus_capacity = max(t.bonus_capacity for t in trains) if trains else None
    best_max_speed = max(t.max_speed for t in trains) if trains else None
    best_weight_usage = max(weight for weight in weight_usage if weight <= 1.00) if trains else None
    best_length_usage = max(length for length in length_usage if length <= 1.00) if trains else None

    any_train_has_bonus = any(train.has_bonus for train in trains)

    return Results(
        options=options,
        all_engines=all_engines,
        all_wagons=all_wagons,
        all_cargos=all_cargos,
        selected_engines=selected_engines,
        selected_wagons=selected_wagons,
        selected_cargos=selected_cargos,
        filtered_wagons=filtered_wagons,
        suggestions=suggestions,
        trains=trains,
        after_generate=after_generate,
        after_deduplicate=after_deduplicate,
        after_discard_empty=after_discard_empty,
        after_discard_extra=after_discard_extra,
        after_filter=after_filter,
        after_sort=after_sort,
        best_capacity=best_capacity,
        best_bonus_capacity=best_bonus_capacity,
        best_max_speed=best_max_speed,
        best_weight_usage=best_weight_usage,
        best_length_usage=best_length_usage,
        any_train_has_bonus=any_train_has_bonus,
    )


def generate_suggestions(
    all_wagons: list[Wagon],
    selected_wagons: list[Wagon],
) -> dict[Wagon, list[list[Wagon]]]:
    all_wagons_by_name = {wagon.name: wagon for wagon in all_wagons}
    return {
        all_wagons_by_name[name]: [
            [all_wagons_by_name[n] for n in suggestion]
            for suggestion in suggestions
            if all(n in all_wagons_by_name for n in suggestion)
        ]
        for name, suggestions in WAGON_SUGGESTIONS.items()
        if name in all_wagons_by_name and all_wagons_by_name[name] in selected_wagons
    }


def generate_wagons(
    selected_wagons: typing.Sequence[Wagon],
    selected_cargos: typing.Sequence[CargoType],
) -> typing.Sequence[Wagon]:
    return [w for w in selected_wagons if w.cargo_type in selected_cargos]


def generate_trains(
    selected_engines: typing.Sequence[Engine],
    selected_wagons: typing.Sequence[Wagon],
    suggestions: dict[Wagon, list[list[Wagon]]],
    station_length_short: int,
    station_length_long: int,
    maximum_engines: int = 2,
) -> typing.Iterable[Train]:
    for engine, wagon in itertools.product(selected_engines, selected_wagons):
        heads = [engine.times(n) for n in range(1, maximum_engines + 1)]
        tails = [()] + suggestions.get(wagon, [])

        for head, tail in itertools.product(heads, tails):
            train = Train((*head, *tail))

            yield train.add_wagons_to_recommended_weight(wagon)
            yield train.add_wagons_to_length(wagon, station_length_short)
            yield train.add_wagons_to_length(wagon, station_length_long)


def generate_discard_extra(trains: list[Train]) -> typing.Iterable[Train]:
    """Remove trains with unused extra engines."""

    similar = collections.defaultdict(list)

    for train in trains:
        similar[frozenset(train.wagon_types)].append(train)

    for train in trains:
        others = similar[frozenset(train.wagon_types)]

        # Discard trains that have more engines than a similar train but a lower capacity.
        if not any(
            train.engine_count > o.engine_count and train.capacity <= o.capacity for o in others
        ):
            yield train


def generate_discard_empty(trains: list[Train]) -> typing.Iterable[Train]:
    """Discard trains with a capacity of zero."""
    for train in trains:
        if train.capacity > 0:
            yield train


def generate_deduplicate(trains: list[Train]) -> typing.Iterable[Train]:
    """Deduplicate identical trains."""
    unique: dict[Train, typing.Literal[None]] = {}
    for train in trains:
        # This uses setdefault instead of []=, so the first train wins.
        unique.setdefault(train, None)
    return list(unique.keys())


def generate_filter(trains: list[Train], options) -> typing.Iterable[Train]:
    return filter(options.should_include, trains)


def generate_sort(trains: list[Train]) -> typing.Iterable[Train]:
    return sorted(trains, key=lambda t: t.bonus_capacity, reverse=True)
