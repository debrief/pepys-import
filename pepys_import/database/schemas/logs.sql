CREATE TABLE pepys."Logs"
(
    log_id       UUID         NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    id           UUID         NOT NULL,
    field        VARCHAR(150) NOT NULL,
    new_value    VARCHAR(150) NOT NULL,
    change_id    UUID         NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (log_id),
    FOREIGN KEY (id) REFERENCES pepys."Logs" (log_id)
)
