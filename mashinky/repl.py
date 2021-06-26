from __future__ import annotations

import dataclasses
import importlib
import inspect
import sys
import traceback
import typing


import prompt_toolkit
import prompt_toolkit.auto_suggest
import prompt_toolkit.completion
import prompt_toolkit.history
import prompt_toolkit.styles
import prompt_toolkit.validation
import prompt_toolkit.output

import mashinky.commands
import mashinky.palette
import mashinky.style
import mashinky.state


class Continue(Exception):
    pass


@dataclasses.dataclass()
class Application:
    state: mashinky.state.State

    def bottom_toolbar(self) -> typing.List[typing.Tuple[str, str]]:
        spacer = ("class:spacer", " | ")

        return [
            ("", " "),
            ("class:state-key", f"Era: "),
            ("class:state-value", str(self.state.era)),
            spacer,
            ("class:state-key", f"Station length: "),
            ("class:state-value", str(self.state.station_length)),
            spacer,
            ("class:state-key", f"Depot extension: "),
            ("class:state-value", str(self.state.depot_extension)),
            spacer,
            ("class:state-key", f"Quest rewards: "),
            ("class:state-value", str(self.state.quest_rewards)),
            ("", " "),
        ]

    @staticmethod
    def completions() -> typing.Mapping[str, typing.Any]:
        commands = inspect.getmembers(mashinky.commands.Commands, predicate=inspect.isfunction)
        return {name: getattr(method, "__completer__", {}) for name, method in commands}

    def prompt_session(self) -> prompt_toolkit.PromptSession:
        completions = self.completions()
        history = self.state.history_path()
        history.parent.mkdir(exist_ok=True, parents=True)
        return prompt_toolkit.PromptSession(
            style=prompt_toolkit.styles.Style.from_dict({}),
            history=prompt_toolkit.history.FileHistory(history.as_posix()),
            auto_suggest=prompt_toolkit.auto_suggest.AutoSuggestFromHistory(),
            completer=prompt_toolkit.completion.NestedCompleter.from_nested_dict(completions),
            bottom_toolbar=self.bottom_toolbar,
            color_depth=prompt_toolkit.output.ColorDepth.TRUE_COLOR,
        )

    def main(self, argv: typing.Sequence[str]) -> None:
        if argv:
            return self.command(sys.argv[1:])

        return self.repl()

    def repl(self) -> None:
        prompt_toolkit.shortcuts.clear()
        session = self.prompt_session()
        while True:
            try:
                text = session.prompt("> ", reserve_space_for_menu=0)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            try:
                words = [word.strip() for word in text.split()]
            except Continue:
                continue

            if not words:
                continue

            try:
                self.command(words)
            except Exception:
                traceback.print_exc()
                continue

    def command(self, argv: typing.Sequence[str]) -> None:
        for name, module in inspect.getmembers(mashinky, inspect.ismodule):
            importlib.reload(module)

        commands = mashinky.commands.Commands(self.state)
        command, *arguments = argv

        if method := getattr(commands, command):
            method(*arguments)
            return

        raise NotImplementedError(f"Unknown command {command!r}")


def main() -> None:
    with mashinky.state.State.load() as state:
        app = Application(state)
        app.main(sys.argv[1:])
