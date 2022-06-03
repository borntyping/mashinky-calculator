from __future__ import annotations

import dataclasses
import enum
import typing

import flask

from mashinky.models import Epoch
from mashinky.server.trains.models import Train


class MaximumWeight(enum.Enum):
    FULL = "full"
    EMPTY = "empty"
    INFINITE = "infinite"


class MaximumLength(enum.Enum):
    SHORT = "short"
    LONG = "long"
    INFINITE = "infinite"


@dataclasses.dataclass(frozen=True)
class Options:
    epoch: Epoch

    include_depo_upgrade: bool
    include_quest_reward: bool
    maximum_engines: int = 2
    maximum_weight: MaximumWeight = MaximumWeight.FULL
    maximum_length: MaximumLength = MaximumLength.SHORT
    station_length_short: int = 6
    station_length_long: int = 8

    @property
    def station_length(self) -> int:
        if self.maximum_length == MaximumLength.SHORT:
            return self.station_length_short
        elif self.maximum_length == MaximumLength.LONG:
            return self.station_length_long
        elif self.maximum_length == MaximumLength.INFINITE:
            return self.station_length_long
        raise NotImplementedError(self.maximum_length)

    def should_include(self, train: Train) -> bool:
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

    def start_again_from_epoch(self) -> str:
        return flask.url_for("trains")

    def start_again_from_options(self) -> str:
        return flask.url_for("trains", epoch=self.epoch.value)

    def start_again_from_selection(self) -> str:
        return self.clear_selection(self.epoch)

    def switch_epoch(self, epoch: Epoch):
        return self.clear_selection(epoch)

    def clear_selection(self, epoch) -> str:
        kwargs = {}

        if self.include_depo_upgrade:
            kwargs["include_depo_upgrade"] = "true"

        if self.include_quest_reward:
            kwargs["include_quest_reward"] = "true"

        return flask.url_for(
            "trains",
            epoch=epoch.value,
            maximum_weight=self.maximum_weight.value,
            maximum_length=self.maximum_length.value,
            station_length_short=self.station_length_short,
            station_length_long=self.station_length_long,
            **kwargs,
        )
