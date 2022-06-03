from __future__ import annotations

import enum
import math
import typing

import sqlalchemy.orm
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import declarative_base, relationship

from mashinky.ext.sqlalchemy import IntEnum

Base = declarative_base()

T = typing.TypeVar("T")


@enum.unique
class Epoch(enum.IntEnum):
    EARLY_STEAM = 1
    STEAM = 2
    EARLY_DIESEL = 3
    DIESEL = 4
    EARLY_ELECTRIC = 5
    ELECTRIC = 6
    LATE_ELECTRIC = 7

    def __str__(self) -> str:
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

    @property
    def numeral(self) -> str:
        numerals = {
            self.EARLY_STEAM: "Ⅰ",
            self.STEAM: "Ⅱ",
            self.EARLY_DIESEL: "Ⅲ",
            self.DIESEL: "Ⅳ",
            self.EARLY_ELECTRIC: "Ⅴ",
            self.ELECTRIC: "Ⅵ",
            self.LATE_ELECTRIC: "Ⅶ",
        }

        return numerals[self]


@enum.unique
class Track(enum.IntEnum):
    STANDARD = 0
    ELECTRIC = 2

    def __str__(self):
        names = {self.STANDARD: "Standard", self.ELECTRIC: "Electric"}
        return names[self]


class Amount:
    wagon_type: WagonType
    token_type: TokenType
    amount: int

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.wagon_type}, {self.token_type}, {self.amount})"


class Cost(Base, Amount):
    __tablename__ = "cost"

    id = Column(Integer, primary_key=True)
    wagon_type_id = Column(String, ForeignKey("wagon_type.id"), nullable=False)
    token_type_id = Column(String, ForeignKey("token_type.id"), nullable=False)
    amount = Column(Integer, nullable=False)

    wagon_type = relationship("WagonType", back_populates="cost")
    token_type = relationship("TokenType")


class Sell(Base, Amount):
    __tablename__ = "sell"

    wagon_type_id = Column(String, ForeignKey("wagon_type.id"), primary_key=True)
    token_type_id = Column(String, ForeignKey("token_type.id"), primary_key=True)
    amount = Column(Integer, nullable=False)

    wagon_type = relationship("WagonType", back_populates="sell")
    token_type = relationship("TokenType")


class Fuel(Base, Amount):
    __tablename__ = "fuel"

    wagon_type_id = Column(String, ForeignKey("wagon_type.id"), primary_key=True)
    token_type_id = Column(String, ForeignKey("token_type.id"), primary_key=True)
    amount = Column(Integer, nullable=False)

    wagon_type = relationship("WagonType", back_populates="fuel")
    token_type = relationship("TokenType")


class ConfigMixin:
    id: str
    name: typing.Optional[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.id} {self.name!r}]"

    def __str__(self):
        return self.name or self.id

    @classmethod
    def search(
        cls: typing.Type[T],
        *,
        ids: typing.Collection[str] = (),
        names: typing.Collection[str] = (),
    ) -> sqlalchemy.orm.Query:
        query = cls.query.filter(cls.name != None).order_by(cls.name)

        if ids:
            query = query.filter(cls.id.in_(ids))

        if names:
            query = query.filter(cls.id.in_(names))

        return query


class CargoType(Base, ConfigMixin):
    __tablename__ = "cargo_type"

    id = Column(String, primary_key=True)
    name = Column(String)
    color = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    icon_mini = Column(String)
    type = Column(String)
    load_speed = Column(Integer)
    sell_immediately = Column(Boolean, nullable=False)
    affect_city_grow = Column(Integer, nullable=True)
    train_stop_capacity = Column(Integer, nullable=True)
    road_stop_capacity = Column(Integer, nullable=True)
    stop_capacity = Column(Integer, nullable=True)

    epoch = Column(IntEnum(Epoch), nullable=True)

    @property
    def css_color(self) -> str:
        return f"#{self.color}"

    @classmethod
    def search(
        cls: typing.Type[T],
        *,
        ids: typing.Collection[str] = (),
        names: typing.Collection[str] = (),
        epoch: typing.Optional[Epoch] = None,
    ) -> sqlalchemy.orm.Query:
        query = super().search(ids=ids, names=names)

        if epoch is not None:
            query = query.filter(cls.epoch <= epoch)

        return query

    @property
    def is_passengers(self) -> bool:
        return self.name == "Passengers"


