from __future__ import annotations

import enum
import typing

from sqlalchemy.orm import relationship, declarative_base, declared_attr
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, PrimaryKeyConstraint

Base = declarative_base()


class CargoType(Base):
    __tablename__ = "cargo_type"

    id = Column(String, primary_key=True)
    icon = Column(String, nullable=False)
    name = Column(String)


class TokenType(Base):
    __tablename__ = "token_type"

    id = Column(String, primary_key=True)
    icon = Column(String, nullable=False)
    name = Column(String)


class Color(Base):
    __tablename__ = "color"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    red = Column(Integer, nullable=False)
    green = Column(Integer, nullable=False)
    blue = Column(Integer, nullable=False)


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

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    icon_color = Column(String, nullable=False)

    epoch = Column(Enum(Epoch), nullable=True)
    epoch_end = Column(Enum(Epoch), nullable=True)

    track = Column(Enum(Track), nullable=False)
    weight_empty = Column(Integer, nullable=False)
    weight_full = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)

    cost: typing.Sequence[Cost] = relationship("Cost", uselist=True, lazy="joined")
    sell: typing.Sequence[Sell] = relationship("Sell", uselist=True, lazy="joined")
    fuel: typing.Sequence[Fuel] = relationship("Fuel", uselist=True, lazy="joined")

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

    id = Column(
        String,
        ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    power = Column(Integer, nullable=False)
    max_speed = Column(Integer, nullable=False)
    max_speed_reverse = Column(Integer, nullable=True)


class Wagon(WagonType):
    __tablename__ = "wagon"
    __mapper_args__ = {
        "polymorphic_identity": "wagon",
        "polymorphic_load": "inline",
    }

    id = Column(
        String,
        ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    cargo_id = Column(
        String,
        ForeignKey("cargo_type.id"),
        nullable=False,
    )
    cargo = relationship(CargoType)

    capacity = Column(Integer, nullable=False)


class RoadVehicle(WagonType):
    __tablename__ = "road_vehicle"
    __mapper_args__ = {
        "polymorphic_identity": "road_vehicle",
        "polymorphic_load": "inline",
    }

    id = Column(
        String,
        ForeignKey("wagon_type.id"),
        primary_key=True,
    )

    cargo_id = Column(
        String,
        ForeignKey("cargo_type.id"),
        nullable=False,
    )
    cargo = relationship(CargoType)

    capacity = Column(Integer, nullable=False)


class Payment(Base):
    __abstract__ = True
    __table_args__ = (PrimaryKeyConstraint("wagon_type_id", "token_type_id"),)

    @declared_attr
    def wagon_type_id(self):
        return Column(
            String,
            ForeignKey("wagon_type.id"),
            nullable=False,
        )

    @declared_attr
    def token_type_id(self):
        return Column(
            String,
            ForeignKey("token_type.id"),
            nullable=False,
        )

    amount = Column(Integer, nullable=False)


class Cost(Payment):
    __tablename__ = "cost"

    vehicle = relationship(WagonType, back_populates="cost")
    token_type = relationship(TokenType)


class Sell(Payment):
    __tablename__ = "sell"

    vehicle = relationship(WagonType, back_populates="sell")
    token_type = relationship(TokenType)


class Fuel(Payment):
    __tablename__ = "fuel"

    vehicle = relationship(WagonType, back_populates="fuel")
    token_type = relationship(TokenType)
