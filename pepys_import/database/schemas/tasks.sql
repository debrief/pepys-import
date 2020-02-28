CREATE TABLE pepys."Tasks"
(
    task_id      UUID                        NOT NULL,
    parent_id    UUID                        NOT NULL,
    start        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "end"        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    environment  VARCHAR(150),
    location     VARCHAR(150),
    privacy_id   UUID                        NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (task_id),
    FOREIGN KEY (parent_id) REFERENCES pepys."Tasks" (task_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
