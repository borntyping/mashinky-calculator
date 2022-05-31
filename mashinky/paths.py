import pathlib

module = pathlib.Path(__file__).parent
static = module.parent / "static"
assets = module.parent / "assets"

sqlalchemy_path = assets / "models.sqlite3"
sqlalchemy_url = f"sqlite:///{sqlalchemy_path.absolute()}"
