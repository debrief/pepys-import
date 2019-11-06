-- Table: public."State"

-- DROP TABLE public."State";

CREATE TABLE public."State"
(
    --state_id uuid NOT NULL DEFAULT gen_random_uuid(),
    state_id    uuid                        NOT NULL DEFAULT uuid_generate_v4(),
    "time"      timestamp without time zone NOT NULL,
    sensor_id   uuid                        NOT NULL,
    location    point,
    heading     double precision,
    course      double precision,
    speed       double precision,
    datafile_id uuid                        NOT NULL,
    privacy_id  uuid,
    CONSTRAINT "State_pkey" PRIMARY KEY (state_id),
    CONSTRAINT state_datafiles_fk FOREIGN KEY (datafile_id)
        REFERENCES public."Datafiles" (datafile_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT state_entry_fk FOREIGN KEY (state_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT state_privacies_fk FOREIGN KEY (privacy_id)
        REFERENCES public."Privacies" (privacy_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT state_sensors_fk FOREIGN KEY (sensor_id)
        REFERENCES public."Sensors" (sensor_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."State"
    OWNER to tracstor_admin;