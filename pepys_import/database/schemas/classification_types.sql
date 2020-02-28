CREATE TABLE pepys."ClassificationTypes"
(
    class_type_id UUID         NOT NULL,
    class_type    VARCHAR(150) NOT NULL,
    created_date  TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (class_type_id)
)
