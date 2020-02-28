CREATE TABLE pepys."DatafileTypes"
(
    datafile_type_id UUID         NOT NULL,
    name             VARCHAR(150) NOT NULL,
    created_date     TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (datafile_type_id)
)
