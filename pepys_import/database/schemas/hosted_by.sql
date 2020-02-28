CREATE TABLE pepys."HostedBy"
(
    hosted_by_id UUID NOT NULL,
    subject_id   UUID NOT NULL,
    host_id      UUID NOT NULL,
    hosted_from  DATE NOT NULL,
    host_to      DATE NOT NULL,
    privacy_id   UUID NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (hosted_by_id),
    FOREIGN KEY (subject_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (host_id) REFERENCES pepys."Platforms" (platform_id),
    FOREIGN KEY (privacy_id) REFERENCES pepys."Privacies" (privacy_id)
)
