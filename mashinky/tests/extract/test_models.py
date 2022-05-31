import typing

import pytest

from mashinky.models import Track, Cost
from mashinky.extract.models import parse_epoch, parse_track, parse_payments


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", (0, 0)),
        ("1-3", (1, 3)),
        ("1-4", (1, 4)),
        ("1-7", (1, 7)),
        ("2-4", (2, 4)),
        ("2-7", (2, 7)),
        ("3-5", (3, 5)),
        ("3-7", (3, 7)),
        ("4-6", (4, 6)),
        ("4-7", (4, 7)),
        ("5-7", (5, 7)),
        ("6-7", (6, 7)),
    ],
)
def test_parse_epoch(value: str, expected: tuple[int, int]) -> None:
    assert parse_epoch(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", Track.STANDARD),
        ("2", Track.ELECTRIC),
    ],
)
def test_parse_track(value: str, expected: Track) -> None:
    assert parse_track(value) == expected


@pytest.mark.parametrize(
    ("value", "result"),
    [
        ("0", []),
        (
            "-10",
            [
                Cost(amount=-10, token_type_id="F0000000"),
            ],
        ),
        (
            "-200;-20[F27DB683]",
            [
                Cost(amount=-200, token_type_id="F0000000"),
                Cost(amount=-20, token_type_id="F27DB683"),
            ],
        ),
    ],
)
def test_parse_cost(value: str, result: typing.Sequence[Cost]) -> None:
    for actual, expected in zip(parse_payments(value), result):
        assert actual.amount == expected.amount
        assert actual.token_type_id == expected.token_type_id
