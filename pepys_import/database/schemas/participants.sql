CREATE TABLE pepys."Participants"
(
    participant_id UUID NOT NULL,
    platform_id    UUID NOT NULL,
    task_id        UUID NOT NULL,
    start          TIMESTAMP WITHOUT TIME ZONE,
    "end"          TIMESTAMP WITHOUT TIME ZONE,
    force          VARCHAR(150),
    privacy_id     UUID NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (participant_id),
    FOREIGN KEY (platform_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (task_id) REFERENCES pepys."Tasks" (task_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
