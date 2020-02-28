CREATE TABLE pepys."Tags"
(
    tag_id       UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (tag_id)
)
