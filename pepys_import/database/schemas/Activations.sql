-- Table: public."Activations"

-- DROP TABLE public."Activations";

CREATE TABLE public."Activations"
(
    --sensor_id uuid NOT NULL DEFAULT gen_random_uuid(),
    sensor_id     uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    "end"         timestamp without time zone                         NOT NULL,
    min_range     double precision,
    max_range     double precision,
    left_arc      double precision,
    right_arc     double precision,
    datafile_id   uuid                                                NOT NULL,
    privacy_id    uuid,
    name          character varying(150) COLLATE pg_catalog."default" NOT NULL,
    activation_id uuid                                                NOT NULL,
    start         timestamp without time zone                         NOT NULL,
    CONSTRAINT "Activations_pkey" PRIMARY KEY (activation_id),
    CONSTRAINT activations_datafiles_fk FOREIGN KEY (datafile_id)
        REFERENCES public."Datafiles" (datafile_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT activations_entry_fk FOREIGN KEY (activation_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT activations_privacies_fk FOREIGN KEY (privacy_id)
        REFERENCES public."Privacies" (privacy_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT activations_sensors_fk FOREIGN KEY (sensor_id)
        REFERENCES public."Sensors" (sensor_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Activations"
    OWNER to tracstor_admin;