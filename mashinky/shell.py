from __future__ import annotations

import itertools
import typing
import operator

import xdg
import tabulate
import pydantic
import pathlib
import click_shell
import click

from mashinky.types import (
    Era,
    Material,
    Engine,
    Wagon,
    Train,
    Token,
    Stock,
)
from mashinky.engines import ENGINES
from mashinky.wagons import WAGONS
import mashinky.style


tabulate.MIN_PADDING = 0  # type: ignore


S = typing.TypeVar("S", bound=Stock)


def display(
    headers: typing.Sequence[str],
    table: typing.Sequence[typing.Sequence],
) -> None:
    print(tabulate.tabulate(table, headers, floatfmt=".2f", tablefmt="simple"))


class State(pydantic.BaseModel):
    era: Era = Era.EARLY_STEAM
    depot_extension: bool = False
    station_length: int = 6

    def select(self, items: typing.Sequence[S]) -> typing.Sequence[S]:
        return [stock for stock in items if stock.era <= self.era]  # type: ignore

    def engines(self) -> typing.Sequence[Engine]:
        return self.select(ENGINES)

    def wagons(self) -> typing.Sequence[Wagon]:
        return self.select(WAGONS)

    @staticmethod
    def path() -> pathlib.Path:
        return xdg.xdg_config_home() / "mashinky.json"

    @classmethod
    def load(cls) -> State:
        if not cls.path().exists():
            return State()

        return cls.parse_file(cls.path())

    def save(self) -> None:
        self.path().write_text(self.json())


@click_shell.shell(prompt="> ")
@click.pass_context
def main(ctx: click.Context) -> None:
    ctx.obj = State.load()
    ctx.call_on_close(ctx.obj.save)


@main.command(
    help="\n".join(
        (
            "Set an era to use when calculating possible trains",
            "\n\b",
            *(f"- {era}" for era in Era),
        )
    )
)
@click.pass_context
def unlock(ctx: click.Context) -> None:
    ctx.obj.era = Era(
        click.prompt(
            "Current era?",
            type=click.Choice([e.value for e in Era], case_sensitive=False),
            default=ctx.obj.era.value,
        )
    )
    ctx.obj.depot_extension = click.prompt(
        "Depot extension?",
        type=bool,
        default=str(ctx.obj.depot_extension),
    )
    ctx.obj.station_length = click.prompt(
        "Station length",
        type=int,
        default=str(ctx.obj.station_length),
    )

    click.echo()

    era_name = click.style(ctx.obj.era.value, fg="green")
    click.echo(f"Using engines and wagons up to the {era_name} era.")

    if ctx.obj.depot_extension:
        depot = click.style("depot extension", fg="green")
        click.echo(f"Buying engines and wagons from the {depot}.")
    else:
        depot = click.style("basic depot", fg="red")
        click.echo(f"Buying engines and wagons from the {depot}.")

    n = click.style(str(ctx.obj.station_length), fg="blue")
    click.echo(f"Using stations {n} tiles long.")


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
    "-q",
    "--quest-rewards/--no-quest-rewards",
    "quest_rewards",
    is_flag=True,
    default=False,
    help="Include engines from quest rewards.",
)
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
    quest_rewards: bool,
    best: bool,
    cheap: bool,
):
    engines = state.engines()
    wagons = state.wagons()

    # engines = [engine for engine in ENGINES if engine.name == "074 Bangle"]
    # wagons = [wagon for wagon in WAGONS if wagon.name == "Nossinger"]

    if not quest_rewards:
        engines = [engine for engine in engines if not engine.quest_reward]

    # Filter wagons based on the selected material.
    # Shows all combinations if no material is selected.
    if material_name is not None:
        material = Material(material_name.title())
        wagons = [wagon for wagon in wagons if wagon.cargo == material]

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

    max_capacity = max(train.capacity for train in trains)
    max_speed = max(train.engine.speed for train in trains)

    if best:
        trains = [train for train in trains if train.capacity == max_capacity]

    if cheap:
        trains = [t for t in trains if t.engine.operating_cost_tokens == {Token.MONEY}]

    print(
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
