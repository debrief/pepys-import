CREATE TABLE pepys."CommentTypes"
(
    comment_type_id UUID         NOT NULL,
    name            VARCHAR(150) NOT NULL,
    created_date    TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (comment_type_id)
)
