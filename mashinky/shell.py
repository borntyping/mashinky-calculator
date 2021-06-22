from __future__ import annotations

import itertools
import typing
import operator

import tabulate
import click_shell
import click

from mashinky.types import Era, Material, Train, Token
from mashinky.engines import ENGINES
from mashinky.wagons import WAGONS
from mashinky.state import State
import mashinky.style


tabulate.MIN_PADDING = 0  # type: ignore


def display(
    headers: typing.Sequence[str],
    table: typing.Sequence[typing.Sequence],
) -> None:
    click.echo(tabulate.tabulate(table, headers, floatfmt=".2f", tablefmt="simple"))


@click_shell.shell(prompt="> ")
@click.pass_context
def main(ctx: click.Context) -> None:
    ctx.obj = State.load()
    ctx.call_on_close(ctx.obj.save)


class JoinedStringType(click.ParamType):
    def convert(self, value, param, ctx):
        raise Exception((value, param))


@main.command(no_args_is_help=True)
@click.argument("name", type=click.Choice([e.value for e in Era], case_sensitive=False))
@click.pass_obj
def era(state: State, name: typing.Sequence[str]) -> None:
    """Set an era to use when listing engines and wagons."""
    state.era = Era(name)
    click.echo(mashinky.style.state_era(state))


era.help += "\n\n\b"
for name in Era:
    era.help += f"\n- {name}"


def toggle(state: State, words: typing.Sequence[str], value: bool) -> None:
    for word in words:
        if word in {"quest", "rewards"}:
            state.quest_rewards = value
        elif word in {"depot", "extension"}:
            state.depot_extension = value
        else:
            raise NotImplementedError(f"Unknown word {word}")

    click.echo(mashinky.style.state_unlocks(state))


@main.command(no_args_is_help=True)
@click.argument("words", nargs=-1, type=click.STRING)
@click.pass_obj
def unlock(state: State, words: typing.Sequence[str]) -> None:
    """
    Unlock quest rewards or depot extensions.

    \b
    - "quest rewards"
    - "depot extension"
    """
    toggle(state, words, True)


@main.command(no_args_is_help=True)
@click.argument("words", nargs=-1, type=click.STRING)
@click.pass_obj
def lock(state: State, words: typing.Sequence[str]) -> None:
    """
    Lock quest rewards or depot extensions.

    \b
    - "quest rewards"
    - "depot extension"
    """
    toggle(state, words, False)


@main.command()
@click.argument("length", type=click.INT)
@click.pass_obj
def station(state: State, length: int) -> None:
    state.station_length = length
    click.echo(mashinky.style.state_station_length(state))


@main.command()
@click.pass_obj
def engines(state: State):
    display(
        headers=["Name", "Era", "Speed", "Capacity", "Power", "Weight", "Length"],
        table=[
            (
                engine.name,
                engine.era,
                engine.speed,
                engine.capacity,
                engine.power,
                engine.weight,
                engine.length,
            )
            for engine in state.engines()
        ],
    )


@main.command()
@click.pass_obj
def wagons(state: State):
    display(
        headers=[
            "Name",
            "Era",
            "Cargo",
            "Capacity",
            "Unloaded",
            "Loaded",
            "Length",
            "Special",
        ],
        table=[
            (
                wagon.name,
                wagon.era,
                wagon.cargo,
                wagon.capacity,
                f"{wagon.unloaded:02d} tons",
                f"{wagon.loaded:02d} tons",
                wagon.length,
                wagon.special,
            )
            for wagon in state.wagons()
        ],
    )


@main.command()
@click.option(
    "-b",
    "--best",
    "best",
    is_flag=True,
    default=False,
    help="Only show the best trains.",
)
@click.option(
    "-c",
    "--cheap",
    "cheap",
    is_flag=True,
    default=False,
    help="Only show trains that cost money to operate.",
)
@click.argument("material_name", default=None, required=False, type=click.STRING)
@click.pass_obj
def transport(
    state: State,
    material_name: typing.Optional[str],
    best: bool,
    cheap: bool,
):
    engines = state.engines()
    wagons = state.wagons()

    # Filter wagons based on the selected material.
    # Shows all combinations if no material is selected.
    if material_name is not None:
        material = Material(material_name.title())
        wagons = [wagon for wagon in wagons if wagon.cargo == material]

    # This filters out trains made entirely from dining cars.
    wagons = [wagon for wagon in wagons if wagon.capacity > 0]

    # Generate a list of possible trains. The combinations() method filters
    # double-header trains with a lower capacity than a single header train.
    combinations = Train.combinations(engines, wagons, state.station_length)
    trains = sorted(combinations, key=operator.attrgetter("capacity"))

    max_capacity = max(train.capacity for train in trains)
    max_speed = max(train.engine.speed for train in trains)

    if best:
        trains = [train for train in trains if train.capacity == max_capacity]

    if cheap:
        trains = [t for t in trains if t.engine.operating_cost_tokens == {Token.MONEY}]

    click.echo(
        tabulate.tabulate(
            [
                (
                    # Engine
                    mashinky.style.era(train.engine.era),
                    mashinky.style.engine_name(train),
                    mashinky.style.count(train.engine_count),
                    # Wagon
                    mashinky.style.era(train.wagon.era),
                    mashinky.style.wagon_name(train),
                    mashinky.style.count(train.wagon_count),
                    train.wagon.cargo,
                    # Train
                    mashinky.style.compare(train.capacity, max_capacity),
                    mashinky.style.usage(train),
                    mashinky.style.compare(train.engine.speed, max_speed),
                    mashinky.style.length(train.length, state.station_length),
                    mashinky.style.limit(train.wagon_limit),
                    mashinky.style.engine_cost(train),
                    mashinky.style.wagon_cost(train),
                    mashinky.style.operating_cost(train),
                )
                for train in trains
            ],
            headers=[
                # Engine
                click.style("#", fg="red"),
                click.style("Engine", fg="red"),
                click.style("#", fg="red"),
                # Wagon
                click.style("#", fg="blue"),
                click.style("Wagon", fg="blue"),
                click.style("#", fg="blue"),
                click.style("Cargo", fg="blue"),
                # Train
                click.style("Total", fg="magenta"),
                click.style("Speed", fg="magenta"),
                click.style("Usage", fg="magenta"),
                click.style("Length", fg="magenta"),
                click.style("Limit", fg="magenta"),
                click.style("Engine cost", fg="red"),
                click.style("Wagon cost", fg="blue"),
                click.style("Operating cost", fg="red"),
            ],
            floatfmt=".2f",
        )
    )
