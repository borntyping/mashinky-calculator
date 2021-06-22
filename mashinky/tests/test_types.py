import mashinky.types


def test_era_ordering() -> None:
    assert mashinky.types.Era("early steam") < mashinky.types.Era("steam")
