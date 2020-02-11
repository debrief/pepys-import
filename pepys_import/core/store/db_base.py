from sqlalchemy.ext.declarative import declarative_base

# define this as the base for all the DB tables here in a common module
BasePostGIS = declarative_base()
BaseSpatiaLite = declarative_base()
