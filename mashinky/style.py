import typing

import click

from .types import Train, Payment, Token, Limit


def engine_name(train: Train) -> str:
    return click.style(train.engine.name, fg="red")


def wagon_name(train: Train) -> str:
    return click.style(f"{train.wagon.name:<17}", fg="blue")


def count(n: int) -> typing.Optional[int]:
    return n if n > 1 else None


def usage(train: Train) -> str:
    loaded_usage = train.loaded_usage()
    if loaded_usage >= 0.75:
        return click.style(str(loaded_usage), fg="green")
    if loaded_usage >= 0.50:
        return click.style(str(loaded_usage), fg="yellow")
    return click.style(str(loaded_usage), fg="red")


def limit(l: Limit) -> str:
    return click.style(l.value, fg="bright_black" if l is Limit.WEIGHT else "white")


def payment(payment: Payment) -> str:
    symbol = "⦿ "
    symbol = "●"
    if payment.token is Token.MONEY:
        symbol = click.style(symbol, fg="green")
    elif payment.token is Token.TIMBER:
        symbol = click.style(symbol, fg="bright_yellow")
    elif payment.token is Token.COAL:
        symbol = click.style(symbol, fg="black")
    elif payment.token is Token.IRON:
        symbol = click.style(symbol, fg="bright_black")
    elif payment.token is Token.DIESEL:
        symbol = click.style(symbol, fg="magenta")
    elif payment.token is Token.STEEL:
        symbol = click.style(symbol, fg="bright_white")
    elif payment.token is Token.ELECTRIC:
        symbol = click.style(symbol, fg="yellow")

    return f"{symbol} {payment.amount} {payment.token}".ljust(13)


def payments(cost: typing.Sequence[Payment]) -> str:
    return ", ".join([payment(p) for p in cost])


def compare(value: int, max: int) -> str:
    if value == max:
        return click.style(str(value), fg="green")

    return str(value)


def length(value: float, station_length: float) -> str:
    if value >= station_length - 1.0:
        return click.style(str(value), fg="green")

    if value <= station_length / 2.0:
        return click.style(str(value), fg="red")

    return click.style(str(value), fg="yellow")
