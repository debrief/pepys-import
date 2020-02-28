CREATE TABLE pepys."TaggedItems"
(
    tagged_item_id UUID    NOT NULL,
    tag_id         UUID    NOT NULL,
    item_id        UUID    NOT NULL,
    tagged_by_id   UUID    NOT NULL,
    private        BOOLEAN NOT NULL,
    tagged_on      DATE    NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (tagged_item_id),
    FOREIGN KEY (tag_id) REFERENCES pepys."Tags" (tag_id),
    FOREIGN KEY (tagged_by_id) REFERENCES pepys."Users" (user_id)
)

