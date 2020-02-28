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
)
