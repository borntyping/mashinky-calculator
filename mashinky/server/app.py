import flask
import flask_sqlalchemy
import sqlalchemy
from sqlalchemy import asc, nulls_last

import mashinky.models
import mashinky.paths

app = flask.Flask(__name__, static_folder=mashinky.paths.static)
app.config["SQLALCHEMY_DATABASE_URI"] = mashinky.paths.sqlalchemy_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = flask_sqlalchemy.SQLAlchemy(app=app, model_class=mashinky.models.Base)


@app.route("/")
def home():
    return flask.render_template("home.html.j2")


@app.route("/data")
def data():
    cargo_types = mashinky.models.CargoType.query.order_by(
        nulls_last(mashinky.models.CargoType.name),
        asc(mashinky.models.CargoType.name),
    ).all()
    token_types = mashinky.models.TokenType.query.all()
    colors = mashinky.models.Color.query.all()
    wagon_types = mashinky.models.WagonType.query.all()

    return flask.render_template(
        "data.html.j2",
        cargo_types=cargo_types,
        token_types=token_types,
        colors=colors,
        wagon_types=wagon_types,
    )


@app.add_template_global
def undefined() -> str:
    return "—"
