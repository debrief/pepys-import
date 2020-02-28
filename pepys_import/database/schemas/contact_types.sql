CREATE TABLE pepys."ContactTypes"
(
    contact_type_id UUID         NOT NULL,
    contact_type    VARCHAR(150) NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (contact_type_id)
)
