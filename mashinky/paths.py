import os
import pathlib

module = pathlib.Path(__file__).parent
static = module.parent / "static"
assets = module.parent / "assets"
images = module.parent / "static"

database = assets / "models.sqlite3"
game_data = pathlib.Path(os.environ["MASHINKY_GAME_DATA"])
sqlalchemy_url = f"sqlite:///{database.absolute()}"
