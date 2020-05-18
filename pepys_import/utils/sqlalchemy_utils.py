import uuid

from sqlalchemy import types
from sqlalchemy.dialects import mssql, postgresql


#
# From https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/types/uuid.html#UUIDType
#
class UUIDType(types.TypeDecorator):
    """
    Stores a UUID in the database natively when it can and falls back to
    a BINARY(16) or a CHAR(32) when it can't.

    Note: In a difference to the original implementation, this uses
    a CHAR field as the default fallback to make it easier to view in SQLite
    database viewers.

    ::

        from sqlalchemy_utils import UUIDType
        import uuid

        class User(Base):
            __tablename__ = 'user'

            # Pass `binary=True` to fallback to BINARY instead of CHAR
            id = sa.Column(UUIDType(binary=False), primary_key=True)
    """

    impl = types.BINARY(16)

    python_type = uuid.UUID

    def __init__(self, binary=False, native=True, length=None):
        """
        :param binary: Whether to use a BINARY(16) or CHAR(32) fallback.

        We ignore the length parameter, but it is needed for Alembic to work properly
        """
        self.binary = binary
        self.native = native

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and self.native:
            # Use the native UUID type.
            return dialect.type_descriptor(postgresql.UUID())

        if dialect.name == "mssql" and self.native:
            # Use the native UNIQUEIDENTIFIER type.
            return dialect.type_descriptor(mssql.UNIQUEIDENTIFIER())

        else:
            # Fallback to either a BINARY or a CHAR.
            kind = self.impl if self.binary else types.CHAR(32)
            return dialect.type_descriptor(kind)

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)

            except (TypeError, ValueError):
                value = uuid.UUID(bytes=value)

        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = self._coerce(value)

        if self.native and dialect.name in ("postgresql", "mssql"):
            return str(value)

        return value.bytes if self.binary else value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if self.native and dialect.name in ("postgresql", "mssql"):
            if isinstance(value, uuid.UUID):
                # Some drivers convert PostgreSQL's uuid values to
                # Python's uuid.UUID objects by themselves
                return value
            return uuid.UUID(value)

        return uuid.UUID(bytes=value) if self.binary else uuid.UUID(value)
