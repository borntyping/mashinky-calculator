import pathlib

module_folder = pathlib.Path(__file__).parent
static_folder = module_folder.parent / "static"
assets_folder = module_folder.parent / "assets"

sqlalchemy_database_path = assets_folder / "models.sqlite3"
sqlalchemy_database_url = f"sqlite:///{sqlalchemy_database_path.absolute()}"
