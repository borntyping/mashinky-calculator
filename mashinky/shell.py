import dataclasses
import itertools
import typing
import operator

import click
import click_shell
import tabulate

from .types import Era, Material, Engine, Wagon, Train, Payment, Limit
from .engines import ENGINES
from .wagons import WAGONS
import mashinky.style


tabulate.MIN_PADDING = 0


def display(
    headers: typing.Sequence[str],
    table: typing.Sequence[typing.Sequence],
) -> None:
    print(tabulate.tabulate(table, headers, floatfmt=".2f", tablefmt="simple"))


@dataclasses.dataclass()
class State:
    era: Era
    depot_extension: bool
    station_length: int


@click_shell.shell(prompt="> ")
@click.option("-e", "--era", "era_name", default="early steam", type=click.STRING)
@click.option("-d", "--depot", "depot_extension", default=True, is_flag=True)
@click.option("-s", "--station", "station_length", default=6, type=click.IntRange(1, 8))
@click.pass_context
def main(
    ctx: click.Context,
    era_name: str,
    depot_extension: bool,
    station_length: int,
) -> None:
    ctx.obj = State(
        era=Era.named(era_name),
        depot_extension=depot_extension,
        station_length=station_length,
    )


@main.command()
@click.argument("era_name", type=click.STRING)
@click.pass_obj
def unlock(state: State, era_name: str) -> None:
    state.era = Era.named(era_name)

    value = click.style(state.era.numeral, fg="red")
    click.echo(f"Using engines and wagons up to the {value} era")


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
            for engine in ENGINES
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
            for wagon in WAGONS
        ],
    )


@main.command()
@click.argument("material_name", type=click.STRING)
@click.pass_obj
def transport(state: State, material_name: str):
    material = Material(material_name.capitalize())
    engines = [
        engine
        for engine in ENGINES
        if engine.era <= state.era and engine.quest_reward is False
    ]
    wagons = [
        wagon for wagon in WAGONS if wagon.era <= state.era and wagon.cargo == material
    ]

    trains = [
        Train.build(
            engine=engine,
            wagon=wagon,
            station_length=state.station_length,
            engine_count=engine_count,
        )
        for engine, wagon in itertools.product(engines, wagons)
        for engine_count in (1, 2)
    ]

    # This filters out trains made entirely from dining cars.
    trains = [train for train in trains if train.capacity != 0]

    trains = sorted(trains, key=operator.attrgetter("capacity"))

    print(
        tabulate.tabulate(
            [
                (
                    # Engine
                    train.engine.era.numeral,
                    mashinky.style.engine_name(train),
                    # Wagon
                    train.wagon.era.numeral,
                    mashinky.style.wagon_name(train),
                    train.wagon.cargo,
                    # Train
                    train.capacity,
                    train.format_usage(),
                    train.length,
                    train.wagon_limit,
                    Payment.payments(train.engine.cost),
                    Payment.payments(train.wagon.cost),
                    Payment.payments(train.engine.operating_cost),
                )
                for train in trains
            ],
            headers=[
                # Engine
                click.style("Era", fg="red"),
                click.style("Engine", fg="red"),
                # Wagon
                click.style("Era", fg="blue"),
                click.style("Wagon", fg="blue"),
                click.style("Cargo", fg="blue"),
                # Train
                click.style("Total", fg="magenta"),
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
