CREATE TABLE pepys."Privacies"
(
    privacy_id   UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (privacy_id)
)
