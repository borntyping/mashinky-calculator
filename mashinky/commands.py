import dataclasses
import operator
import typing

import colors
import prompt_toolkit
import prompt_toolkit.completion
import prompt_toolkit.shortcuts
import prompt_toolkit.validation
import prompt_toolkit.output
import tabulate

import mashinky.style
import mashinky.palette
import mashinky.state
import mashinky.types

tabulate.MIN_PADDING = 0  # type: ignore

F = typing.TypeVar("F")


class NumberValidator(prompt_toolkit.validation.Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            for cursor_position, character in enumerate(text):
                if not character.isdigit():
                    raise prompt_toolkit.validation.ValidationError(
                        message="This input contains non-numeric characters",
                        cursor_position=cursor_position,
                    )


def display(
    headers: typing.Sequence[str],
    table: typing.Sequence[typing.Sequence],
) -> None:
    prompt_toolkit.shortcuts.clear()
    print(tabulate.tabulate(table, headers, floatfmt=".2f", tablefmt="simple"))


def completer(c: prompt_toolkit.completion.Completer) -> typing.Callable[[F], F]:
    def decorator(f: F) -> F:
        f.__completer__ = c
        return f

    return decorator


def word_completer(words: typing.Iterable[str]) -> typing.Callable[[F], F]:
    return completer(prompt_toolkit.completion.WordCompleter(list(words)))


def take(words: typing.Sequence[str], *take_words: str) -> typing.Tuple[typing.Sequence[str], bool]:
    return [word for word in words if word not in take_words], any(t in words for t in take_words)


@dataclasses.dataclass
class Commands:
    state: mashinky.state.State

    @word_completer(name for name in mashinky.types.Era.names)
    def era(self, *words: str) -> None:
        self.state.era = mashinky.types.Era.names[" ".join(word.casefold() for word in words)]
        print(f"Using engines and wagons up to the {self.state.era} era.")

    def station(self) -> None:
        station_length = prompt_toolkit.prompt("Station length: ", validator=NumberValidator())
        self.state.station_length = int(station_length)
        print(f"Using stations {self.state.station_length} tiles long.")

    def depot(self) -> None:
        self.state.depot_extension = not self.state.depot_extension
        prefix = "Showing" if self.state.depot_extension else "Not showing"
        print(f"{prefix} engines and wagons from the depot extension.")

    def quest(self) -> None:
        self.state.quest_rewards = not self.state.quest_rewards
        prefix = "Showing" if self.state.quest_rewards else "Not showing"
        print(f"{prefix} engines from quest rewards.")

    def engines(self) -> None:
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
                for engine in self.state.engines()
            ],
        )

    def wagons(self) -> None:
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
                for wagon in self.state.wagons()
            ],
        )

    @word_completer(material.value.lower() for material in mashinky.types.Material)
    def transport(self, *words: str) -> None:
        prompt_toolkit.shortcuts.clear()

        words, cheap = take(words, "cheap")
        words, best = take(words, "best")
        material = mashinky.types.Material(" ".join(words).title()) if words else None

        engines = self.state.engines()
        wagons = self.state.wagons()

        # Filter wagons based on the selected material.
        # Shows all combinations if no material is selected.
        if material is not None:
            wagons = [wagon for wagon in wagons if wagon.cargo.name == material.name]

        # This filters out trains made entirely from dining cars.
        wagons = [wagon for wagon in wagons if wagon.capacity > 0]

        # Generate a list of possible trains. The combinations() method filters
        # double-header trains with a lower capacity than a single header train.
        combinations = mashinky.types.Train.combinations(engines, wagons, self.state.station_length)
        trains = sorted(combinations, key=operator.attrgetter("capacity"))

        if cheap:
            trains = [
                train
                for train in trains
                if train.engine.operating_cost_tokens == {mashinky.types.Token.MONEY}
            ]

        capacity_comparison = mashinky.style.compare(trains, "capacity")
        speed_comparison = mashinky.style.compare(trains, "speed")
        usage_comparison = mashinky.style.compare(trains, "usage")

        if best:
            trains = [train for train in trains if train.capacity == capacity_comparison.max()]

        table = tabulate.tabulate(
            [
                (
                    # Engine
                    mashinky.palette.era(train.engine.era.index),
                    mashinky.palette.engine(train.engine.name),
                    train.multiple_engines,
                    # Wagon
                    mashinky.palette.era(train.wagon.era.index),
                    mashinky.palette.wagon(train.wagon.name),
                    train.multiple_wagons,
                    train.wagon.cargo,
                    # Train
                    capacity_comparison.style(train.capacity),
                    speed_comparison.style(train.speed),
                    usage_comparison.style(train.usage),
                    mashinky.style.length(train.length, self.state.station_length),
                    mashinky.style.style_limit(train.wagon_limit),
                    # Costs
                    mashinky.style.engine_cost(train),
                    mashinky.style.wagon_cost(train),
                    mashinky.style.operating_cost(train),
                )
                for train in trains
            ],
            headers=[
                # Engine
                mashinky.palette.engine("#"),
                mashinky.palette.engine("Engine"),
                mashinky.palette.engine("#"),
                # Wagon
                mashinky.palette.wagon("#"),
                mashinky.palette.wagon("Wagon"),
                mashinky.palette.wagon("#"),
                mashinky.palette.wagon("Cargo"),
                # Train
                mashinky.palette.train("Total"),
                mashinky.palette.train("Speed"),
                mashinky.palette.train("Usage"),
                mashinky.palette.train("Length"),
                mashinky.palette.train("Limit"),
                # Costs
                mashinky.palette.engine("Engine cost"),
                mashinky.palette.wagon("Wagon cost"),
                mashinky.palette.engine("Operating cost"),
            ],
            floatfmt=".2f",
        )

        prompt_toolkit.print_formatted_text(
            prompt_toolkit.ANSI(table),
            color_depth=prompt_toolkit.output.ColorDepth.TRUE_COLOR,
        )

    @staticmethod
    def clear() -> None:
        prompt_toolkit.shortcuts.clear()
