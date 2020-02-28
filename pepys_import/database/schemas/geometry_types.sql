CREATE TABLE pepys."GeometryTypes"
(
    geo_type_id  UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (geo_type_id)
)
