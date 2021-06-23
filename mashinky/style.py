import dataclasses
import typing

import click

from mashinky.types import Era, Train, Payment, Token, Limit
from mashinky.state import State


NUMERALS = {
    Era.EARLY_STEAM: "Ⅰ",
    Era.STEAM: "Ⅱ",
    Era.EARLY_DIESEL: "Ⅲ",
    Era.DIESEL: "Ⅳ",
    Era.EARLY_ELECTRIC: "Ⅴ",
}


def era(era: Era) -> str:
    return NUMERALS[era]


def engine_name(train: Train) -> str:
    return click.style(train.engine.name, fg="red")


def wagon_name(train: Train) -> str:
    return click.style(f"{train.wagon.name:<17}", fg="blue")


def count(n: int) -> typing.Optional[int]:
    return n if n > 1 else None


def usage(usage: float, min_usage: float, max_usage: float) -> str:
    return compare(
        round(usage * 100),
        round(min_usage * 100),
        round(max_usage * 100),
        "{:>5}%",
    )


def limit(l: Limit) -> str:
    return click.style(l.value, fg="bright_black" if l is Limit.WEIGHT else "white")


def payment(payment: Payment) -> str:
    token = "●"
    if payment.token is Token.MONEY:
        symbol = click.style(token, fg="green")
    elif payment.token is Token.TIMBER:
        symbol = click.style(token, fg="bright_yellow")
    elif payment.token is Token.COAL:
        symbol = click.style(token, fg="black")
    elif payment.token is Token.IRON:
        symbol = click.style(token, fg="bright_black")
    elif payment.token is Token.DIESEL:
        symbol = click.style(token, fg="magenta")
    elif payment.token is Token.STEEL:
        symbol = click.style(token, fg="bright_white")
    elif payment.token is Token.ELECTRIC:
        symbol = click.style(token, fg="yellow")

    return f"{symbol} {payment.amount} {payment.token}".ljust(13)


def payments(cost: typing.Iterable[Payment], multiplier: int) -> str:
    return ", ".join([payment(p * multiplier) for p in cost])


def engine_cost(train: Train) -> str:
    if train.engine.quest_reward:
        symbol = click.style("○", fg="yellow")
        return f"{symbol} quest reward"

    return payments(train.engine.cost, train.engine_count)


def wagon_cost(train: Train) -> str:
    return payments(train.wagon.cost, train.wagon_count)


def operating_cost(train: Train) -> str:
    return payments(train.engine.operating_cost, train.engine_count)


def compare(value: float, lo: float, hi: float, format: str = "{}") -> str:
    if value >= hi:
        fg = "green"
    elif value <= lo:
        fg = "red"
    else:
        fg = "reset"

    return click.style(format.format(value), fg=fg)


def length(value: float, station_length: float) -> str:
    return compare(
        value,
        lo=station_length / 2.0,
        hi=station_length - 1.0,
    )


def state_era(state: State) -> str:
    formatted_era = click.style(str(state.era), fg="green")
    return f"Using engines and wagons up to the {formatted_era} era."


def state_station_length(state: State) -> str:
    formatted_station_length = click.style(str(state.station_length), fg="blue")
    return f"Using stations {formatted_station_length} tiles long."


def state_unlocks(state: State) -> str:
    depot_extension = _unlock(
        description="engines and wagons from the depot extension",
        toggle=state.depot_extension,
    )
    quest_rewards = _unlock(
        description="engines from quest rewards",
        toggle=state.quest_rewards,
    )
    return "\n".join((depot_extension, quest_rewards))


def _unlock(description: str, toggle: bool) -> str:
    prefix = "Showing" if toggle else "Not showing"
    colour = "green" if toggle else "red"
    return click.style(f"{prefix} {description}.", fg=colour)
