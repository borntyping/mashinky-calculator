import typing

from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from jinja2 import StrictUndefined
from sqlalchemy import asc

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
from mashinky.server.trains.generate import generate
from mashinky.server.trains.options import Options, MaximumLength, MaximumWeight

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
        "Epoch": Epoch,
    }


@app.route("/")
def home():
    return render_template("home.html.j2")


@app.route("/trains", endpoint="trains")
def search_trains():

    options = Options(
        epoch=Epoch(request.args.get("epoch", default=1, type=int)),
        include_depo_upgrade=request.args.get("include_depo_upgrade", default=False, type=bool),
        include_quest_reward=request.args.get("include_quest_reward", default=False, type=bool),
        maximum_length=MaximumLength(request.args.get("maximum_length", default="short", type=str)),
        maximum_weight=MaximumWeight(request.args.get("maximum_weight", default="full", type=str)),
        station_length_short=request.args.get("station_length_short", default=6, type=int),
        station_length_long=request.args.get("station_length_long", default=8, type=int),
    )

    results = generate(
        options,
        engine_ids=request.args.getlist("engine_id"),
        wagon_ids=request.args.getlist("wagon_id"),
        cargo_ids=request.args.getlist("cargo_type_id"),
    )
    return render_template("trains.html.j2", options=options, results=results)


@app.route("/wagon_types")
def wagon_types():
    results = WagonType.query.order_by(WagonType.id).all()
    return render_template(
        "wagon_types.html.j2",
        wagon_types=results,
        engines=[v for v in results if isinstance(v, Engine)],
        wagons=[v for v in results if isinstance(v, Wagon)],
        road_vehicles=[v for v in results if isinstance(v, RoadVehicle)],
    )


@app.route("/cargo_types")
def cargo_types():
    return render_template(
        "cargo_types.html.j2",
        cargo_types=CargoType.query.order_by(asc(CargoType.id)).all(),
    )


@app.route("/token_types")
def token_types():
    return render_template(
        "token_types.html.j2",
        token_types=TokenType.query.order_by(asc(TokenType.id)).all(),
    )


@app.route("/colors")
def colors():
    return render_template("colors.html.j2", colors=Color.query.all())
