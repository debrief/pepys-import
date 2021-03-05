from unittest import TestCase

import pytest
import sqlalchemy

from pepys_import.core.store.data_store import DataStore


class AddDataTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()
            self.store.populate_metadata()

    def test_add_plat_type(self):
        with self.store.session_scope():
            self.store.add_item(self.store.db_classes.PlatformType, {"name": "NewPlatformType"})

        with self.store.session_scope():
            results = (
                self.store.session.query(self.store.db_classes.PlatformType)
                .filter(self.store.db_classes.PlatformType.name == "NewPlatformType")
                .all()
            )
            assert len(results) == 1

    def test_add_platform(self):
        Platform = self.store.db_classes.Platform
        Nationality = self.store.db_classes.Nationality
        PlatformType = self.store.db_classes.PlatformType
        Privacy = self.store.db_classes.Privacy

        nat_id = self.store.session.query(Nationality).all()[-1].nationality_id
        pt_id = self.store.session.query(PlatformType).all()[-1].platform_type_id
        priv_id = self.store.session.query(Privacy).all()[-1].privacy_id

        with self.store.session_scope():
            self.store.add_item(
                Platform,
                {
                    "name": "NewPlatform",
                    "trigraph": "ABC",
                    "identifier": "NewIdent",
                    "nationality_name": nat_id,
                    "platform_type_name": pt_id,
                    "privacy_name": priv_id,
                },
            )

        with self.store.session_scope():
            results = (
                self.store.session.query(Platform).filter(Platform.name == "NewPlatform").all()
            )
            assert len(results) == 1

            assert results[0].name == "NewPlatform"
            assert results[0].trigraph == "ABC"
            assert results[0].identifier == "NewIdent"
            assert results[0].nationality_id == nat_id
            assert results[0].platform_type_id == pt_id
            assert results[0].privacy_id == priv_id

    def test_add_platform_fields_missing(self):
        Platform = self.store.db_classes.Platform
        Nationality = self.store.db_classes.Nationality
        PlatformType = self.store.db_classes.PlatformType
        Privacy = self.store.db_classes.Privacy

        nat_id = self.store.session.query(Nationality).all()[-1].nationality_id
        pt_id = self.store.session.query(PlatformType).all()[-1].platform_type_id
        priv_id = self.store.session.query(Privacy).all()[-1].privacy_id

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            with self.store.session_scope():
                # with pytest.raises(sqlalchemy.exc.IntegrityError):
                # Identifier field not specified
                self.store.add_item(
                    Platform,
                    {
                        "name": "NewPlatform",
                        "nationality_name": nat_id,
                        "platform_type_name": pt_id,
                        "privacy_name": priv_id,
                    },
                )
