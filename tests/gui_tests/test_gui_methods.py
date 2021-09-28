import uuid
from unittest.mock import Mock

import pytest

from pepys_admin.maintenance.gui import MaintenanceGUI
from pepys_import.core.store.db_status import TableTypes

# These tests only work properly if pytest is run with the -s option
# that stops pytest trying to change where stdin is pointing to.
# This is because the constructor of the prompt_toolkit Application class
# tries to sort out input/output terminals, even if we don't call
# the run method.
# I tried various ways to configure this programatically, and they all
# failed in various interesting and intermittent ways - so it is best
# just to run these tests with -s.
# The first few lines of each test skip the test if pytest hasn't been
# run with -s - otherwise they would fail.
# The CI configuration has been updated to do two test runs: one
# for most of the tests without -s, and then the GUI tests with -s.


def set_selected_table_to_platform(gui):
    gui.current_table_object = gui.data_store.db_classes.Platform
    gui.get_column_data(gui.current_table_object)
    gui.dropdown_table.text = "Platforms"
    gui.get_default_preview_fields()


def set_selected_table_to_nationality(gui):
    gui.current_table_object = gui.data_store.db_classes.Nationality
    gui.get_column_data(gui.current_table_object)
    gui.dropdown_table.text = "Nationalities"
    gui.get_default_preview_fields()


