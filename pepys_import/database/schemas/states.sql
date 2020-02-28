CREATE TABLE pepys."States"
(
    state_id     UUID                        NOT NULL,
    time         TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sensor_id    UUID                        NOT NULL,
    location     geometry(POINT, 0),
    heading      DOUBLE PRECISION,
    course       DOUBLE PRECISION,
    speed        DOUBLE PRECISION,
    source_id    UUID                        NOT NULL,
    privacy_id   UUID,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (state_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
