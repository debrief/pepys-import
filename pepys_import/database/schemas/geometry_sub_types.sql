CREATE TABLE pepys."GeometrySubTypes"
(
    geo_sub_type_id UUID         NOT NULL,
    name            VARCHAR(150) NOT NULL,
    parent          UUID         NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (geo_sub_type_id)
)
