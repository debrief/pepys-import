CREATE TABLE pepys."UnitTypes"
(
    unit_type_id UUID         NOT NULL,
    units        VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (unit_type_id)
)
