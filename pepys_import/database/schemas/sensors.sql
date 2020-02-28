CREATE TABLE pepys."Sensors"
(
    sensor_id      UUID         NOT NULL,
    name           VARCHAR(150) NOT NULL,
    sensor_type_id UUID         NOT NULL,
    host           UUID         NOT NULL,
    created_date   TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (sensor_id),
    FOREIGN KEY (sensor_type_id) REFERENCES pepys."SensorTypes" (sensor_type_id),
    FOREIGN KEY (host) REFERENCES pepys."Platforms" (platform_id)
)
