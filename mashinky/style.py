import dataclasses
import operator
import typing

import mashinky.palette
import mashinky.types

TOKEN = "●"


def style_limit(lim: mashinky.types.Limit) -> str:
    if lim is mashinky.types.Limit.WEIGHT:
        return mashinky.palette.good(lim.value)
    else:
        return mashinky.palette.neutral(lim.value)


def payment(p: mashinky.types.Payment) -> str:
    if p.token.value == mashinky.types.Token.MONEY.value:
        symbol = mashinky.palette.money(TOKEN)
    elif p.token.value == mashinky.types.Token.TIMBER.value:
        symbol = mashinky.palette.timber(TOKEN)
    elif p.token.value == mashinky.types.Token.COAL.value:
        symbol = mashinky.palette.coal(TOKEN)
    elif p.token.value == mashinky.types.Token.IRON.value:
        symbol = mashinky.palette.iron(TOKEN)
    elif p.token.value == mashinky.types.Token.DIESEL.value:
        symbol = mashinky.palette.diesel(TOKEN)
    elif p.token.value == mashinky.types.Token.STEEL.value:
        symbol = mashinky.palette.steel(TOKEN)
    elif p.token.value == mashinky.types.Token.ELECTRIC.value:
        symbol = mashinky.palette.electric(TOKEN)
    else:
        raise NotImplementedError(f"Unknown token type {p.token!r}")

    return f"{symbol} {p.amount} {p.token}"


def payments(cost: typing.Iterable[mashinky.types.Payment], multiplier: int) -> str:
    return ", ".join([payment(p * multiplier) for p in cost])


def engine_cost(train: mashinky.types.Train) -> str:
    if train.engine.quest_reward:
        return f"{mashinky.palette.quest(TOKEN)} quest reward"

    return payments(train.engine.cost, train.engine_count)


def wagon_cost(train: mashinky.types.Train) -> str:
    return payments(train.wagon.cost, train.wagon_count)


def operating_cost(train: mashinky.types.Train) -> str:
    return payments(train.engine.operating_cost, train.engine_count)


def length(value: float, station_length: float) -> str:
    if value >= station_length - 1.0:
        return mashinky.palette.good(str(value))
    elif value >= station_length - 2.0:
        return mashinky.palette.neutral(str(value))

    return mashinky.palette.bad(str(value))


@dataclasses.dataclass(frozen=True)
class Comparison:
    values: typing.Sequence[float]
    format: str = "{}"

    def max(self) -> float:
        return max(self.values)

    def style(self, value: float) -> str:
        best = self.max()
        string = self.format.format(value)

        if value >= best:
            return mashinky.palette.color(string, "green", 500)
        elif value >= best * 0.9:
            return mashinky.palette.color(string, "green", 600)
        elif value >= best * 0.8:
            return mashinky.palette.color(string, "green", 700)
        elif value >= best * 0.7:
            return mashinky.palette.color(string, "green", 800)
        elif value >= best * 0.6:
            return mashinky.palette.color(string, "green", 900)
        elif value >= best * 0.5:
            return mashinky.palette.color(string, "red", 900)
        elif value >= best * 0.4:
            return mashinky.palette.color(string, "red", 800)
        elif value >= best * 0.3:
            return mashinky.palette.color(string, "red", 700)
        elif value >= best * 0.2:
            return mashinky.palette.color(string, "red", 600)
        elif value >= best * 0.1:
            return mashinky.palette.color(string, "red", 500)
        else:
            return mashinky.palette.color(string, "red", 400)


def compare(trains: typing.Sequence[mashinky.types.Train], attribute: str) -> Comparison:
    getter = operator.attrgetter(attribute)
    return Comparison(list(sorted(getter(train) for train in trains)))
