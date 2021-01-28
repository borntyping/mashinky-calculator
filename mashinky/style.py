import click

from .types import Train


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
