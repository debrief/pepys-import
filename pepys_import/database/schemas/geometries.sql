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
    FOREIGN KEY (geo_type_id) REFERENCES pepys."GeometryTypes" (geo_type_id),
    FOREIGN KEY (geo_sub_type_id) REFERENCES pepys."GeometrySubTypes" (geo_sub_type_id),
    FOREIGN KEY (subject_platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (sensor_platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
