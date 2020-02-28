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
    FOREIGN KEY (source_id) REFERENCES pepys."Datafiles" (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
