import sqlalchemy.orm

from .base import Base
from .config import CargoType, TokenType


class Vehicle(Base):
    __abstract__ = True

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon_color = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    epoch_min = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    epoch_max = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    track = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    weight_empty = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    weight_full = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    length = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class Engine(Vehicle):
    __tablename__ = "engine"

    fuel_cost = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    power = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    max_speed = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    max_speed_reverse = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    payments = sqlalchemy.orm.relationship("Payment", back_populates="engine")


class Wagon(Vehicle):
    __tablename__ = "wagon"

    cargo_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("cargo_type.id"))
    cargo = sqlalchemy.orm.relationship(CargoType)


class RoadVehicle(Vehicle):
    __tablename__ = "road_vehicle"

    cargo_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("cargo_type.id"))
    cargo = sqlalchemy.orm.relationship(CargoType)


class Payment(Base):
    __tablename__ = "trains_payment"
    __table_args__ = (sqlalchemy.PrimaryKeyConstraint("engine_id", "token_id"),)

    engine_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("engine.id"))
    engine = sqlalchemy.orm.relationship(Engine)

    token_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("token_type.id"))
    token = sqlalchemy.orm.relationship(TokenType)

    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
