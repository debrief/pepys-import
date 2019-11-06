-- Table: public."Nationalities"

-- DROP TABLE public."Nationalities";

CREATE TABLE public."Nationalities"
(
    --nationality_id uuid NOT NULL DEFAULT gen_random_uuid(),
    nationality_id uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name           character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Nationalities_pkey" PRIMARY KEY (nationality_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Nationalities"
    OWNER to tracstor_admin;