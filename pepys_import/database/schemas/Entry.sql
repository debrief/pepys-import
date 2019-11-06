-- Table: public."Entry"

-- DROP TABLE public."Entry";

CREATE TABLE public."Entry"
(
    --entry_id uuid NOT NULL DEFAULT gen_random_uuid(),
    entry_id uuid NOT NULL DEFAULT uuid_generate_v4(),
    tabletype_id integer NOT NULL,
    created_user integer,
    CONSTRAINT "Entry_pkey" PRIMARY KEY (entry_id),
    CONSTRAINT entry_tabletypes_fk FOREIGN KEY (tabletype_id)
        REFERENCES public."TableTypes" (tabletype_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT entry_users_fk FOREIGN KEY (created_user)
        REFERENCES public."Users" (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public."Entry"
    OWNER to tracstor_admin;