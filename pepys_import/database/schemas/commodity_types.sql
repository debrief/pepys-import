CREATE TABLE pepys."CommodityTypes"
(
    commodity_type_id UUID         NOT NULL,
    name              VARCHAR(150) NOT NULL,
    created_date      TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (commodity_type_id)
)
