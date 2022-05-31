import enum
import typing

import sqlalchemy


class IntEnum(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.Integer

    def __init__(self, cls: typing.Type[enum.IntEnum], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cls = cls

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return self.cls(value)
