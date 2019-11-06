-- Table: public."DatafileTypes"

-- DROP TABLE public."DatafileTypes";

CREATE TABLE public."DatafileTypes"
(
    --datafiletype_id uuid NOT NULL DEFAULT gen_random_uuid(),
    datafiletype_id uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name            character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "DatafileTypes_pkey" PRIMARY KEY (datafiletype_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."DatafileTypes"
    OWNER to tracstor_admin;