-- Table: public."Datafiles"

-- DROP TABLE public."Datafiles";

CREATE TABLE public."Datafiles"
(
    --datafile_id uuid NOT NULL DEFAULT gen_random_uuid(),
    datafile_id     uuid NOT NULL DEFAULT uuid_generate_v4(),
    simulated       boolean,
    reference       character varying(150) COLLATE pg_catalog."default",
    url             character varying(500) COLLATE pg_catalog."default",
    privacy_id      uuid NOT NULL,
    datafiletype_id uuid NOT NULL,
    CONSTRAINT "Datafiles_pkey" PRIMARY KEY (datafile_id),
    CONSTRAINT datafiles_datafiletypes_fk FOREIGN KEY (datafiletype_id)
        REFERENCES public."DatafileTypes" (datafiletype_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT datafiles_entry_fk FOREIGN KEY (datafile_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT datafiles_privacies_fk FOREIGN KEY (privacy_id)
        REFERENCES public."Privacies" (privacy_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Datafiles"
    OWNER to tracstor_admin;