CREATE TABLE pepys."Nationalities"
(
    nationality_id UUID         NOT NULL,
    name           VARCHAR(150) NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (nationality_id)
)
