-- Table: public."Platforms"

-- DROP TABLE public."Platforms";

CREATE TABLE public."Platforms"
(
    --platform_id uuid NOT NULL DEFAULT gen_random_uuid(),
    platform_id      uuid                                                NOT NULL DEFAULT uuid_generate_v4(),
    name             character varying(150) COLLATE pg_catalog."default" NOT NULL,
    platformtype_id  uuid                                                NOT NULL,
    host_platform_id uuid,
    nationality_id   uuid                                                NOT NULL,
    CONSTRAINT "Platforms_pkey" PRIMARY KEY (platform_id),
    CONSTRAINT platforms_entry_fk FOREIGN KEY (platform_id)
        REFERENCES public."Entry" (entry_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT platforms_nationalities_fk FOREIGN KEY (nationality_id)
        REFERENCES public."Nationalities" (nationality_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT platforms_platforms_fk FOREIGN KEY (host_platform_id)
        REFERENCES public."Platforms" (platform_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT platforms_platformtypes_fk FOREIGN KEY (platformtype_id)
        REFERENCES public."PlatformTypes" (platformtype_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Platforms"
    OWNER to tracstor_admin;