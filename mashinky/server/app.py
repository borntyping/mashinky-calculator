from flask import Flask, render_template, request, url_for, redirect
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from jinja2 import StrictUndefined
from sqlalchemy import asc, nulls_last

from mashinky.models import (
    Base,
    CargoType,
    Color,
    Engine,
    Epoch,
    RoadVehicle,
    TokenType,
    Wagon,
    WagonType,
)
from mashinky.paths import sqlalchemy_database_url, static_folder
from mashinky.trains import combinations

app = Flask(import_name=__name__, static_folder=static_folder)
app.jinja_env.undefined = StrictUndefined
app.config["SECRET_KEY"] = "50e80816-1736-404b-880d-16e35c6c6ef4"
app.config["SQLALCHEMY_DATABASE_URI"] = sqlalchemy_database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

db = SQLAlchemy(app=app, model_class=Base)
toolbar = DebugToolbarExtension(app=app)


@app.context_processor
def variables():
    return {
        "undefined": "—",
        "tile_width": 100,
    }


@app.route("/")
def home():
    return render_template("home.html.j2")


@app.route("/trains")
def trains():
    epoch = Epoch(request.args.get("epoch", default=1, type=int))
    station_length: int = request.args.get("station_length", default=6, type=int)

    path = url_for("trains", epoch=epoch.value, station_length=station_length, _external=False)
    if path != request.full_path:
        return redirect(path)

    engines = (
        Engine.query.order_by(Engine.id)
        .filter(WagonType.epoch_start <= epoch, epoch <= WagonType.epoch_end)
        .all()
    )
    wagons = (
        Wagon.query.order_by(Wagon.id)
        .filter(WagonType.epoch_start <= epoch, epoch <= WagonType.epoch_end)
        .all()
    )

    combos = list(combinations(engines, wagons, station_length=station_length))
    combos = sorted(combos, key=lambda train: train.capacity, reverse=True)

    return render_template("trains.html.j2", trains=combos)


@app.route("/wagon_types")
def wagon_types():
    results = WagonType.query.order_by(WagonType.id).all()
    return render_template(
        "wagon_types.j2",
        wagon_types=results,
        engines=[v for v in results if isinstance(v, Engine)],
        wagons=[v for v in results if isinstance(v, Wagon)],
        road_vehicles=[v for v in results if isinstance(v, RoadVehicle)],
    )


@app.route("/cargo_types")
def cargo_types():
    return render_template(
        "cargo_types.html.j2",
        cargo_types=CargoType.query.order_by(nulls_last(CargoType.name), asc(CargoType.name)).all(),
    )


@app.route("/token_types")
def token_types():
    return render_template(
        "token_types.html.j2",
        token_types=TokenType.query.order_by(nulls_last(TokenType.name), asc(TokenType.name)).all(),
    )


@app.route("/colors")
def colors():
    return render_template("colors.html.j2", colors=Color.query.all())
