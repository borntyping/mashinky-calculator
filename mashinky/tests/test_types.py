import mashinky.types


def test_era_ordering() -> None:
    assert mashinky.types.Era.EARLY_STEAM < mashinky.types.Era.STEAM


def test_era_equality() -> None:
    assert mashinky.types.Era.EARLY_STEAM == mashinky.types.Era.EARLY_STEAM


def test_material_equality() -> None:
    assert mashinky.types.Material.COAL == mashinky.types.Material.COAL
