import sqlalchemy.orm

Base = sqlalchemy.orm.declarative_base()


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
