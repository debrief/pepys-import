BEGIN;

CREATE TABLE pepys.alembic_version
(
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 5154f7db278d

CREATE TABLE pepys."Changes"
(
    change_id    UUID         NOT NULL,
    "user"       VARCHAR(150) NOT NULL,
    modified     DATE         NOT NULL,
    reason       VARCHAR(500) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (change_id)
);

CREATE TABLE pepys."ClassificationTypes"
(
    class_type_id UUID         NOT NULL,
    class_type    VARCHAR(150) NOT NULL,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (class_type_id)
);

CREATE TABLE pepys."CommentTypes"
(
    comment_type_id UUID         NOT NULL,
    name            VARCHAR(150) NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (comment_type_id)
);

CREATE TABLE pepys."CommodityTypes"
(
    commodity_type_id UUID         NOT NULL,
    name              VARCHAR(150) NOT NULL,
    created_date      TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (commodity_type_id)
);

CREATE TABLE pepys."ConfidenceLevels"
(
    confidence_level_id UUID         NOT NULL,
    level               VARCHAR(150) NOT NULL,
    created_date        TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (confidence_level_id)
);

CREATE TABLE pepys."ContactTypes"
(
    contact_type_id UUID         NOT NULL,
    contact_type    VARCHAR(150) NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (contact_type_id)
);

CREATE TABLE pepys."DatafileTypes"
(
    datafile_type_id UUID         NOT NULL,
    name             VARCHAR(150) NOT NULL,
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (datafile_type_id)
);

CREATE TABLE pepys."Extractions"
(
    extraction_id UUID         NOT NULL,
    "table"       VARCHAR(150) NOT NULL,
    field         VARCHAR(150) NOT NULL,
    chars         VARCHAR(150) NOT NULL,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (extraction_id)
);

CREATE TABLE pepys."GeometrySubTypes"
(
    geo_sub_type_id UUID         NOT NULL,
    name            VARCHAR(150) NOT NULL,
    parent          UUID         NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (geo_sub_type_id)
);

CREATE TABLE pepys."GeometryTypes"
(
    geo_type_id  UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (geo_type_id)
);

CREATE TABLE pepys."MediaTypes"
(
    media_type_id UUID         NOT NULL,
    name          VARCHAR(150) NOT NULL,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (media_type_id)
);

CREATE TABLE pepys."Nationalities"
(
    nationality_id UUID         NOT NULL,
    name           VARCHAR(150) NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (nationality_id)
);

CREATE TABLE pepys."PlatformTypes"
(
    platform_type_id UUID         NOT NULL,
    name             VARCHAR(150) NOT NULL,
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (platform_type_id)
);

CREATE TABLE pepys."Privacies"
(
    privacy_id   UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (privacy_id)
);

CREATE TABLE pepys."SensorTypes"
(
    sensor_type_id UUID         NOT NULL,
    name           VARCHAR(150) NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (sensor_type_id)
);

CREATE TABLE pepys."Synonyms"
(
    synonym_id   UUID         NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    entity       UUID         NOT NULL,
    synonym      VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (synonym_id)
);

CREATE TABLE pepys."Tags"
(
    tag_id       UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (tag_id)
);

CREATE TABLE pepys."UnitTypes"
(
    unit_type_id UUID         NOT NULL,
    units        VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (unit_type_id)
);

CREATE TABLE pepys."Users"
(
    user_id      UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (user_id)
);

CREATE TABLE pepys."Datafiles"
(
    datafile_id      UUID        NOT NULL,
    simulated        BOOLEAN,
    privacy_id       UUID        NOT NULL,
    datafile_type_id UUID        NOT NULL,
    reference        VARCHAR(150),
    url              VARCHAR(150),
    size             INTEGER     NOT NULL,
    hash             VARCHAR(32) NOT NULL,
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (datafile_id),
    FOREIGN KEY (datafile_type_id) REFERENCES pepys."DatafileTypes" (datafile_type_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
);

CREATE TABLE pepys."Logs"
(
    log_id       UUID         NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    id           UUID         NOT NULL,
    field        VARCHAR(150),
    new_value    VARCHAR(150),
    change_id    UUID         NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (log_id),
    FOREIGN KEY (change_id) REFERENCES pepys."Changes" (change_id)
);

CREATE TABLE pepys."Platforms"
(
    platform_id      UUID         NOT NULL,
    name             VARCHAR(150) NOT NULL,
    pennant          VARCHAR(10),
    trigraph         VARCHAR(3),
    quadgraph        VARCHAR(4),
    nationality_id   UUID         NOT NULL,
    platform_type_id UUID         NOT NULL,
    privacy_id       UUID         NOT NULL,
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (platform_id),
    FOREIGN KEY (nationality_id) REFERENCES pepys."Nationalities" (nationality_id),
    FOREIGN KEY (platform_type_id) REFERENCES pepys."PlatformTypes" (platform_type_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
);

CREATE TABLE pepys."TaggedItems"
(
    tagged_item_id UUID    NOT NULL,
    tag_id         UUID    NOT NULL,
    item_id        UUID    NOT NULL,
    tagged_by_id   UUID    NOT NULL,
    private        BOOLEAN NOT NULL,
    tagged_on      DATE    NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (tagged_item_id),
    FOREIGN KEY (tag_id) REFERENCES pepys."Tags" (tag_id),
    FOREIGN KEY (tagged_by_id) REFERENCES pepys."Users" (user_id)
);

CREATE TABLE pepys."Tasks"
(
    task_id      UUID                        NOT NULL,
    parent_id    UUID                        NOT NULL,
    start        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "end"        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    environment  VARCHAR(150),
    location     VARCHAR(150),
    privacy_id   UUID                        NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (task_id),
    FOREIGN KEY (parent_id) REFERENCES pepys."Tasks" (task_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
);

CREATE TABLE pepys."Comments"
(
    comment_id      UUID                        NOT NULL,
    platform_id     UUID                        NOT NULL,
    time            TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    comment_type_id UUID                        NOT NULL,
    content         VARCHAR(150)                NOT NULL,
    source_id       UUID                        NOT NULL,
    privacy_id      UUID,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id)
);

CREATE TABLE pepys."Geometries"
(
    geometry_id         UUID                   NOT NULL,
    geometry            geometry(GEOMETRY, -1) NOT NULL,
    name                VARCHAR(150)           NOT NULL,
    geo_type_id         UUID                   NOT NULL,
    geo_sub_type_id     UUID                   NOT NULL,
    start               TIMESTAMP WITHOUT TIME ZONE,
    "end"               TIMESTAMP WITHOUT TIME ZONE,
    task_id             UUID,
    subject_platform_id UUID,
    sensor_platform_id  UUID,
    source_id           UUID                   NOT NULL,
    privacy_id          UUID,
    created_date        TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (geometry_id),
    FOREIGN KEY (geo_sub_type_id) REFERENCES pepys."GeometrySubTypes" (geo_sub_type_id),
    FOREIGN KEY (geo_type_id) REFERENCES pepys."GeometryTypes" (geo_type_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (subject_platform_id) REFERENCES pepys."Platforms" (platform_id)
);

CREATE INDEX "idx_Geometries_geometry" ON "pepys"."Geometries" USING GIST ("geometry");

CREATE TABLE pepys."HostedBy"
(
    hosted_by_id UUID NOT NULL,
    subject_id   UUID NOT NULL,
    host_id      UUID NOT NULL,
    hosted_from  DATE NOT NULL,
    host_to      DATE NOT NULL,
    privacy_id   UUID NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (hosted_by_id),
    FOREIGN KEY (host_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (subject_id) REFERENCES pepys."Platforms" (platform_id)
);

CREATE TABLE pepys."LogsHoldings"
(
    logs_holding_id UUID                        NOT NULL,
    time            TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    quantity        DOUBLE PRECISION            NOT NULL,
    unit_type_id    UUID                        NOT NULL,
    platform_id     UUID                        NOT NULL,
    comment         VARCHAR(150)                NOT NULL,
    source_id       UUID                        NOT NULL,
    privacy_id      UUID,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (logs_holding_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (unit_type_id) REFERENCES pepys."UnitTypes" (unit_type_id)
);

CREATE TABLE pepys."Participants"
(
    participant_id UUID NOT NULL,
    platform_id    UUID NOT NULL,
    task_id        UUID NOT NULL,
    start          TIMESTAMP WITHOUT TIME ZONE,
    "end"          TIMESTAMP WITHOUT TIME ZONE,
    force          VARCHAR(150),
    privacy_id     UUID NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (participant_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (task_id) REFERENCES pepys."Tasks" (task_id)
);

CREATE TABLE pepys."Sensors"
(
    sensor_id      UUID         NOT NULL,
    name           VARCHAR(150) NOT NULL,
    sensor_type_id UUID         NOT NULL,
    host           UUID         NOT NULL,
    privacy_id     UUID         NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (sensor_id),
    FOREIGN KEY (host) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_type_id) REFERENCES pepys."SensorTypes" (sensor_type_id)
);

CREATE TABLE pepys."Activations"
(
    activation_id UUID                        NOT NULL,
    name          VARCHAR(150)                NOT NULL,
    sensor_id     UUID                        NOT NULL,
    start         TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "end"         TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    min_range     DOUBLE PRECISION,
    max_range     DOUBLE PRECISION,
    left_arc      DOUBLE PRECISION,
    right_arc     DOUBLE PRECISION,
    source_id     UUID                        NOT NULL,
    privacy_id    UUID,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (activation_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id)
);

CREATE TABLE pepys."Contacts"
(
    contact_id     UUID                        NOT NULL,
    name           VARCHAR(150),
    sensor_id      UUID                        NOT NULL,
    time           TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    bearing        DOUBLE PRECISION,
    rel_bearing    DOUBLE PRECISION,
    ambig_bearing  DOUBLE PRECISION,
    freq           DOUBLE PRECISION,
    range          DOUBLE PRECISION,
    location       geometry(POINT, 4326),
    elevation      DOUBLE PRECISION,
    major          DOUBLE PRECISION,
    minor          DOUBLE PRECISION,
    orientation    DOUBLE PRECISION,
    classification VARCHAR(150),
    confidence     VARCHAR(150),
    contact_type   VARCHAR(150),
    mla            DOUBLE PRECISION,
    soa            DOUBLE PRECISION,
    subject_id     UUID,
    source_id      UUID                        NOT NULL,
    privacy_id     UUID,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (contact_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (subject_id) REFERENCES pepys."Platforms" (platform_id)
);

CREATE INDEX "idx_Contacts_location" ON "pepys"."Contacts" USING GIST ("location");

CREATE TABLE pepys."Media"
(
    media_id      UUID         NOT NULL,
    platform_id   UUID,
    subject_id    UUID,
    sensor_id     UUID,
    location      geometry(POINT, 4326),
    elevation     DOUBLE PRECISION,
    time          TIMESTAMP WITHOUT TIME ZONE,
    media_type_id UUID         NOT NULL,
    url           VARCHAR(150) NOT NULL,
    source_id     UUID         NOT NULL,
    privacy_id    UUID,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (media_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (subject_id) REFERENCES pepys."Platforms" (platform_id)
);

CREATE INDEX "idx_Media_location" ON "pepys"."Media" USING GIST ("location");

CREATE TABLE pepys."States"
(
    state_id     UUID                        NOT NULL,
    time         TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sensor_id    UUID                        NOT NULL,
    location     geometry(POINT, 4326),
    elevation    DOUBLE PRECISION,
    heading      DOUBLE PRECISION,
    course       DOUBLE PRECISION,
    speed        DOUBLE PRECISION,
    source_id    UUID                        NOT NULL,
    privacy_id   UUID,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (state_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id)
);

CREATE INDEX "idx_States_location" ON "pepys"."States" USING GIST ("location");

INSERT INTO pepys.alembic_version (version_num)
VALUES ('5154f7db278d');

COMMIT;