class TokenType(Base, ConfigMixin):
    __tablename__ = "token_type"

    id = Column(String, primary_key=True)
    icon = Column(String, nullable=False)
    name = Column(String)


class Color(Base, ConfigMixin):
    __tablename__ = "color"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    red = Column(Integer, nullable=False)
    green = Column(Integer, nullable=False)
    blue = Column(Integer, nullable=False)


class WagonType(Base, ConfigMixin):
    __tablename__ = "wagon_type"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    icon_color = Column(String, nullable=False)

    epoch_start = Column(IntEnum(Epoch), nullable=True)
    epoch_end = Column(IntEnum(Epoch), nullable=True)

    track = Column(IntEnum(Track), nullable=False)
    weight_empty = Column(Integer, nullable=False)
    weight_full = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)
    depo_upgrade = Column(Boolean, nullable=False)

    # All wagon types can have cargo. No engines use this yet.
    # https://store.steampowered.com/news/app/598960/view/4738306083311895973
    cargo_type_id = Column(String, ForeignKey("cargo_type.id"), nullable=True)
    cargo_type = relationship(CargoType, lazy="joined", backref="wagon_types")

    capacity = Column(Integer, nullable=False)

    cost: list[Cost] = relationship(
        Cost,
        uselist=True,
        lazy="joined",
        back_populates="wagon_type",
    )
    sell: list[Sell] = relationship(
        Sell,
        uselist=True,
        lazy="joined",
        back_populates="wagon_type",
    )
    fuel: list[Fuel] = relationship(
        Fuel,
        uselist=True,
        lazy="joined",
        back_populates="wagon_type",
    )

    bonus_income: typing.Optional[int] = Column(Integer, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type,
    }

    @property
    def is_quest_reward(self) -> bool:
        return self.epoch_start is None

    @property
    def unique(self) -> bool:
        """TODO: Special cases for quest rewards that give multiple engines."""
        return self.is_quest_reward

    def times(self, count: int) -> tuple[WagonType, ...]:
        return tuple(self for _ in range(count))

    @classmethod
    def search(
        cls: typing.Type[T],
        *,
        ids: typing.Collection[str] = (),
        names: typing.Collection[str] = (),
        epoch: typing.Optional[Epoch] = None,
    ) -> sqlalchemy.orm.Query:
        query = cls.query.order_by(cls.id)

        if ids:
            query = query.filter(cls.id.in_(ids))

        if names:
            query = query.filter(cls.id.in_(names))

        if epoch is not None:
            query = query.filter(cls.epoch_start <= epoch, epoch <= cls.epoch_end)

        return query


class Engine(WagonType, ConfigMixin):
    __tablename__ = "wagon_type_engine"
    __mapper_args__ = {
        "polymorphic_identity": "engine",
        "polymorphic_load": "inline",
    }

    id = Column(String, ForeignKey("wagon_type.id"), primary_key=True)
    power = Column(Integer, nullable=False)
    max_speed = Column(Integer, nullable=False)
    max_speed_reverse = Column(Integer, nullable=True)

    @property
    def recommended_weight(self) -> int:
        """
        This value is calculated by the game. There's a function named GetVehicleRecommendedWeight.

        Someone on the Mashinky Discord reverse engineered the formula:
        https://discord.com/channels/319014803756679171/377847968344047626/540116140576210945
        """
        return math.floor(42.1 * self.power / self.max_speed)


class Wagon(WagonType, ConfigMixin):
    __tablename__ = "wagon_type_wagon"
    __mapper_args__ = {
        "polymorphic_identity": "wagon",
        "polymorphic_load": "inline",
    }
    id = Column(String, ForeignKey("wagon_type.id"), primary_key=True)


class RoadVehicle(WagonType, ConfigMixin):
    __tablename__ = "wagon_type_road_vehicle"
    __mapper_args__ = {
        "polymorphic_identity": "road_vehicle",
        "polymorphic_load": "inline",
    }
    id = Column(String, ForeignKey("wagon_type.id"), primary_key=True)
