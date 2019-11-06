from sqlalchemy.ext.declarative import declarative_base

# define this as the base for all the DB tables here in a common module
base_postgres = declarative_base()
base_sqlite = declarative_base()
