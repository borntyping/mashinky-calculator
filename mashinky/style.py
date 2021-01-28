import typing

import click

from .types import Train, Payment, Token, Limit


def engine_name(train: Train) -> str:
    name = click.style(train.engine.name, fg="red")

    if train.engine_count > 1:
        name += f" (x{train.engine_count})"

    return name


def wagon_name(train: Train) -> str:
    name = click.style(f"{train.wagon.name:<10}", fg="red")

    if train.wagon_count > 1:
        name += f" (x{train.wagon_count})"

    return name


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
    amount = f"{payment.amount} {payment.token}".ljust(13)

    if payment.token is Token.MONEY:
        return click.style(amount, fg="black", bg="green")
    elif payment.token is Token.TIMBER:
        return click.style(amount, fg="black", bg="bright_white")
    elif payment.token is Token.COAL:
        return click.style(amount, fg="white", bg="black")
    elif payment.token is Token.IRON:
        return click.style(amount, fg="black", bg="bright_black")
    elif payment.token is Token.DIESEL:
        return click.style(amount, fg="black", bg="magenta")
    elif payment.token is Token.STEEL:
        return click.style(amount, fg="black", bg="white")
    elif payment.token is Token.ELECTRIC:
        return click.style(amount, fg="black", bg="yellow")

    raise NotImplementedError


def payments(cost: typing.Sequence[Payment]) -> str:
    return "".join([payment(p) for p in cost])


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
