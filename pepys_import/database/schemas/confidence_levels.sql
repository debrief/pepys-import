CREATE TABLE pepys."ConfidenceLevels"
(
    confidence_level_id UUID         NOT NULL,
    level               VARCHAR(150) NOT NULL,
    created_date        TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (confidence_level_id)
)
