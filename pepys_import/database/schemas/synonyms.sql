CREATE TABLE pepys."Synonyms"
(
    synonym_id   UUID         NOT NULL,
    "table"      VARCHAR(150) NOT NULL,
    entity       UUID         NOT NULL,
    synonym      VARCHAR(150) NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (synonym_id)
)
