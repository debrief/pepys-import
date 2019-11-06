-- Table: public."PlatformTypes"

-- DROP TABLE public."PlatformTypes";

CREATE TABLE public."PlatformTypes"
(
    --platformtype_id uuid NOT NULL DEFAULT gen_random_uuid(),
    platformtype_id uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name            character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "PlatformTypes_pkey" PRIMARY KEY (platformtype_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."PlatformTypes"
    OWNER to tracstor_admin;