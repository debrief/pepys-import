-- Table: public."Sensors"

-- DROP TABLE public."Sensors";

CREATE TABLE public."Sensors"
(
    --sensor_id uuid NOT NULL DEFAULT gen_random_uuid(),
    sensor_id     uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name          character varying(150) COLLATE pg_catalog."default" NOT NULL,
    sensortype_id uuid                                                NOT NULL,
    platform_id   uuid                                                NOT NULL,
    CONSTRAINT "Sensors_pkey" PRIMARY KEY (sensor_id),
    CONSTRAINT sensor_entry_fk FOREIGN KEY (sensor_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT sensor_platforms_fk FOREIGN KEY (platform_id)
        REFERENCES public."Platforms" (platform_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT sensor_sensortypes_fk FOREIGN KEY (sensortype_id)
        REFERENCES public."SensorTypes" (sensortype_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Sensors"
    OWNER to tracstor_admin;