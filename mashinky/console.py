import typing

import rich.progress


def track(sequence: typing.Iterable, description: str, plural: str):
    progress = rich.progress.Progress(
        rich.progress.TextColumn("[progress.description]{task.description:40}"),
        rich.progress.BarColumn(),
        rich.progress.TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        rich.progress.TimeElapsedColumn(),
        rich.progress.TextColumn("[progress.remaining]{task.completed:} %s" % plural),
    )

    with progress:
        yield from progress.track(sequence, description=description)
