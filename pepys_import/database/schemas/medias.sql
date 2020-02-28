CREATE TABLE pepys."Media"
(
    media_id      UUID         NOT NULL,
    platform_id   UUID,
    subject_id    UUID,
    sensor_id     UUID,
    location      geometry(POINT, 4326),
    time          TIMESTAMP WITHOUT TIME ZONE,
    media_type_id UUID         NOT NULL,
    url           VARCHAR(150) NOT NULL,
    source_id     UUID         NOT NULL,
    privacy_id    UUID,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (media_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (subject_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (sensor_id) REFERENCES pepys."Sensors" (sensor_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
