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
    click.clear()
    click.echo(tabulate.tabulate(table, headers, floatfmt=".2f", tablefmt="simple"))


class State(pydantic.BaseModel):
    era: Era = pydantic.Field(default=Era.EARLY_STEAM)
    station_length: int = pydantic.Field(default=6, ge=1, le=8)
    depot_extension: bool = pydantic.Field(default=False)
    quest_rewards: bool = pydantic.Field(default=False)

    def select(self, items: typing.Sequence[S]) -> typing.Sequence[S]:
        depot_extension = {True, False} if self.depot_extension else {False}
        return [
            stock
            for stock in items
            if stock.era <= self.era
            and stock.requires_depot_extension in depot_extension
        ]

    def engines(self) -> typing.Sequence[Engine]:
        quest_rewards = {True, False} if self.quest_rewards else {False}
        return [
            engine
            for engine in self.select(ENGINES)
            if engine.quest_reward in quest_rewards
        ]

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
    ctx.obj.station_length = click.prompt(
        "Station length",
        type=click.IntRange(min=1, max=8),
        default=ctx.obj.station_length,
    )
    ctx.obj.depot_extension = click.prompt(
        "Depot extension?",
        type=bool,
        default=ctx.obj.depot_extension,
    )
    ctx.obj.quest_rewards = click.prompt(
        "Show engines from quest rewards?",
        type=bool,
        default=ctx.obj.quest_rewards,
    )

    click.echo()

    era_name = click.style(str(ctx.obj.era), fg="green")
    length = click.style(str(ctx.obj.station_length), fg="blue")
    click.echo(
        f"Using engines and wagons up to the {era_name} era "
        f"with stations {length} tiles long."
    )

    if ctx.obj.depot_extension:
        click.echo(f"Showing engines and wagons from the depot extension.")

    if ctx.obj.quest_rewards:
        click.echo("Showing engines from quest rewards.")


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

    click.clear()
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
