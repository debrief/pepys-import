-- Table: public."Users"

-- DROP TABLE public."Users";

CREATE TABLE public."Users"
(
    --user_id integer NOT NULL DEFAULT nextval('"Users_user_id_seq"'::regclass) ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    user_id   serial                                              NOT NULL,
    user_name character varying(150) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Users_pkey" PRIMARY KEY (user_id)
)
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

ALTER TABLE public."Users"
    OWNER to tracstor_admin;