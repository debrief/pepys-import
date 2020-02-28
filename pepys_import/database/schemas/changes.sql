CREATE TABLE pepys."Changes"
(
    change_id    UUID         NOT NULL,
    "user"       VARCHAR(150) NOT NULL,
    modified     DATE         NOT NULL,
    reason       VARCHAR(500) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (change_id)
)
