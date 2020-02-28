CREATE TABLE pepys."Datafiles"
(
    datafile_id      UUID NOT NULL,
    simulated        BOOLEAN,
    privacy_id       UUID NOT NULL,
    datafile_type_id UUID NOT NULL,
    reference        VARCHAR(150),
    url              VARCHAR(150),
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (datafile_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id),
    FOREIGN KEY (datafile_type_id) REFERENCES pepys."DatafileTypes" (datafile_type_id)
)
