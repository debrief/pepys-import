CREATE TABLE alembic_version
(
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> bcff0ccb4fbd

CREATE TABLE "Activations"
(
    activation_id INTEGER      NOT NULL,
    name          VARCHAR(150) NOT NULL,
    sensor_id     INTEGER      NOT NULL,
    start         TIMESTAMP    NOT NULL,
    "end"         TIMESTAMP    NOT NULL,
    min_range     REAL,
    max_range     REAL,
    left_arc      REAL,
    right_arc     REAL,
    source_id     INTEGER      NOT NULL,
    privacy_id    INTEGER,
    created_date  DATETIME,
    PRIMARY KEY (activation_id)
);

CREATE TABLE "Changes"
(
    change_id    INTEGER      NOT NULL,
    user         VARCHAR(150) NOT NULL,
    modified     DATE         NOT NULL,
    reason       VARCHAR(500) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (change_id)
);

CREATE TABLE "ClassificationTypes"
(
    class_type_id INTEGER      NOT NULL,
    class_type    VARCHAR(150) NOT NULL,
    created_date  DATETIME,
    PRIMARY KEY (class_type_id)
);

CREATE TABLE "CommentTypes"
(
    comment_type_id INTEGER      NOT NULL,
    name            VARCHAR(150) NOT NULL,
    created_date    DATETIME,
    PRIMARY KEY (comment_type_id)
);

CREATE TABLE "Comments"
(
    comment_id      INTEGER      NOT NULL,
    platform_id     INTEGER,
    time            TIMESTAMP    NOT NULL,
    comment_type_id INTEGER      NOT NULL,
    content         VARCHAR(150) NOT NULL,
    source_id       INTEGER      NOT NULL,
    privacy_id      INTEGER,
    created_date    DATETIME,
    PRIMARY KEY (comment_id)
);

CREATE TABLE "CommodityTypes"
(
    commodity_type_id INTEGER      NOT NULL,
    name              VARCHAR(150) NOT NULL,
    created_date      DATETIME,
    PRIMARY KEY (commodity_type_id)
);

CREATE TABLE "ConfidenceLevels"
(
    confidence_level_id INTEGER      NOT NULL,
    level               VARCHAR(150) NOT NULL,
    created_date        DATETIME,
    PRIMARY KEY (confidence_level_id)
);

CREATE TABLE "ContactTypes"
(
    contact_type_id INTEGER      NOT NULL,
    contact_type    VARCHAR(150) NOT NULL,
    created_date    DATETIME,
    PRIMARY KEY (contact_type_id)
);

CREATE TABLE "Contacts"
(
    contact_id     INTEGER   NOT NULL,
    name           VARCHAR(150),
    sensor_id      INTEGER   NOT NULL,
    time           TIMESTAMP NOT NULL,
    bearing        REAL,
    rel_bearing    REAL,
    ambig_bearing  REAL,
    freq           REAL,
    range          REAL,
    elevation      REAL,
    major          REAL,
    minor          REAL,
    orientation    REAL,
    classification VARCHAR(150),
    confidence     VARCHAR(150),
    contact_type   VARCHAR(150),
    mla            REAL,
    soa            REAL,
    subject_id     INTEGER,
    source_id      INTEGER   NOT NULL,
    privacy_id     INTEGER,
    created_date   DATETIME,
    PRIMARY KEY (contact_id)
);

SELECT AddGeometryColumn(NULL, NULL, 4326, 'POINT', 2) AS "AddGeometryColumn_1";

SELECT CreateSpatialIndex(NULL, NULL) AS "CreateSpatialIndex_1";

CREATE TABLE "DatafileTypes"
(
    datafile_type_id INTEGER      NOT NULL,
    name             VARCHAR(150) NOT NULL,
    created_date     DATETIME,
    PRIMARY KEY (datafile_type_id)
);

CREATE TABLE "Datafiles"
(
    datafile_id      INTEGER     NOT NULL,
    simulated        BOOLEAN     NOT NULL,
    privacy_id       INTEGER     NOT NULL,
    datafile_type_id INTEGER     NOT NULL,
    reference        VARCHAR(150),
    url              VARCHAR(150),
    size             INTEGER     NOT NULL,
    hash             VARCHAR(32) NOT NULL,
    created_date     DATETIME,
    PRIMARY KEY (datafile_id),
    CHECK (simulated IN (0, 1))
);

CREATE TABLE "Extractions"
(
    extraction_id INTEGER      NOT NULL,
    "table"       VARCHAR(150) NOT NULL,
    field         VARCHAR(150) NOT NULL,
    chars         VARCHAR(150) NOT NULL,
    created_date  DATETIME,
    PRIMARY KEY (extraction_id)
);

CREATE TABLE "Geometries"
(
    geometry_id         INTEGER      NOT NULL,
    name                VARCHAR(150) NOT NULL,
    geo_type_id         INTEGER      NOT NULL,
    geo_sub_type_id     INTEGER      NOT NULL,
    start               TIMESTAMP,
    "end"               TIMESTAMP,
    task_id             INTEGER,
    subject_platform_id INTEGER,
    sensor_platform_id  INTEGER,
    source_id           INTEGER      NOT NULL,
    privacy_id          INTEGER,
    created_date        DATETIME,
    PRIMARY KEY (geometry_id)
);

SELECT AddGeometryColumn(NULL, NULL, -1, 'GEOMETRY', 2) AS "AddGeometryColumn_1";

SELECT CreateSpatialIndex(NULL, NULL) AS "CreateSpatialIndex_1";

CREATE TABLE "GeometrySubTypes"
(
    geo_sub_type_id INTEGER      NOT NULL,
    name            VARCHAR(150) NOT NULL,
    parent          INTEGER      NOT NULL,
    created_date    DATETIME,
    PRIMARY KEY (geo_sub_type_id)
);

CREATE TABLE "GeometryTypes"
(
    geo_type_id  INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (geo_type_id)
);

CREATE TABLE "HostedBy"
(
    hosted_by_id INTEGER NOT NULL,
    subject_id   INTEGER NOT NULL,
    host_id      INTEGER NOT NULL,
    hosted_from  DATE    NOT NULL,
    host_to      DATE    NOT NULL,
    privacy_id   INTEGER NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (hosted_by_id)
);

CREATE TABLE "Logs"
(
    log_id       INTEGER      NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    id           INTEGER      NOT NULL,
    field        VARCHAR(150),
    new_value    VARCHAR(150),
    change_id    INTEGER      NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (log_id)
);

CREATE TABLE "LogsHoldings"
(
    logs_holding_id INTEGER      NOT NULL,
    time            TIMESTAMP    NOT NULL,
    commodity_id    INTEGER      NOT NULL,
    quantity        REAL         NOT NULL,
    unit_type_id    INTEGER      NOT NULL,
    platform_id     INTEGER      NOT NULL,
    comment         VARCHAR(150) NOT NULL,
    source_id       INTEGER      NOT NULL,
    privacy_id      INTEGER,
    created_date    DATETIME,
    PRIMARY KEY (logs_holding_id)
);

CREATE TABLE "Media"
(
    media_id      INTEGER      NOT NULL,
    platform_id   INTEGER,
    subject_id    INTEGER,
    sensor_id     INTEGER,
    elevation     REAL,
    time          TIMESTAMP,
    media_type_id INTEGER      NOT NULL,
    url           VARCHAR(150) NOT NULL,
    source_id     INTEGER      NOT NULL,
    privacy_id    INTEGER,
    created_date  DATETIME,
    PRIMARY KEY (media_id)
);

SELECT AddGeometryColumn(NULL, NULL, 4326, 'POINT', 2) AS "AddGeometryColumn_1";

SELECT CreateSpatialIndex(NULL, NULL) AS "CreateSpatialIndex_1";

CREATE TABLE "MediaTypes"
(
    media_type_id INTEGER      NOT NULL,
    name          VARCHAR(150) NOT NULL,
    created_date  DATETIME,
    PRIMARY KEY (media_type_id)
);

CREATE TABLE "Nationalities"
(
    nationality_id INTEGER      NOT NULL,
    name           VARCHAR(150) NOT NULL,
    created_date   DATETIME,
    PRIMARY KEY (nationality_id)
);

CREATE TABLE "Participants"
(
    participant_id INTEGER NOT NULL,
    platform_id    INTEGER NOT NULL,
    task_id        INTEGER NOT NULL,
    start          TIMESTAMP,
    "end"          TIMESTAMP,
    force          VARCHAR(150),
    privacy_id     INTEGER NOT NULL,
    created_date   DATETIME,
    PRIMARY KEY (participant_id)
);

CREATE TABLE "PlatformTypes"
(
    platform_type_id INTEGER NOT NULL,
    name             VARCHAR(150),
    created_date     DATETIME,
    PRIMARY KEY (platform_type_id)
);

CREATE TABLE "Platforms"
(
    platform_id      INTEGER      NOT NULL,
    name             VARCHAR(150) NOT NULL,
    pennant          VARCHAR(10),
    trigraph         VARCHAR(3),
    quadgraph        VARCHAR(4),
    nationality_id   INTEGER      NOT NULL,
    platform_type_id INTEGER      NOT NULL,
    privacy_id       INTEGER      NOT NULL,
    created_date     DATETIME,
    PRIMARY KEY (platform_id)
);

CREATE TABLE "Privacies"
(
    privacy_id   INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (privacy_id)
);

CREATE TABLE "SensorTypes"
(
    sensor_type_id INTEGER NOT NULL,
    name           VARCHAR(150),
    created_date   DATETIME,
    PRIMARY KEY (sensor_type_id)
);

CREATE TABLE "Sensors"
(
    sensor_id      INTEGER      NOT NULL,
    name           VARCHAR(150) NOT NULL,
    sensor_type_id INTEGER      NOT NULL,
    host           INTEGER      NOT NULL,
    privacy_id     INTEGER      NOT NULL,
    created_date   DATETIME,
    PRIMARY KEY (sensor_id)
);

CREATE TABLE "States"
(
    state_id     INTEGER   NOT NULL,
    time         TIMESTAMP NOT NULL,
    sensor_id    INTEGER   NOT NULL,
    elevation    REAL,
    heading      REAL,
    course       REAL,
    speed        REAL,
    source_id    INTEGER   NOT NULL,
    privacy_id   INTEGER,
    created_date DATETIME,
    PRIMARY KEY (state_id)
);

SELECT AddGeometryColumn(NULL, NULL, 4326, 'POINT', 2) AS "AddGeometryColumn_1";

SELECT CreateSpatialIndex(NULL, NULL) AS "CreateSpatialIndex_1";

CREATE TABLE "Synonyms"
(
    synonym_id   INTEGER      NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    entity       INTEGER      NOT NULL,
    synonym      VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (synonym_id)
);

CREATE TABLE "TaggedItems"
(
    tagged_item_id INTEGER NOT NULL,
    tag_id         INTEGER NOT NULL,
    item_id        INTEGER NOT NULL,
    tagged_by_id   INTEGER NOT NULL,
    private        BOOLEAN NOT NULL,
    tagged_on      DATE    NOT NULL,
    created_date   DATETIME,
    PRIMARY KEY (tagged_item_id),
    CHECK (private IN (0, 1))
);

CREATE TABLE "Tags"
(
    tag_id       INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (tag_id)
);

CREATE TABLE "Tasks"
(
    task_id      INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    parent_id    INTEGER      NOT NULL,
    start        TIMESTAMP    NOT NULL,
    "end"        TIMESTAMP    NOT NULL,
    environment  VARCHAR(150),
    location     VARCHAR(150),
    privacy_id   INTEGER      NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (task_id)
);

CREATE TABLE "UnitTypes"
(
    unit_type_id INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (unit_type_id)
);

CREATE TABLE "Users"
(
    user_id      INTEGER      NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date DATETIME,
    PRIMARY KEY (user_id)
);

INSERT INTO alembic_version (version_num)
VALUES ('bcff0ccb4fbd');

