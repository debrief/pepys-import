from unittest import TestCase

import pytest
import sqlalchemy
from sqlalchemy.orm import undefer

from pepys_import.core.store.data_store import DataStore


class EditDataTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()
            self.store.populate_metadata()

            self.platforms = (
                self.store.session.query(self.store.db_classes.Platform).options(undefer("*")).all()
            )
            self.store.session.expunge_all()

    def test_edit_platform_identifier_single(self):
        self.store.edit_items([self.platforms[0]], {"identifier": "NEWIDENT"})

        all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
        assert len((all_platforms)) == 4

        result = (
            self.store.session.query(self.store.db_classes.Platform)
            .filter(self.store.db_classes.Platform.identifier == "NEWIDENT")
            .all()
        )
        assert len(result) == 1

        assert result[0].name == self.platforms[0].name
        assert result[0].nationality_name == self.platforms[0].nationality_name
        assert result[0].identifier == "NEWIDENT"

    def test_edit_platform_identifier_multiple(self):
        self.store.edit_items([self.platforms[0], self.platforms[1]], {"identifier": "NEWIDENT"})

        all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
        assert len((all_platforms)) == 4

        result = (
            self.store.session.query(self.store.db_classes.Platform)
            .filter(self.store.db_classes.Platform.identifier == "NEWIDENT")
            .all()
        )
        assert len(result) == 2

        assert result[0].name == self.platforms[0].name
        assert result[0].nationality_name == self.platforms[0].nationality_name
        assert result[0].identifier == "NEWIDENT"

        assert result[1].name == self.platforms[1].name
        assert result[1].nationality_name == self.platforms[1].nationality_name
        assert result[1].identifier == "NEWIDENT"

    def test_edit_platform_multiple_fields_single_object(self):
        self.store.edit_items([self.platforms[0]], {"identifier": "NEWIDENT", "name": "TestName"})

        all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
        assert len((all_platforms)) == 4

        result = (
            self.store.session.query(self.store.db_classes.Platform)
            .filter(self.store.db_classes.Platform.identifier == "NEWIDENT")
            .all()
        )
        assert len(result) == 1

        assert result[0].name == "TestName"
        assert result[0].identifier == "NEWIDENT"
        assert result[0].nationality_name == self.platforms[0].nationality_name

    def test_edit_platform_nationality(self):
        nationalities = (
            self.store.session.query(self.store.db_classes.Nationality).options(undefer("*")).all()
        )
        new_nat_id = nationalities[-1].nationality_id
        self.store.edit_items([self.platforms[0]], {"nationality": new_nat_id})

        all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
        assert len((all_platforms)) == 4

        result = self.store.session.query(self.store.db_classes.Platform).all()[0]

        assert result.name == "ADRI"
        assert result.identifier == "A643"
        assert result.nationality_name == nationalities[-1].name
        assert result.nationality_id == new_nat_id

    def test_edit_platform_plat_type(self):
        plat_types = (
            self.store.session.query(self.store.db_classes.PlatformType).options(undefer("*")).all()
        )
        new_pt_id = plat_types[0].platform_type_id
        self.store.edit_items([self.platforms[0]], {"platform_type": new_pt_id})

        all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
        assert len((all_platforms)) == 4

        result = self.store.session.query(self.store.db_classes.Platform).all()[0]

        assert result.name == "ADRI"
        assert result.identifier == "A643"
        assert result.platform_type_name == plat_types[0].name
        assert result.platform_type_id == new_pt_id

    def test_edit_platform_cause_unique_error(self):
        # This should cause a violation of a unique constraint as we're changing two platforms which already
        # have the same nationality, to have the same identifier and name too
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            self.store.edit_items(
                [self.platforms[0], self.platforms[1]],
                {"identifier": "NEWIDENT", "name": "TestName"},
            )

    def test_edit_platform_type(self):
        all_pts = (
            self.store.session.query(self.store.db_classes.PlatformType).options(undefer("*")).all()
        )
        before_len = len(all_pts)

        self.store.edit_items([all_pts[0]], {"name": "NewName"})

        all_pts = (
            self.store.session.query(self.store.db_classes.PlatformType).options(undefer("*")).all()
        )

        assert len(all_pts) == before_len

        assert all_pts[0].name == "NewName"
