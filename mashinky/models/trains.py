from __future__ import annotations

import enum
import typing

import sqlalchemy.orm

from .base import Base
from .config import CargoType, TokenType


@enum.unique
class Track(enum.IntEnum):
    STANDARD = 0
    ELECTRIC = 2

    def __str__(self):
        names = {self.STANDARD: "Standard", self.ELECTRIC: "Electric"}
        return names[self]


@enum.unique
class Epoch(enum.IntEnum):
    EARLY_STEAM = 1
    STEAM = 2
    EARLY_DIESEL = 3
    DIESEL = 4
    EARLY_ELECTRIC = 5
    ELECTRIC = 6
    LATE_ELECTRIC = 7

    def __str__(self):
        names = {
            self.EARLY_STEAM: "Early steam",
            self.STEAM: "Steam",
            self.EARLY_DIESEL: "Early diesel",
            self.DIESEL: "Diesel",
            self.EARLY_ELECTRIC: "Early electric",
            self.ELECTRIC: "Electric",
            self.LATE_ELECTRIC: "Late electric",
        }

        return names[self]


class WagonType(Base):
    __tablename__ = "wagon_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon_color = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    epoch = sqlalchemy.Column(sqlalchemy.Enum(Epoch), nullable=True)
    epoch_end = sqlalchemy.Column(sqlalchemy.Enum(Epoch), nullable=True)

    track = sqlalchemy.Column(sqlalchemy.Enum(Track), nullable=False)
    weight_empty = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    weight_full = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    length = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    cost: typing.Sequence[Cost] = sqlalchemy.orm.relationship("Cost", uselist=True, lazy="joined")
    sell: typing.Sequence[Sell] = sqlalchemy.orm.relationship("Sell", uselist=True, lazy="joined")
    fuel: typing.Sequence[Fuel] = sqlalchemy.orm.relationship("Fuel", uselist=True, lazy="joined")

    __mapper_args__ = {
        "polymorphic_on": type,
    }

    @property
    def weight(self) -> str:
        if self.weight_empty == self.weight_full:
            return f"{self.weight_full}"
        else:
            return f"{self.weight_empty}&ndash;{self.weight_full}"

    @property
    def is_quest_reward(self) -> bool:
        return self.epoch is None


class Engine(WagonType):
    __tablename__ = "engine"
    __mapper_args__ = {
        "polymorphic_identity": "engine",
        "polymorphic_load": "inline",
    }

    id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    power = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    max_speed = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    max_speed_reverse = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)


class Wagon(WagonType):
    __tablename__ = "wagon"
    __mapper_args__ = {
        "polymorphic_identity": "wagon",
        "polymorphic_load": "inline",
    }

    id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    cargo_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("cargo_type.id"),
        nullable=False,
    )
    cargo = sqlalchemy.orm.relationship(CargoType)

    capacity = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class RoadVehicle(WagonType):
    __tablename__ = "road_vehicle"
    __mapper_args__ = {
        "polymorphic_identity": "road_vehicle",
        "polymorphic_load": "inline",
    }

    id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    cargo_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("cargo_type.id"),
        nullable=False,
    )
    cargo = sqlalchemy.orm.relationship(CargoType)

    capacity = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class Payment(Base):
    __abstract__ = True
    __table_args__ = (sqlalchemy.PrimaryKeyConstraint("wagon_type_id", "token_type_id"),)

    @sqlalchemy.orm.declared_attr
    def wagon_type_id(self):
        return sqlalchemy.Column(
            sqlalchemy.String,
            sqlalchemy.ForeignKey("wagon_type.id"),
            nullable=False,
        )

    @sqlalchemy.orm.declared_attr
    def token_type_id(self):
        return sqlalchemy.Column(
            sqlalchemy.String,
            sqlalchemy.ForeignKey("token_type.id"),
            nullable=False,
        )

    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class Cost(Payment):
    __tablename__ = "cost"

    vehicle = sqlalchemy.orm.relationship(WagonType, back_populates="cost")
    token_type = sqlalchemy.orm.relationship(TokenType)


class Sell(Payment):
    __tablename__ = "sell"

    vehicle = sqlalchemy.orm.relationship(WagonType, back_populates="sell")
    token_type = sqlalchemy.orm.relationship(TokenType)


class Fuel(Payment):
    __tablename__ = "fuel"

    vehicle = sqlalchemy.orm.relationship(WagonType, back_populates="fuel")
    token_type = sqlalchemy.orm.relationship(TokenType)
