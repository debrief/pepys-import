class PepysError(Exception):
    pass


class DatabaseError(PepysError):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class DatabaseQueryError(DatabaseError):
    pass
