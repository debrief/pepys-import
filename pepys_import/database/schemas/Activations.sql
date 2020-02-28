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
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
