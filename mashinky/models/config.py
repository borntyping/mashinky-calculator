import sqlalchemy.orm

from .base import Base


class CargoType(Base):
    __tablename__ = "cargo_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String)


class TokenType(Base):
    __tablename__ = "token_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String)


class Color(Base):
    __tablename__ = "color"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    red = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    green = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    blue = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class WagonType(Base):
    __tablename__ = "wagon_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon_color = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    epoch = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    level = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    track = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    weight_empty = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    weight_full = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    length = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    cost = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    sell = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Engines
    fuel_cost = sqlalchemy.Column(sqlalchemy.String)
    power = sqlalchemy.Column(sqlalchemy.String)
    max_speed = sqlalchemy.Column(sqlalchemy.String)
    max_speed_reverse = sqlalchemy.Column(sqlalchemy.String)

    depo_upgrade = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Wagons + Road vehicles
    cargo_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("cargo_type.id"))
    cargo = sqlalchemy.orm.relationship(CargoType)
    capacity = sqlalchemy.Column(sqlalchemy.String)
