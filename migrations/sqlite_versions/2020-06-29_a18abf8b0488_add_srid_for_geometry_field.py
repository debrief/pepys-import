"""Add SRID for Geometry field

Revision ID: a18abf8b0488
Revises: fd0f7e61611c
Create Date: 2020-06-29 09:53:29.937222

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

# revision identifiers, used by Alembic.
revision = "a18abf8b0488"
down_revision = "fd0f7e61611c"
branch_labels = None
depends_on = None

Session = sessionmaker()


def upgrade():
    # This migration script update the SRID value of the geometry column of Geometries table by
    # running raw SQL which is explained here:
    # https://gis.stackexchange.com/questions/130258/setting-srid-in-spatialite-table

    # Query for changing the expected SRID in the geometry_columns
    query_1 = """
UPDATE geometry_columns
SET srid = 4326
WHERE f_table_name = 'geometries';
    """
    # Query for updating the SRID
    query_2 = """
UPDATE Geometries
SET geometry = SetSRID(geometry, 4326);
    """
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(query_1)
    session.execute(query_2)
    session.commit()
    session.close()


def downgrade():
    # Query for changing the expected SRID in the geometry_columns
    query_1 = """
    UPDATE geometry_columns
    SET srid = -1
    WHERE f_table_name = 'geometries';
    """
    # Query for updating the SRID
    query_2 = """
    UPDATE Geometries
    SET geometry = SetSRID(geometry, -1);
    """
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(query_1)
    session.execute(query_2)
    session.commit()
    session.close()
