from sqlalchemy import types
from sqlalchemy.types import Binary
import uuid


class UUID(types.TypeDecorator):
    impl = Binary

    def __init__(self):
        self.impl.length = 16
        types.TypeDecorator.__init__(self, length=self.impl.length)

    @staticmethod
    def process_bind_param(value, dialect=None):
        if value and isinstance(value, uuid.UUID):
            return value.bytes
        elif value and not isinstance(value, uuid.UUID):
            raise ValueError(f"value {value} is not a valid uuid.UUID")
        else:
            return None

    @staticmethod
    def process_result_value(value, dialect=None):
        if value:
            return uuid.UUID(bytes=value)
        else:
            return None

    @staticmethod
    def is_mutable():
        return False


#
#
# id_column_name = "id"
#
# def id_column():
#     import uuid
#     return Column(id_column_name,UUID(),primary_key=True,default=uuid.uuid4)