def test_generating_column_data(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    gui = MaintenanceGUI(test_datastore)
    set_selected_table_to_platform(gui)

    correct_col_data = {
        "created date": {
            "required": False,
            "sqlalchemy_type": "column",
            "system_name": "created_date",
            "type": "datetime",
        },
        "identifier": {
            "required": True,
            "sqlalchemy_type": "column",
            "system_name": "identifier",
            "type": "string",
            "values": ["A643", "A816", "C045", "P543"],
        },
        "name": {
            "required": True,
            "sqlalchemy_type": "column",
            "system_name": "name",
            "type": "string",
            "values": ["ADRI", "JEAN", "NARV", "SPAR"],
        },
        "nationality": {
            "foreign_table_type": TableTypes.REFERENCE,
            "multiple_values_allowed": False,
            "required": True,
            "second_level": False,
            "sqlalchemy_type": "relationship",
            "system_name": "nationality",
            "type": "string",
            "values": [
                "United Kingdom",
                "Canada",
                "France",
                "Germany",
                "Italy",
                "Netherlands",
                "United States",
                "Afghanistan",
                "Albania",
                "Algeria",
                "American Samoa",
                "Andorra",
                "Angola",
                "Anguilla",
                "Antarctica",
                "Antigua and Barbuda",
                "Argentina",
                "Armenia",
                "Aruba",
                "Australia",
                "Austria",
                "Azerbaijan",
                "Bahamas",
                "Bahrain",
                "Bangladesh",
                "Barbados",
                "Belarus",
                "Belgium",
                "Belize",
                "Benin",
                "Bermuda",
                "Bhutan",
                "Bolivia, Plurinational State of",
                "Bolivia",
                "Bosnia and Herzegovina",
                "Botswana",
                "Bouvet Island",
                "Brazil",
                "British Indian Ocean Territory",
                "Brunei Darussalam",
                "Brunei",
                "Bulgaria",
                "Burkina Faso",
                "Burundi",
                "Cambodia",
                "Cameroon",
                "Cape Verde",
                "Cayman Islands",
                "Central African Republic",
                "Chad",
                "Chile",
                "China",
                "Christmas Island",
                "Cocos (Keeling) Islands",
                "Colombia",
                "Comoros",
                "Congo",
                "Congo, the Democratic Republic of the",
                "Cook Islands",
                "Costa Rica",
                "Cote d'Ivoire",
                "Ivory Coast",
                "Croatia",
                "Cuba",
                "Cyprus",
                "Czech Republic",
                "Denmark",
                "Djibouti",
                "Dominica",
                "Dominican Republic",
                "Ecuador",
                "Egypt",
                "El Salvador",
                "Equatorial Guinea",
                "Eritrea",
                "Estonia",
                "Ethiopia",
                "Falkland Islands (Malvinas)",
                "Faroe Islands",
                "Fiji",
                "Finland",
                "French Guiana",
                "French Polynesia",
                "French Southern Territories",
                "Gabon",
                "Gambia",
                "Georgia",
                "Ghana",
                "Gibraltar",
                "Greece",
                "Greenland",
                "Grenada",
                "Guadeloupe",
                "Guam",
                "Guatemala",
                "Guernsey",
                "Guinea",
                "Guinea-Bissau",
                "Guyana",
                "Haiti",
                "Heard Island and McDonald Islands",
                "Holy See (Vatican City State)",
                "Honduras",
                "Hong Kong",
                "Hungary",
                "Iceland",
                "India",
                "Indonesia",
                "Iran, Islamic Republic of",
                "Iraq",
                "Ireland",
                "Isle of Man",
                "Israel",
                "Jamaica",
                "Japan",
                "Jersey",
                "Jordan",
                "Kazakhstan",
                "Kenya",
                "Kiribati",
                "Korea, Democratic People's Republic of",
                "Korea, Republic of",
                "South Korea",
                "Kuwait",
                "Kyrgyzstan",
                "Lao People's Democratic Republic",
                "Latvia",
                "Lebanon",
                "Lesotho",
                "Liberia",
                "Libyan Arab Jamahiriya",
                "Libya",
                "Liechtenstein",
                "Lithuania",
                "Luxembourg",
                "Macao",
                "Macedonia, the former Yugoslav Republic of",
                "Madagascar",
                "Malawi",
                "Malaysia",
                "Maldives",
                "Mali",
                "Malta",
                "Marshall Islands",
                "Martinique",
                "Mauritania",
                "Mauritius",
                "Mayotte",
                "Mexico",
                "Micronesia, Federated States of",
                "Moldova, Republic of",
                "Monaco",
                "Mongolia",
                "Montenegro",
                "Montserrat",
                "Morocco",
                "Mozambique",
                "Myanmar",
                "Burma",
                "Namibia",
                "Nauru",
                "Nepal",
                "Netherlands Antilles",
                "New Caledonia",
                "New Zealand",
                "Nicaragua",
                "Niger",
                "Nigeria",
                "Niue",
                "Norfolk Island",
                "Northern Mariana Islands",
                "Norway",
                "Oman",
                "Pakistan",
                "Palau",
                "Palestinian Territory, Occupied",
                "Panama",
                "Papua New Guinea",
                "Paraguay",
                "Peru",
                "Philippines",
                "Pitcairn",
                "Poland",
                "Portugal",
                "Puerto Rico",
                "Qatar",
                "Reunion",
                "Romania",
                "Russian Federation",
                "Russia",
                "Rwanda",
                "Saint Helena, Ascension and Tristan da Cunha",
                "Saint Kitts and Nevis",
                "Saint Lucia",
                "Saint Pierre and Miquelon",
                "Saint Vincent and the Grenadines",
                "Saint Vincent & the Grenadines",
                "St. Vincent and the Grenadines",
                "Samoa",
                "San Marino",
                "Sao Tome and Principe",
                "Saudi Arabia",
                "Senegal",
                "Serbia",
                "Seychelles",
                "Sierra Leone",
                "Singapore",
                "Slovakia",
                "Slovenia",
                "Solomon Islands",
                "Somalia",
                "South Africa",
                "South Georgia and the South Sandwich Islands",
                "South Sudan",
                "Spain",
                "Sri Lanka",
                "Sudan",
                "Suriname",
                "Svalbard and Jan Mayen",
                "Swaziland",
                "Sweden",
                "Switzerland",
                "Syrian Arab Republic",
                "Taiwan, Province of China",
                "Taiwan",
                "Tajikistan",
                "Tanzania, United Republic of",
                "Thailand",
                "Timor-Leste",
                "Togo",
                "Tokelau",
                "Tonga",
                "Trinidad and Tobago",
                "Tunisia",
                "Turkey",
                "Turkmenistan",
                "Turks and Caicos Islands",
                "Tuvalu",
                "Uganda",
                "Ukraine",
                "United Arab Emirates",
                "United States Minor Outlying Islands",
                "Uruguay",
                "Uzbekistan",
                "Vanuatu",
                "Venezuela, Bolivarian Republic of",
                "Venezuela",
                "Viet Nam",
                "Vietnam",
                "Virgin Islands, British",
                "Virgin Islands, U.S.",
                "Wallis and Futuna",
                "Western Sahara",
                "Yemen",
                "Zambia",
                "Zimbabwe",
            ],
        },
        "nationality name": {
            "required": True,
            "sqlalchemy_type": "assoc_proxy",
            "system_name": "nationality_name",
            "type": "string",
            "values": [
                "United Kingdom",
                "Canada",
                "France",
                "Germany",
                "Italy",
                "Netherlands",
                "United States",
                "Afghanistan",
                "Albania",
                "Algeria",
                "American Samoa",
                "Andorra",
                "Angola",
                "Anguilla",
                "Antarctica",
                "Antigua and Barbuda",
                "Argentina",
                "Armenia",
                "Aruba",
                "Australia",
                "Austria",
                "Azerbaijan",
                "Bahamas",
                "Bahrain",
                "Bangladesh",
                "Barbados",
                "Belarus",
                "Belgium",
                "Belize",
                "Benin",
                "Bermuda",
                "Bhutan",
                "Bolivia, Plurinational State of",
                "Bolivia",
                "Bosnia and Herzegovina",
                "Botswana",
                "Bouvet Island",
                "Brazil",
                "British Indian Ocean Territory",
                "Brunei Darussalam",
                "Brunei",
                "Bulgaria",
                "Burkina Faso",
                "Burundi",
                "Cambodia",
                "Cameroon",
                "Cape Verde",
                "Cayman Islands",
                "Central African Republic",
                "Chad",
                "Chile",
                "China",
                "Christmas Island",
                "Cocos (Keeling) Islands",
                "Colombia",
                "Comoros",
                "Congo",
                "Congo, the Democratic Republic of the",
                "Cook Islands",
                "Costa Rica",
                "Cote d'Ivoire",
                "Ivory Coast",
                "Croatia",
                "Cuba",
                "Cyprus",
                "Czech Republic",
                "Denmark",
                "Djibouti",
                "Dominica",
                "Dominican Republic",
                "Ecuador",
                "Egypt",
                "El Salvador",
                "Equatorial Guinea",
                "Eritrea",
                "Estonia",
                "Ethiopia",
                "Falkland Islands (Malvinas)",
                "Faroe Islands",
                "Fiji",
                "Finland",
                "French Guiana",
                "French Polynesia",
                "French Southern Territories",
                "Gabon",
                "Gambia",
                "Georgia",
                "Ghana",
                "Gibraltar",
                "Greece",
                "Greenland",
                "Grenada",
                "Guadeloupe",
                "Guam",
                "Guatemala",
                "Guernsey",
                "Guinea",
                "Guinea-Bissau",
                "Guyana",
                "Haiti",
                "Heard Island and McDonald Islands",
                "Holy See (Vatican City State)",
                "Honduras",
                "Hong Kong",
                "Hungary",
                "Iceland",
                "India",
                "Indonesia",
                "Iran, Islamic Republic of",
                "Iraq",
                "Ireland",
                "Isle of Man",
                "Israel",
                "Jamaica",
                "Japan",
                "Jersey",
                "Jordan",
                "Kazakhstan",
                "Kenya",
                "Kiribati",
                "Korea, Democratic People's Republic of",
                "Korea, Republic of",
                "South Korea",
                "Kuwait",
                "Kyrgyzstan",
                "Lao People's Democratic Republic",
                "Latvia",
                "Lebanon",
                "Lesotho",
                "Liberia",
                "Libyan Arab Jamahiriya",
                "Libya",
                "Liechtenstein",
                "Lithuania",
                "Luxembourg",
                "Macao",
                "Macedonia, the former Yugoslav Republic of",
                "Madagascar",
                "Malawi",
                "Malaysia",
                "Maldives",
                "Mali",
                "Malta",
                "Marshall Islands",
                "Martinique",
                "Mauritania",
                "Mauritius",
                "Mayotte",
                "Mexico",
                "Micronesia, Federated States of",
                "Moldova, Republic of",
                "Monaco",
                "Mongolia",
                "Montenegro",
                "Montserrat",
                "Morocco",
                "Mozambique",
                "Myanmar",
                "Burma",
                "Namibia",
                "Nauru",
                "Nepal",
                "Netherlands Antilles",
                "New Caledonia",
                "New Zealand",
                "Nicaragua",
                "Niger",
                "Nigeria",
                "Niue",
                "Norfolk Island",
                "Northern Mariana Islands",
                "Norway",
                "Oman",
                "Pakistan",
                "Palau",
                "Palestinian Territory, Occupied",
                "Panama",
                "Papua New Guinea",
                "Paraguay",
                "Peru",
                "Philippines",
                "Pitcairn",
                "Poland",
                "Portugal",
                "Puerto Rico",
                "Qatar",
                "Reunion",
                "Romania",
                "Russian Federation",
                "Russia",
                "Rwanda",
                "Saint Helena, Ascension and Tristan da Cunha",
                "Saint Kitts and Nevis",
                "Saint Lucia",
                "Saint Pierre and Miquelon",
                "Saint Vincent and the Grenadines",
                "Saint Vincent & the Grenadines",
                "St. Vincent and the Grenadines",
                "Samoa",
                "San Marino",
                "Sao Tome and Principe",
                "Saudi Arabia",
                "Senegal",
                "Serbia",
                "Seychelles",
                "Sierra Leone",
                "Singapore",
                "Slovakia",
                "Slovenia",
                "Solomon Islands",
                "Somalia",
                "South Africa",
                "South Georgia and the South Sandwich Islands",
                "South Sudan",
                "Spain",
                "Sri Lanka",
                "Sudan",
                "Suriname",
                "Svalbard and Jan Mayen",
                "Swaziland",
                "Sweden",
                "Switzerland",
                "Syrian Arab Republic",
                "Taiwan, Province of China",
                "Taiwan",
                "Tajikistan",
                "Tanzania, United Republic of",
                "Thailand",
                "Timor-Leste",
                "Togo",
                "Tokelau",
                "Tonga",
                "Trinidad and Tobago",
                "Tunisia",
                "Turkey",
                "Turkmenistan",
                "Turks and Caicos Islands",
                "Tuvalu",
                "Uganda",
                "Ukraine",
                "United Arab Emirates",
                "United States Minor Outlying Islands",
                "Uruguay",
                "Uzbekistan",
                "Vanuatu",
                "Venezuela, Bolivarian Republic of",
                "Venezuela",
                "Viet Nam",
                "Vietnam",
                "Virgin Islands, British",
                "Virgin Islands, U.S.",
                "Wallis and Futuna",
                "Western Sahara",
                "Yemen",
                "Zambia",
                "Zimbabwe",
            ],
        },
        "platform id": {
            "required": True,
            "sqlalchemy_type": "column",
            "system_name": "platform_id",
            "type": "id",
        },
        "platform type": {
            "foreign_table_type": TableTypes.REFERENCE,
            "multiple_values_allowed": False,
            "required": True,
            "second_level": False,
            "sqlalchemy_type": "relationship",
            "system_name": "platform_type",
            "type": "string",
            "values": [
                "Naval - aircraft",
                "Naval - frigate",
                "Naval - auxiliary",
                "Naval - destroyer",
                "Naval - survey",
                "Naval - minesweeper",
                "Naval - patrol",
                "Naval - aircraft carrier",
                "Naval - submarine",
                "Naval - miscellaneous",
                "Merchant",
                "Tug",
                "Tanker",
                "Law Enforcement",
                "Pleasure Craft",
                "Search and Rescue",
                "Fishing Vessel",
                "Passenger/Ferry",
                "High Speed Craft",
            ],
        },
        "platform type name": {
            "required": True,
            "sqlalchemy_type": "assoc_proxy",
            "system_name": "platform_type_name",
            "type": "string",
            "values": [
                "Fishing Vessel",
                "High Speed Craft",
                "Law Enforcement",
                "Merchant",
                "Naval - aircraft",
                "Naval - aircraft carrier",
                "Naval - auxiliary",
                "Naval - destroyer",
                "Naval - frigate",
                "Naval - minesweeper",
                "Naval - miscellaneous",
                "Naval - patrol",
                "Naval - submarine",
                "Naval - survey",
                "Passenger/Ferry",
                "Pleasure Craft",
                "Search and Rescue",
                "Tanker",
                "Tug",
            ],
        },
        "privacy": {
            "foreign_table_type": TableTypes.REFERENCE,
            "multiple_values_allowed": False,
            "required": True,
            "second_level": False,
            "sqlalchemy_type": "relationship",
            "system_name": "privacy",
            "type": "string",
            "values": [
                "Public",
                "Public Sensitive",
                "Private",
                "Private UK/IE",
                "Very Private UK/IE",
                "Private UK/IE/FR",
                "Very Private UK/IE/FR",
                "Very Private",
            ],
        },
        "privacy name": {
            "required": True,
            "sqlalchemy_type": "assoc_proxy",
            "system_name": "privacy_name",
            "type": "string",
            "values": [
                "Public",
                "Public Sensitive",
                "Private",
                "Private UK/IE",
                "Very Private UK/IE",
                "Private UK/IE/FR",
                "Very Private UK/IE/FR",
                "Very Private",
            ],
        },
        "quadgraph": {
            "required": False,
            "sqlalchemy_type": "column",
            "system_name": "quadgraph",
            "type": "string",
            "values": [],
        },
        "trigraph": {
            "required": False,
            "sqlalchemy_type": "column",
            "system_name": "trigraph",
            "type": "string",
            "values": [],
        },
        "wargame participations": {
            "required": True,
            "sqlalchemy_type": "assoc_proxy",
            "system_name": "wargame_participations",
            "type": "string",
            "values": [],
        },
    }
    output_col_data = gui.column_data

    del output_col_data["nationality"]["ids"]
    del output_col_data["platform type"]["ids"]
    del output_col_data["privacy"]["ids"]

    assert output_col_data == correct_col_data


def test_running_query_single_condition(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    gui = MaintenanceGUI(test_datastore)
    set_selected_table_to_platform(gui)

    gui.filter_widget = Mock()
    gui.filter_widget.filters = [["name", "=", "ADRI"]]

    gui.run_query()

    # Should be 2 entries because of the header line,
    # plus the one result
    assert len(gui.table_data) == 2
    assert len(gui.table_objects) == 2

    assert gui.table_data[0] == ["Name", "Identifier", "Nationality name", "Platform type name"]
    assert gui.table_data[1] == ["ADRI", "A643", "United Kingdom", "Naval - frigate"]

    assert isinstance(gui.table_objects[1], gui.data_store.db_classes.Platform)
    assert gui.table_objects[0] is None
    assert gui.table_objects[1].name == "ADRI"


def test_running_query_two_conditions_or(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    gui = MaintenanceGUI(test_datastore)
    set_selected_table_to_platform(gui)

    gui.filter_widget = Mock()
    gui.filter_widget.filters = [["name", "=", "ADRI"], ["OR"], ["name", "=", "JEAN"]]

    gui.run_query()

    # Should be 3 entries because of the header line,
    # plus the two results
    assert len(gui.table_data) == 3
    assert len(gui.table_objects) == 3

    assert gui.table_data[0] == ["Name", "Identifier", "Nationality name", "Platform type name"]
    assert gui.table_data[2] == ["JEAN", "A816", "United Kingdom", "Naval - frigate"]

    assert isinstance(gui.table_objects[2], gui.data_store.db_classes.Platform)
    assert gui.table_objects[0] is None
    assert gui.table_objects[2].name == "JEAN"


def test_running_query_two_conditions_and(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    gui = MaintenanceGUI(test_datastore)
    set_selected_table_to_platform(gui)

    gui.filter_widget = Mock()
    gui.filter_widget.filters = [
        ["nationality_name", "=", "United Kingdom"],
        ["AND"],
        ["identifier", "LIKE", "A"],
    ]

    gui.run_query()

    # Should be 3 entries because of the header line,
    # plus the two results
    assert len(gui.table_data) == 3
    assert len(gui.table_objects) == 3

    assert gui.table_data[0] == ["Name", "Identifier", "Nationality name", "Platform type name"]
    assert gui.table_data[1] == ["ADRI", "A643", "United Kingdom", "Naval - frigate"]
    assert gui.table_data[2] == ["JEAN", "A816", "United Kingdom", "Naval - frigate"]

    assert isinstance(gui.table_objects[2], gui.data_store.db_classes.Platform)
    assert gui.table_objects[0] is None
    assert gui.table_objects[1].name == "ADRI"
    assert gui.table_objects[2].name == "JEAN"


def test_selecting_all_table_entries(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    gui = MaintenanceGUI(test_datastore)
    set_selected_table_to_nationality(gui)

    gui.run_query()

    # Should be 101 entries because of the header line,
    # plus the 100 results
    assert len(gui.table_data) == 101
    assert len(gui.table_objects) == 101

    assert gui.table_data[0] == ["Name", "Priority"]
    assert gui.table_data[1] == ["Afghanistan", "None"]

    gui.preview_table.current_values = gui.table_objects[1:]
    gui.preview_table.non_visible_selected = True

    non_vis_entries = gui.get_non_visible_entries_from_database(lambda x: None, lambda x: None)
    # Should be 256 - 100
    assert len(non_vis_entries) == 156

    assert isinstance(non_vis_entries[0], uuid.UUID)

    with test_datastore.session_scope():
        entries = (
            test_datastore.session.query(test_datastore.db_classes.Nationality)
            .filter(test_datastore.db_classes.Nationality.nationality_id.in_(non_vis_entries))
            .all()
        )
        names = set([entry.name for entry in entries])

        # Hong Kong is last entry shown in preview table, so shouldn't be in the non-visible items list
        assert "Hong Kong" not in names
        # UK is further down the list, so should be in the list
        assert "United Kingdom" in names
