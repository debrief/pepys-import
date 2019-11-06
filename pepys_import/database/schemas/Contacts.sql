-- Table: public."Contacts"

-- DROP TABLE public."Contacts";

CREATE TABLE public."Contacts"
(
    --contact_id uuid NOT NULL DEFAULT gen_random_uuid(),
    contact_id  uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name        character varying(150) COLLATE pg_catalog."default" NOT NULL,
    sensor_id   uuid                                                NOT NULL,
    "time"      timestamp without time zone                         NOT NULL,
    bearing     double precision,
    freq        double precision,
    location    point,
    major       double precision,
    minor       double precision,
    orientation double precision,
    datafile_id uuid                                                NOT NULL,
    privacy_id  uuid,
    CONSTRAINT "Contacts_pkey" PRIMARY KEY (contact_id),
    CONSTRAINT contacts_datafiles_fk FOREIGN KEY (datafile_id)
        REFERENCES public."Datafiles" (datafile_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT contacts_entry_fk FOREIGN KEY (contact_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT contacts_privacies_fk FOREIGN KEY (privacy_id)
        REFERENCES public."Privacies" (privacy_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT contacts_sensors_fk FOREIGN KEY (sensor_id)
        REFERENCES public."Sensors" (sensor_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Contacts"
    OWNER to tracstor_admin;