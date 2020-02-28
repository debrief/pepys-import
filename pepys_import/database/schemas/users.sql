CREATE TABLE pepys."Users"
(
    user_id      UUID         NOT NULL,
    name         VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (user_id)
)
