import sqlalchemy.orm

Base = sqlalchemy.orm.declarative_base()


class CargoType(Base):
    __tablename__ = "config_cargo_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String)


class TokenType(Base):
    __tablename__ = "config_token_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String)


class Color(Base):
    __tablename__ = "config_color"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    red = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    green = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    blue = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class WagonType(Base):
    __tablename__ = "config_wagon_type"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    # icon_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    # icon_color_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    epoch = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    track = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    cost = sqlalchemy.Column(sqlalchemy.String)
    sell = sqlalchemy.Column(sqlalchemy.String)
    weight_empty = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    weight_full = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    length = sqlalchemy.Column(sqlalchemy.Numeric, nullable=False)

    # Engines
    fuel_cost = sqlalchemy.Column(sqlalchemy.String)
    power = sqlalchemy.Column(sqlalchemy.Integer)
    max_speed = sqlalchemy.Column(sqlalchemy.Integer)
    max_speed_reverse = sqlalchemy.Column(sqlalchemy.Integer)

    depo_upgrade = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Wagons + Road vehicles
    cargo_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("config_cargo_type.id"))
    cargo = sqlalchemy.orm.relationship(CargoType)
    capacity = sqlalchemy.Column(sqlalchemy.Integer)


class Engine(Base):
    __tablename__ = "app_engine"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
