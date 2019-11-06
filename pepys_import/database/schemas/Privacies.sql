-- Table: public."Privacies"

-- DROP TABLE public."Privacies";

CREATE TABLE public."Privacies"
(
    --privacy_id uuid NOT NULL DEFAULT gen_random_uuid(),
    privacy_id uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name       character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Privacies_pkey" PRIMARY KEY (privacy_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Privacies"
    OWNER to tracstor_admin;