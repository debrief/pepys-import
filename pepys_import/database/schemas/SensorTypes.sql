-- Table: public."SensorTypes"

-- DROP TABLE public."SensorTypes";

CREATE TABLE public."SensorTypes"
(
    --sensortype_id uuid NOT NULL DEFAULT gen_random_uuid(),
    sensortype_id uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name          character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "SensorTypes_pkey" PRIMARY KEY (sensortype_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."SensorTypes"
    OWNER to tracstor_admin;