from pprint import pprint

from pepys_admin.maintenance.column_data import create_column_data
from pepys_import.core.store.data_store import DataStore


def test_column_data_platform():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    col_data = create_column_data(store, store.db_classes.Platform)

    correct_col_data = {
        "platform id": {"type": "id", "system_name": "platform_id"},
        "name": {
            "type": "string",
            "values": ["ADRI", "JEAN", "NARV", "SPAR"],
            "system_name": "name",
        },
        "identifier": {
            "type": "string",
            "values": ["A643", "A816", "C045", "P543"],
            "system_name": "identifier",
        },
        "trigraph": {"type": "string", "values": [], "system_name": "trigraph"},
        "quadgraph": {"type": "string", "values": [], "system_name": "quadgraph"},
        "nationality": {
            "type": "string",
            "system_name": "nationality_name",
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
        "platform type": {
            "type": "string",
            "system_name": "platform_type_name",
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
            "type": "string",
            "system_name": "privacy_name",
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
        "created date": {"system_name": "created_date", "type": "datetime"},
    }

    assert col_data == correct_col_data


def test_column_data_platform_type():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    col_data = create_column_data(store, store.db_classes.PlatformType)

    correct_col_data = {
        "created date": {"system_name": "created_date", "type": "datetime"},
        "name": {
            "system_name": "name",
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
        "platform type id": {
            "system_name": "platform_type_id",
            "type": "id",
        },
    }

    assert col_data == correct_col_data


def test_column_data_state():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    col_data = create_column_data(store, store.db_classes.State)

    print(pprint(col_data))

    correct_col_data = {
        "course": {"system_name": "course", "type": "float"},
        "created date": {"system_name": "created_date", "type": "datetime"},
        "elevation": {"system_name": "elevation", "type": "float"},
        "heading": {"system_name": "heading", "type": "float"},
        "location": {"system_name": "location", "type": "geometry"},
        "platform": {
            "system_name": "platform_name",
            "type": "string",
            "values": ["ADRI", "JEAN", "NARV", "SPAR"],
        },
        "privacy": {
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
        "remarks": {"system_name": "remarks", "type": "string", "values": []},
        "sensor": {
            "system_name": "sensor_name",
            "type": "string",
            "values": ["GPS", "INS", "Periscope", "Radar"],
        },
        "source reference": {"system_name": "source_reference", "type": "string", "values": []},
        "speed": {"system_name": "speed", "type": "float"},
        "state id": {
            "system_name": "state_id",
            "type": "id",
        },
        "time": {"system_name": "time", "type": "datetime"},
    }

    assert col_data == correct_col_data


def test_column_data_privacies():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    col_data = create_column_data(store, store.db_classes.Privacy)

    print(pprint(col_data))

    assert col_data == {
        "created date": {"system_name": "created_date", "type": "datetime"},
        "level": {"system_name": "level", "type": "int"},
        "name": {
            "system_name": "name",
            "type": "string",
            "values": [
                "Private",
                "Private UK/IE",
                "Private UK/IE/FR",
                "Public",
                "Public Sensitive",
                "Very Private",
                "Very Private UK/IE",
                "Very Private UK/IE/FR",
            ],
        },
        "privacy id": {"system_name": "privacy_id", "type": "id"},
    }
