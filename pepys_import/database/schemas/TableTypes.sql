-- Table: public."TableTypes"

-- DROP TABLE public."TableTypes";

CREATE TABLE public."TableTypes"
(
    tabletype_id integer                                             NOT NULL,
    name         character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "TableTypes_pkey" PRIMARY KEY (tabletype_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."TableTypes"
    OWNER to tracstor_admin;