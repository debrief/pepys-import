CREATE TABLE pepys."Extractions"
(
    extraction_id UUID         NOT NULL,
    "table"       VARCHAR(150) NOT NULL,
    field         VARCHAR(150) NOT NULL,
    chars         VARCHAR(150) NOT NULL,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (extraction_id)
)
